# Copyright 2024 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

import argparse
import os

import datasets
import faiss
import numpy as np
from loguru import logger
from tqdm import tqdm

from mx_rag.embedding.local import TextEmbedding
from mx_rag.reranker.local import LocalReranker


def retrieve_and_evaluate(dataset_path: str, embedding_path: str, reranker_path: str):
    logger.info("检索评估embedding+reranker模型准确率")

    corpus_data_path = os.path.join(dataset_path, "corpus_data.jsonl")
    eval_data_path = os.path.join(dataset_path, "eval_data.jsonl")

    corpus_data = datasets.load_dataset("json", data_files=corpus_data_path, split="train")
    eval_data = datasets.load_dataset("json", data_files=eval_data_path, split="train")

    embed_model = TextEmbedding(embedding_path)
    rerank_model = LocalReranker(reranker_path)

    faiss_index = _build_index(embed_model, corpus_data)
    _, indices = _search(model=embed_model, queries=eval_data, faiss_index=faiss_index)
    retrieval_results = []
    for indice in indices:
        indice = indice[indice != -1].tolist()
        retrieval_results.append(corpus_data[indice]["content"])

    reranker_retrieval_results = []
    queries = eval_data["query"]
    for idx, retrieval_result in enumerate(tqdm(retrieval_results, desc="reranker sort")):
        query = queries[idx]
        scores = rerank_model.rerank(query, retrieval_result).tolist()

        retrival_result_scores = list(zip(retrieval_result, scores))
        sorted_retrieval_result_scores = sorted(retrival_result_scores, key=lambda x: x[1], reverse=True)
        sorted_retrieval_result = [item[0] for item in sorted_retrieval_result_scores]
        reranker_retrieval_results.append(sorted_retrieval_result)

    ground_truths = []
    for sample in eval_data:
        ground_truths.append(sample["pos"])

    return _evaluate_recall5(eval_data["query"], reranker_retrieval_results, ground_truths)


def _build_index(model: TextEmbedding,
                 corpus: datasets.Dataset,
                 batch_size: int = 256,
                 max_length: int = 512,
                 index_factory: str = "Flat"):
    corpus_embeddings = model.embed_texts(corpus["content"], batch_size=batch_size, max_length=max_length)
    dim = corpus_embeddings.shape[-1]

    faiss_index = faiss.index_factory(dim, index_factory, faiss.METRIC_INNER_PRODUCT)
    corpus_embeddings = corpus_embeddings.astype(np.float32)
    faiss_index.train(corpus_embeddings)
    faiss_index.add(corpus_embeddings)
    return faiss_index


def _search(model: TextEmbedding, queries: datasets, faiss_index: faiss.Index, k: int = 100, batch_size: int = 256):
    query_embeddings = model.embed_texts(queries["query"], batch_size=batch_size)
    query_size = len(query_embeddings)

    all_scores = []
    all_indices = []

    for i in tqdm(range(0, query_size, batch_size), desc="searching"):
        j = min(i + batch_size, query_size)
        query_embedding = query_embeddings[i:j]
        score, indice = faiss_index.search(query_embedding, k=k)
        all_scores.append(score)
        all_indices.append(indice)

    all_scores = np.concatenate(all_scores, axis=0)
    all_indices = np.concatenate(all_indices, axis=0)

    return all_scores, all_indices


def _evaluate_recall5(queries, preds, labels):
    metrics = {}

    recalls = 0
    count = 0
    no_recall_list = []
    for pred, label in tqdm(list(zip(preds, labels)), desc="calculate recall"):
        recall = np.intersect1d(label, pred[:5])
        if len(recall) != len(label):
            item = {"query": queries[count], "pos": label}
            if item not in no_recall_list:
                no_recall_list.append(item)
        recalls += len(recall) / len(label)
        count += 1
    recalls /= len(preds)
    metrics["Recall@5"] = recalls

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval_data", type=str)
    parser.add_argument("--embedding_path", type=str)
    parser.add_argument("--reranker_path", type=str)
    args = parser.parse_args()

    result = retrieve_and_evaluate(args.eval_data, args.embedding_path, args.reranker_path)
    logger.info(f"eval result is {result}")
