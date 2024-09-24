# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from typing import List
from mx_rag.document.splitter import DocSplitter, StructuredDocSplitter
from mx_rag.reranker.local import LocalReranker
from mx_rag.retrievers import DocRetriever, StructuredDocRetriever, DocRetrieverPara


class DocQaCompressor(object):
    def __init__(self, model_path: str, device_id: int):
        self.pre_processor = DocSplitter()
        self.core_processor = LocalReranker(model_path=model_path, dev_id=device_id)
        self.post_processor = DocRetriever(model_path=model_path)

        self.structured_pre_processor = StructuredDocSplitter()
        self.structured_post_processor = StructuredDocRetriever()

    def run_doc_qa(self, context: str, question: str, target_tokens: int, target_rate: float):
        sentences_list = self.pre_processor.split_text(text=context)
        ranker_result = self.core_processor.rerank(query=question, texts=sentences_list)
        dp = DocRetrieverPara(None, sentences_list, ranker_result, target_tokens, target_rate, True)
        compressed_context = self.post_processor.assemble_result(dp)

        return compressed_context

    def run_structured_doc_qa(self, raw_data: List, question: str, topk: int = 5):
        data_dict = self.structured_pre_processor.split_text(raw_data=raw_data)
        ranker_result = self.core_processor.rerank(query=question, texts=list(data_dict.keys()))
        compressed_context = self.structured_post_processor.assemble_result(data_dict, ranker_result, topk)

        return compressed_context
