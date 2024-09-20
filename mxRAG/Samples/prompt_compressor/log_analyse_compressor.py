# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from mx_rag.document.splitter import LogSplitter
from mx_rag.reranker.local import Bm25Reranker
from mx_rag.retrievers import LogRetriever


class LogAnaluseCompressor(object):
    def __init__(self):
        self.pre_processor = LogSplitter()
        self.core_processor = Bm25Reranker(None)
        self.post_processor = LogRetriever()

    def run_log_analusis(self, context: str, question: str):
        sentences_list = self.pre_processor.split_text(context)
        ranker_result = self.core_processor.rerank(question, sentences_list)
        compressed_context, reserved_list = self.post_processor.assemble_result(sentences_list, ranker_result)

        return compressed_context, reserved_list