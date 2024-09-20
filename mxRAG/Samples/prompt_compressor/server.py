# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from typing import List, Union, Dict
from pydantic import BaseModel
from fastapi import FastAPI
from mx_rag.summary import ClusterSummary
from doc_qa_compressor import DocQaCompressor
from log_analyse_compressor import LogAnalyseCompressor


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

    return log_analyse.run_log_analysis(context, question)


@app.post("doc_summary_compressor/")
async def create_doc_summary_item(item: SummaryItem):
    context = item.context
    question = item.question
    compress_rate = item.compress_rate
    embedding_batch_size = item.embedding_batch_size
    min_cluster_size = item.min_cluster_size

    return doc_summary.summary(context, question, compress_rate, embedding_batch_size, min_cluster_size)