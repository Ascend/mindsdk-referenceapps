# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from typing import List, Union, Dict
from paddle.base import libpaddle
from pydantic import BaseModel
from fastapi import FastAPI
import numpy as np
from mx_rag.summary import ClusterSummary
from doc_qa_compressor import DocQaCompressor
from log_analyse_compressor import LogAnalyseCompressor
from mx_rag.storage.vectorstore import MindFAISS
from mx_rag.embedding.local.text_embedding import TextEmbedding
from mx_rag.storage.vectorstore.vectorstore import SimilarityStrategy


class DocQaUnstructuredItem(BaseModel):
    context: str
    question: str
    target_tokens: int
    target_rate: float


class DocQaStructuredItem(BaseModel):
    context: List
    question: str
    topk: int


class LogAnalyseItem(BaseModel):
    context: str
    question: str


class SummaryItem(BaseModel):
    context: str
    question: str
    compress_rate: float
    embedding_batch_size: int
    min_cluster_size: int


DOC_QA_MODEL_PATH = '/home/models/bge-reranker-v2-m3'
DOC_SUMMARY_MODEL_PATH = '/home/models/bge-small-zh-v1.5'
DOC_SUMMARY_DEVICE = 'npu:0'
DEVICE_ID = 0
X_DIM = 1024
FAISS_LOCAL_INDEX = './faiss.index'
FAISS_EMBEDDING_MODEL = '/home/models/bge-large-en-v1.5'
LOG_ANALYSE_LABEL_PATH = './data/log/history_label.jsonl'
LABEL_RECALL_TOP_K = 5

doc_qa = DocQaCompressor(DOC_QA_MODEL_PATH, DEVICE_ID)
log_analyse = LogAnalyseCompressor()
doc_summary = ClusterSummary(DOC_SUMMARY_MODEL_PATH, DOC_SUMMARY_DEVICE)

faiss = MindFAISS(x_dim=X_DIM,
                  similarity_strategy=SimilarityStrategy.FLAT_L2,
                  devs=[DEVICE_ID],
                  load_local_index=FAISS_LOCAL_INDEX,
                  auto_save=False)
embed = TextEmbedding(FAISS_EMBEDDING_MODEL, dev_id=DEVICE_ID)
label_list = []
with open(LOG_ANALYSE_LABEL_PATH, 'r') as f:
    for line in f:
        label_list.append(line)
faiss.add(np.array(embed.embed_documents(label_list)), [i for i in range(len(label_list))])


def query_data_by_chunk(local_faiss, local_embed, reserved_list, local_label_list, topk: int = 5):
    if not isinstance(reserved_list, List):
        raise ValueError('The reserved_list must be of type List')

    topk = min(topk, len(local_label_list))
    q_len = len(reserved_list)
    epsilon = 1e-10

    ret = local_faiss.search(np.array(local_embed.embed_documents(reserved_list)), k=topk)
    distances_list = ret[0]
    id_list = ret[1]

    distances = [
        distances_list[j][i]
        for j in range(q_len)
        for i in range(topk)
    ]
    sorted_distances = sorted(distances)[:q_len]
    result_list = []
    tem_set = set()
    for distance in sorted_distances:
        for j in range(q_len):
            for i in range(topk):
                if abs(distances_list[j][i] - distance) < epsilon:
                    doc_id = int(id_list[j][i])
                    if doc_id not in tem_set:
                        tem_set.add(doc_id)
                        text = local_label_list[doc_id]
                        result_list.append((doc_id, text))
                    break
    return result_list[:topk] if len(result_list) > topk else result_list


app = FastAPI()


@app.post("/doc_qa_unstructured_compressor/")
async def create_doc_qa_unstructured_item(item: DocQaUnstructuredItem):
    context = item.context
    question = item.question
    target_tokens = item.target_tokens
    target_rate = item.target_rate

    return doc_qa.run_doc_qa(context, question, target_tokens, target_rate)


@app.post("/doc_qa_structured_compressor/")
async def create_doc_qa_structured_item(item: DocQaStructuredItem):
    context = item.context
    question = item.question
    topk = item.topk

    return doc_qa.run_structured_doc_qa(context, question, topk)


@app.post("/log_analyse_compressor/")
async def create_log_analyse_item(item: LogAnalyseItem):
    context = item.context
    question = item.question

    compressed_context, reserved_list = log_analyse.run_log_analysis(context, question)
    result_list = query_data_by_chunk(faiss, embed, reserved_list, label_list, LABEL_RECALL_TOP_K)
    history_label = '\n'.join([data for _, data in result_list])

    return compressed_context, history_label


@app.post("/doc_summary_compressor/")
async def create_doc_summary_item(item: SummaryItem):
    context = item.context
    question = item.question
    compress_rate = item.compress_rate
    embedding_batch_size = item.embedding_batch_size
    min_cluster_size = item.min_cluster_size

    return doc_summary.summary(context, question, compress_rate, embedding_batch_size, min_cluster_size)
