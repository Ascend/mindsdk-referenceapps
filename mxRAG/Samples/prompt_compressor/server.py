# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from typing import List, Union, Dict
from pydantic import BaseModel
from fastapi import FastAPI
from mx_rag.summary import ClusterSummary
from doc_qa_compressor import DocQaCompressor
from log_analyse_compressor import LogAnalyseCompressor
from mx_rag.storage.vectorstore import MindFAISS
from mx_rag.embedding.local.text_embedding import TextEmbedding


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
DOC_QA_DEVICE_ID = 1

DOC_SUMMARY_MODEL_PATH = '/home/models/bge-small-zh-v1.5'
DOC_SUMMARY_DEVICE = 'npu:1'

doc_qa = DocQaCompressor(DOC_QA_MODEL_PATH, DOC_QA_DEVICE_ID)
log_analyse = LogAnalyseCompressor()
doc_summary = ClusterSummary(DOC_SUMMARY_MODEL_PATH, DOC_SUMMARY_DEVICE)

faiss = MindFAISS(x_dim=1024,
                  index_type="FLAT:L2",
                  devs=[1],
                  load_local_index='./faiss.index',
                  auto_save=False
                  )
embed = TextEmbedding('/home/models/bge-large-en-v1.5', dev_id=1)

labels_path = './data/log/history_label.jsonl'
label_list = []
with open(labels_path, 'r') as f:
    for line in f:
        label_list.append(line)
faiss.add(embed.embed_texts(label_list), [i for i in range(len(label_list))])

def query_data_by_chunk(faiss, embed, reserved_list, label_list, topk: int = 5):
    if not isinstance(reserved_list, List):
        raise ValueError('The reserved_list must be of type List')

    topk = min(topk, len(label_list))
    q_len = len(reserved_list)

    ret = faiss.search(embed.embed_texts(reserved_list), k=topk)
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
                if distances_list[j][i] == distance:
                    doc_id = int(id_list[j][i])
                    if doc_id not in tem_set:
                        tem_set.add(doc_id)
                        text = label_list[doc_id]
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
    result_list = query_data_by_chunk(faiss, embed, reserved_list, label_list, 5)
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
