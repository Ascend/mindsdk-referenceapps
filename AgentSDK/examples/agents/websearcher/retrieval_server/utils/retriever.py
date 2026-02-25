"""
Copyright 2026 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
import faiss
import torch
import numpy as np

from typing import List
from tqdm import tqdm

from examples.agents.websearcher.retrieval_server.utils.function import load_corpus, load_docs, load_model, pooling

class Encoder:
    """Text encoder for converting natural language to vector representations.
    
    Supports multiple model architectures with consistent output format.
    """
    def __init__(self, model_name, model_path, pooling_method, max_length, use_fp16):
        """Initialize the text encoder."""
        self.model_name = model_name
        self.model_path = model_path
        self.pooling_method = pooling_method
        self.max_length = max_length
        self.use_fp16 = use_fp16

        self.model, self.tokenizer = load_model(model_path=model_path, use_fp16=use_fp16)
        self.model.eval()

    @torch.no_grad()
    def encode(self, query_list: List[str]):
        """Encode text queries into fixed-dimension vectors.
        
        Args:
            query_list: List of text queries to encode
            
        Returns:
            np.ndarray: [batch_size, embedding_dim] array of float32 vectors
        """
        # processing query for different encoders
        if not isinstance(query_list, list):
            raise ValueError("Query must be a list")

        if "e5" in self.model_name.lower():
            query_list = [f"query: {query}" for query in query_list]
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")

        inputs = self.tokenizer(query_list,
                                max_length=self.max_length,
                                padding=True,
                                truncation=True,
                                return_tensors="pt"
                                )
        inputs = {k: v.npu() for k, v in inputs.items()}

        if "T5" in type(self.model).__name__:
            # T5-based retrieval model
            decoder_input_ids = torch.zeros(
                (inputs['input_ids'].shape[0], 1), dtype=torch.long
            ).to(inputs['input_ids'].device)
            output = self.model(
                **inputs, decoder_input_ids=decoder_input_ids, return_dict=True
            )
            query_emb = output.last_hidden_state[:, 0, :]
        else:
            output = self.model(**inputs, return_dict=True)
            query_emb = pooling(output.pooler_output,
                                output.last_hidden_state,
                                inputs['attention_mask'],
                                self.pooling_method)
            if "dpr" not in self.model_name.lower():
                query_emb = torch.nn.functional.normalize(query_emb, dim=-1)

        query_emb = query_emb.detach().cpu().numpy()
        query_emb = query_emb.astype(np.float32, order="C")
        
        del inputs, output
        torch.npu.empty_cache()

        return query_emb


class BaseRetriever:
    """Abstract base class for document retrievers.
    
    Provides common interface for vector and keyword-based retrieval systems.
    
    Attributes:
        config: Original configuration parameters
        retrieval_method: Name of retrieval algorithm
        topk: Default number of results to return
        index_path: Path to stored index
        corpus_path: Path to document corpus
    """
    def __init__(self, config_param):
        """Initialize base retriever with common parameters."""
        self.config = config_param
        self.retrieval_method = config_param.retrieval_method
        self.topk = config_param.retrieval_topk
        
        self.index_path = config_param.index_path
        self.corpus_path = config_param.corpus_path
    
    def batch_search(self, query_list: List[str], num: int = None):
        """Public interface for batch query search."""
        return self._batch_search(query_list, num)

    def _batch_search(self, query_list: List[str], num: int):
        """Abstract method for batch query search."""
        raise NotImplementedError

class DenseRetriever(BaseRetriever):
    """A dense vector retrieval system based on FAISS and transformer encoders."""
    
    def __init__(self, config_param, retriever_port):
        """Initialize the dense retriever."""
        super().__init__(config_param)
        
        try:
            print(f'begin load faiss index from {self.index_path}')
            time_start = time.time()
            self.index = faiss.read_index(self.index_path)
            time_end = time.time()
            print(f"load faiss index time : {time_end-time_start:.3f}")
        except faiss.FaissException as e:
            raise RuntimeError(f"Failed to load index from {self.index_path}") from e
        
        if config_param.faiss_gpu:
            co = faiss.GpuMultipleClonerOptions()
            co.useFloat16 = True
            co.shard = True
            self.index = faiss.index_cpu_to_all_gpus(self.index, co=co)

        self.corpus = load_corpus(self.corpus_path)
        self.encoder = Encoder(
            model_name = self.retrieval_method,
            model_path = config_param.retrieval_model_path,
            pooling_method = config_param.retrieval_pooling_method,
            max_length = config_param.retrieval_query_max_length,
            use_fp16 = config_param.retrieval_use_fp16
        )
        self.topk = config_param.retrieval_topk
        self.batch_size = config_param.retrieval_batch_size
        self.port = retriever_port

    def _batch_search(self, query_list: List[str], num: int = None):
        """Perform batch query search with progress tracking.
        
        Args:
            query_list: List of query strings
            num: Number of results per query (defaults to self.topk)
            
        Returns:
            tuple: (list of results, list of scores or None)
        """
        if num is not None:
            if not isinstance(num, int):
                raise ValueError("num must be an integer or None")
            if num <= 0:
                raise ValueError("num must be positive")

        num = num or self.topk
        
        results = []
        scores = []
        pbar = tqdm(
            range(0, len(query_list), self.batch_size),
            desc=f'PORT {self.port} Retrieval process: ',
            unit='queries'
        )
        for start_idx in pbar:
            query_batch = query_list[start_idx:start_idx + self.batch_size]
            batch_emb = self.encoder.encode(query_batch)
            batch_scores, batch_idxs = self.index.search(batch_emb, k=num)
            batch_scores = batch_scores.tolist()
            batch_idxs = batch_idxs.tolist()

            # load_docs is not vectorized, but is a python list approach
            flat_idxs = sum(batch_idxs, [])
            batch_results = load_docs(self.corpus, flat_idxs)
            # chunk them back
            batch_results = [batch_results[i*num : (i+1)*num] for i in range(len(batch_idxs))]
            
            results.extend(batch_results)
            scores.extend(batch_scores)
            
        return results, scores