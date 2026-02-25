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

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


class RetrieverConfig:
    """Configuration class for retrieval services.

    This class encapsulates all parameters needed for model loading and 
    index management. Replace placeholder paths with actual paths in production.

    Attributes:
        retrieval_method (str): Name of retrieval algorithm (e.g. "e5").
        retrieval_topk (int): Number of top results to return, defaults to 10.
        index_path (str): Path to FAISS index file, defaults to example path.
        corpus_path (str): Path to corpus file, defaults to example path.
        retrieval_model_path (str): Path to retrieval model, defaults to example.
        retrieval_pooling_method (str): Pooling method (e.g. "mean"), defaults to mean.
        retrieval_query_max_length (int): Max query length, defaults to 256.
        retrieval_use_fp16 (bool): Whether to use FP16 precision, defaults to False.
        retrieval_batch_size (int): Batch size for processing, defaults to 128.
    """
    def __init__(
        self, 
        index_path: str,
        corpus_path: str,
        retrieval_model_path: str,
        retrieval_method: str = "e5", 
        retrieval_topk: int = 10,
        retrieval_pooling_method: str = "mean",
        retrieval_query_max_length: int = 256,
        retrieval_use_fp16: bool = False,
        retrieval_batch_size: int = 128
    ):
        if not isinstance(retrieval_use_fp16, bool):
            raise TypeError("retrieval_use_fp16 must be a boolean")

        if not isinstance(retrieval_topk, int) or not 1 <= retrieval_topk <= 1024:
            raise TypeError("retrieval_topk must be an integer between 1 and 1024")

        if not isinstance(retrieval_query_max_length, int) or not 1 <= retrieval_query_max_length <= 4096:
            raise TypeError("retrieval_query_max_length must be an integer between 1 and 4096")

        if not isinstance(retrieval_batch_size, int) or not 1 <= retrieval_batch_size <= 1024:
            raise TypeError("retrieval_batch_size must be an integer between 1 and 1024")

        if retrieval_method not in ["e5"]:
            raise ValueError(f"Invalid retrieval_method: {retrieval_method}. Must be one of ['e5']")

        valid_poolings = {"mean", "cls", "pooler"}
        if retrieval_pooling_method not in valid_poolings:
            raise ValueError(f"Invalid pooling method: {retrieval_pooling_method}. Must be one of {valid_poolings}")

        for name, path in (
            ("retrieval_model_path", retrieval_model_path),
            ("index_path", index_path),
            ("corpus_path", corpus_path),
        ):
            p = Path(path)
            if not p.exists():
                raise ValueError(f"{name} does not exist: {path}")
            
        self.retrieval_method = retrieval_method
        self.retrieval_topk = retrieval_topk
        self.index_path = index_path
        self.corpus_path = corpus_path
        self.retrieval_model_path = retrieval_model_path
        self.retrieval_pooling_method = retrieval_pooling_method
        self.retrieval_query_max_length = retrieval_query_max_length
        self.retrieval_use_fp16 = retrieval_use_fp16
        self.retrieval_batch_size = retrieval_batch_size

class QueryRequest(BaseModel):
    queries: List[str]
    topk: Optional[int] = None
    return_scores: bool = False