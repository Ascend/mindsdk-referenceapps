# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
from paddle.base import libpaddle
from mx_rag.chain import SingleText2TextChain
from mx_rag.embedding.local import TextEmbedding
from mx_rag.embedding.service import TEIEmbedding
from mx_rag.llm import Text2TextLLM
from mx_rag.reranker.local import LocalReranker
from mx_rag.reranker.service import TEIReranker
from mx_rag.retrievers import Retriever
from mx_rag.storage.document_store import SQLiteDocstore
from mx_rag.storage.vectorstore import MindFAISS
from mx_rag.storage.vectorstore.vectorstore import SimilarityStrategy
from mx_rag.utils import ClientParam
import traceback

def rag_demo_query():
    parse = argparse.ArgumentParser()
    parse.add_argument("--embedding_path", type=str, default="/home/data/acge_text_embedding", metavar="", help="embedding模型本地路径;类型:str")
    parse.add_argument("--tei_emb", type=bool, default=False, metavar="", help="是否使用TEI服务化的embedding模型;类型:bool;默认值:False")
    parse.add_argument("--embedding_url", type=str, default="http://127.0.0.1:8080/embed", metavar="", help="使用TEI服务化的embedding模型url地址;类型:str")
    parse.add_argument("--embedding_dim", type=int, default=1024, metavar="", help="embedding模型向量维度;类型:int;默认值:1024")
    parse.add_argument("--llm_url", type=str, default="http://127.0.0.1:1025/v1/chat/completions", metavar="", help="大模型url地址;类型:str")
    parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat", metavar="", help="大模型名称;类型:str")
    parse.add_argument("--score_threshold", type=float, default=0.5, metavar="", help="相似性得分的阈值，大于阈值认为检索的信息与问题越相关,取值范围[0,1];类型:float;默认值:0.5")
    parse.add_argument("--tei_reranker", type=bool, default=False, metavar="", help="是否使用TEI服务化的reranker模型;类型:bool;默认值:False")
    parse.add_argument("--reranker_path", type=str, default=None, metavar="", help="reranker模型本地路径;类型:str;默认值:None")
    parse.add_argument("--reranker_url", type=str,  default=None, metavar="", help="使用TEI服务化的embedding模型url地址;类型:str;默认值:None")
    parse.add_argument("--query", type=str, default="请描述2024年高考作文题目", metavar="", help="用户问题;类型:str")

    args = parse.parse_args().__dict__
    embedding_path: str = args.pop('embedding_path')
    embedding_url: str = args.pop('embedding_url')
    tei_emb: bool = args.pop('tei_emb')
    embedding_dim: int = args.pop('embedding_dim')
    llm_url: str = args.pop('llm_url')
    model_name: str = args.pop('model_name')
    score_threshold: int = args.pop('score_threshold')
    query: str = args.pop('query')

    try:
        # 设置向量检索使用的npu卡，具体可以用的卡可执行npu-smi info查询获取
        dev = 0
        # 加载embedding模型，请根据模型具体路径适配
        if tei_emb:
            emb = TEIEmbedding(url=embedding_url, client_param=ClientParam(use_http=True))
        else:
            emb = TextEmbedding(model_path=embedding_path, dev_id=dev)

        # 初始化向量数据库
        vector_store = MindFAISS(x_dim=embedding_dim,
                                 similarity_strategy=SimilarityStrategy.FLAT_L2,
                                 devs=[dev],
                                 load_local_index="./faiss.index",
                                 auto_save=True
                                 )
        # 初始化文档chunk关系数据库
        chunk_store = SQLiteDocstore(db_path="./sql.db")

        # Step2在线问题答复,初始化检索器
        text_retriever = Retriever(vector_store=vector_store,
                                   document_store=chunk_store,
                                   embed_func=emb.embed_documents,
                                   k=1,
                                   score_threshold=score_threshold
                                   )
        # 配置reranker，请根据模型具体路径适配
        reranker_path = args.get("reranker_path")
        reranker_url = args.get("reranker_url")
        tei_reranker = args.get("tei_reranker")
        if tei_reranker:
            reranker = TEIReranker(url=reranker_url, client_param=ClientParam(use_http=True))
        elif reranker_path is not None:
            reranker = LocalReranker(model_path=reranker_path, dev_id=dev)
        else:
            reranker = None
        # 配置text生成text大模型chain，具体ip端口请根据实际情况适配修改
        llm=Text2TextLLM(base_url=llm_url, model_name=model_name, client_param=ClientParam(use_http=True, timeout=60))
        text2text_chain = SingleText2TextChain(llm=llm,
                                               retriever=text_retriever,
                                               reranker=reranker
                                               )
        # 知识问答
        res = text2text_chain.query(text=query)
        # 打印结果
        print(res)
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(stack_trace)
        

if __name__ == '__main__':
    rag_demo_query()