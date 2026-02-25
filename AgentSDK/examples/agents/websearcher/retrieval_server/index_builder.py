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

import os
import torch
import faiss
import warnings
import argparse
import numpy as np
from tqdm import tqdm
from typing import cast
from pathlib import Path

from utils.function import load_corpus, load_model, pooling


class IndexBuilder:
    def __init__(
            self, 
            retrieval_method: str,
            model_path: str,
            corpus_path: str,
            save_dir: str,
            max_length: int,
            batch_size: int,
            use_fp16: bool = False,
            pooling_method: str = "mean",
            faiss_type: str = None,
            embedding_path: str = None,
            save_embedding: bool = False
    ):
        if retrieval_method not in ["e5"]:
            raise ValueError(f"retrieval_method {retrieval_method} is not supported")
        
        if not isinstance(max_length, int) or max_length <= 0:
            raise ValueError(f"max_length {max_length} must be a positive integer")
        
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError(f"batch_size {batch_size} must be a positive integer")
        
        if not isinstance(use_fp16, bool):
            raise ValueError(f"use_fp16 {use_fp16} must be a boolean")
        
        if pooling_method not in ["mean", "cls", "pooler"]:
            raise ValueError(f"Invalid pooling_method: {pooling_method}. Supported methods are ['mean', 'cls', 'pooler'].")
        
        if faiss_type is not None and not isinstance(faiss_type, str):
            raise ValueError(f"faiss_type {faiss_type} must be a string")
        
        if embedding_path is not None and not isinstance(embedding_path, str):
            raise ValueError(f"embedding_path {embedding_path} must be a string")
        
        if not isinstance(save_embedding, bool):
            raise ValueError(f"save_embedding {save_embedding} must be a boolean")
        
        if not isinstance(save_dir, str):
            raise ValueError(f"save_dir {save_dir} must be a string")
        
        if not isinstance(model_path, str):
            raise ValueError(f"model_path {model_path} must be a string")
        
        if not isinstance(corpus_path, str):
            raise ValueError(f"corpus_path {corpus_path} must be a string")
        
        for name, path in (
            ("corpus_path", corpus_path),
        ):
            p = Path(path)
            if not p.exists():
                raise ValueError(f"{name} does not exist: {path}")

        self.retrieval_method = retrieval_method.lower()
        self.model_path = model_path
        self.corpus_path = corpus_path
        self.save_dir = save_dir
        self.max_length = max_length
        self.batch_size = batch_size
        self.use_fp16 = use_fp16
        self.pooling_method = pooling_method
        self.faiss_type = faiss_type if faiss_type is not None else "Flat"
        self.embedding_path = embedding_path
        self.save_embedding = save_embedding

        self.gpu_num = torch.npu.device_count()
        self.index_save_path = os.path.join(self.save_dir, f"{self.retrieval_method}_{self.faiss_type}.index")
        self.embedding_save_path = os.path.join(self.save_dir, f"emb_{self.retrieval_method}.memmap")
        self.corpus = load_corpus(self.corpus_path)

        self.encoder, self.tokenizer = load_model(model_path=self.model_path,
                                                  use_fp16=self.use_fp16)
        
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        else:
            if len(os.listdir(self.save_dir)) > 0:
                warnings.warn("some files already exist in save_dir and will be overwritten.", UserWarning)

        print("Index Builder Initialized Successfully")

    @staticmethod
    def _load_embedding(embedding_path: str, corpus_size: int, hidden_size: int):
        """Load embeddings from a memory-mapped file.

        Args:
            embedding_path (str): Path to the memory-mapped file.
            corpus_size (int): Number of embeddings in the file.
            hidden_size (int): Dimensionality of each embedding.

        Returns:
            np.ndarray: Array of embeddings with shape (corpus_size, hidden_size).
        """
        all_embeddings = np.memmap(
            embedding_path,
            mode="r",
            dtype=np.float32,
        ).reshape(corpus_size, hidden_size)

        return all_embeddings
    
    @torch.no_grad()
    def build_dense_index(self):
        if os.path.exists(self.index_save_path):
            print(f"Index file {self.index_save_path} already exists, skip building index.")
            return
        
        if self.embedding_path is not None:
            hidden_size = self.encoder.config.hidden_size
            corpus_size = len(self.corpus)
            all_embeddings = IndexBuilder._load_embedding(self.embedding_path, corpus_size, hidden_size)
        else:
            all_embeddings = self._encode_all()
            if self.save_embedding:
                self._save_embedding(all_embeddings)
            del self.corpus

        print(f"Build index file {self.index_save_path}")
        dim = all_embeddings.shape[-1]
        faiss_index = faiss.index_factory(dim, self.faiss_type, faiss.METRIC_INNER_PRODUCT)
        if not faiss_index.is_trained:
            faiss_index.train(all_embeddings)
        faiss_index.add(all_embeddings)
        
        faiss.write_index(faiss_index, self.index_save_path)
        print(f"Index file {self.index_save_path} built successfully.")
    
    def _save_embedding(self, embeddings: np.ndarray):
        """Save embeddings to a memory-mapped file.

        Args:
            embeddings (np.ndarray): Array of embeddings to save.
        """
        memmap = np.memmap(
            self.embedding_save_path,
            shape=embeddings.shape,
            mode="w+",
            dtype=embeddings.dtype,
        )
        length = embeddings.shape[0]
        save_batch_size = 10000
        if length > save_batch_size:
            for i in tqdm(range(0, length, save_batch_size), leave=False, desc="Saving embeddings"):
                j = min(i + save_batch_size, length)
                memmap[i:j] = embeddings[i:j]
        else:
            memmap[:] = embeddings

    def _encode_all(self):
        if self.gpu_num > 1:
            print(f"Use multi npu: {self.gpu_num}")
            self.encoder = torch.nn.DataParallel(self.encoder)
            self.batch_size = self.batch_size * self.gpu_num

        all_embeddings = []

        for start_idx in tqdm(range(0, len(self.corpus), self.batch_size), desc="Inference Embeddings:"):
            batch_data = self.corpus[start_idx:start_idx + self.batch_size]['contents']

            if self.retrieval_method == "e5":
                batch_data = [f"passage: {doc}" for doc in batch_data]
            
            inputs = self.tokenizer(
                batch_data,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=self.max_length,
            ).to('npu')

            inputs = {k: v.npu() for k, v in inputs.items()}

            if "T5" in type(self.encoder).__name__:
                decoder_input_ids = torch.zeros(
                    (inputs['input_ids'].shape[0], 1), dtype=torch.long
                ).to(inputs['input_ids'].device)
                output = self.encoder(
                    **inputs,
                    decoder_input_ids=decoder_input_ids,
                    return_dict=True
                )
                embeddings = output.last_hidden_state[:, 0, :]

            else:
                output = self.encoder(**inputs, return_dict=True)
                embeddings = pooling(output.pooler_output,
                                     output.last_hidden_state,
                                     inputs['attention_mask'],
                                     self.pooling_method)
                if "dpr" not in self.retrieval_method:
                    embeddings = torch.nn.functional.normalize(embeddings, dim=-1)
                
            embeddings = cast(torch.Tensor, embeddings)
            embeddings = embeddings.detach().cpu().numpy()
            all_embeddings.append(embeddings)
        
        all_embeddings = np.concatenate(all_embeddings, axis=0)
        all_embeddings = all_embeddings.astype(np.float32)

        return all_embeddings
    

MODEL2POOLING = {
    "e5": "mean",
    "bge": "cls",
    "contriever": "mean",
    "jina": "mean",
}

def main():
    STORE_TRUE = 'store_true'
    parser = argparse.ArgumentParser(description="Build dense index for retrieval server.")
    parser.add_argument("--retrieval_method", type=str, required=True, help="Retrieval method.")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model.")
    parser.add_argument("--corpus_path", type=str, required=True, help="Path to the corpus.")
    parser.add_argument("--save_dir", type=str, default="indexed/", help="Path to save the embeddings.")

    parser.add_argument("--max_length", type=int, default=180, help="Maxinum sequence length.")
    parser.add_argument("--batch_size", type=int, default=2048, help="Batch size for processing.")
    parser.add_argument("--use_fp16", action=STORE_TRUE, default=False, help="Use FP16 for model.")
    parser.add_argument("--pooling_method", type=str, default=None, help="Pooling method.")
    parser.add_argument("--faiss_type", type=str, default=None, help="FAISS index type.")
    parser.add_argument("--embedding_path", type=str, default=None, help="Path to the pre-computed embeddings.")
    parser.add_argument("--save_embedding", action=STORE_TRUE, default=False, help="Whether to save the embeddings.")
    
    args = parser.parse_args()

    if args.pooling_method is None:
        pooling_method = 'mean'
        for k, v in MODEL2POOLING.items():
            if k in args.retrieval_method.lower():
                pooling_method = v
                break
    
    else:
        if args.pooling_method not in ['mean', 'cls', 'pooler']:
            raise ValueError("Invalid pooling method.")
        pooling_method = args.pooling_method

    index_builder = IndexBuilder(
        retrieval_method=args.retrieval_method,
        model_path=args.model_path,
        corpus_path=args.corpus_path,
        save_dir=args.save_dir,
        max_length=args.max_length,
        batch_size=args.batch_size,
        use_fp16=args.use_fp16,
        pooling_method=pooling_method,
        faiss_type=args.faiss_type,
        embedding_path=args.embedding_path,
        save_embedding=args.save_embedding,
    )
    index_builder.build_dense_index()


if __name__ == "__main__":
    main()