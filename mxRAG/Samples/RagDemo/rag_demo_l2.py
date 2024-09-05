# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
from paddle.base import libpaddle
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from mx_rag.document.loader import DocxLoader
from mx_rag.chain import SingleText2TextChain
from mx_rag.embedding.local import TextEmbedding
from mx_rag.knowledge import KnowledgeDB
from mx_rag.knowledge.knowledge import KnowledgeStore
from mx_rag.llm import Text2TextLLM
from mx_rag.reranker.local import LocalReranker
from mx_rag.retrievers import Retriever
from mx_rag.storage.document_store import SQLiteDocstore
from mx_rag.storage.vectorstore import MindFAISS
from mx_rag.storage.vectorstore.vectorstore import SimilarityStrategy
from mx_rag.knowledge.handler import upload_files
from mx_rag.knowledge.doc_loader_mng import LoaderMng


def rag_demo_l2():
    parse = argparse.ArgumentParser()
    parse.add_argument("--embedding_path", type=str, default="/home/data/acge_text_embedding")
    parse.add_argument("--embedding_dim", type=int, default=1024)
    parse.add_argument("--white_path", type=list[str], default=["/home"])
    parse.add_argument("--file_path", type=str, default="/home/data/gaokao.md")
    parse.add_argument("--llm_url", type=str, default="http://<ip>:<port>/v1/chat/completions")
    parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat")
    parse.add_argument("--score_threshold", type=int, default=1)
    parse.add_argument("--reranker_path", type=str, default=None)
    parse.add_argument("--query", type=str, default="请描述2024年高考作文题目")

    args = parse.parse_args().__dict__
    embedding_path: str = args.pop('embedding_path')
    embedding_dim: int = args.pop('embedding_dim')
    white_path: list[str] = args.pop('white_path')
    file_path: str = args.pop('file_path')
    llm_url: str = args.pop('llm_url')
    model_name: str = args.pop('model_name')
    score_threshold: int = args.pop('score_threshold')
    query: str = args.pop('query')

    try:
        # Step1离线构建知识库,首先注册文档处理器
        loader_mng = LoaderMng()
        # 加载文档加载器，可以使用mxrag自有的，也可以使用langchain的
        loader_mng.register_loader(loader_class=TextLoader, file_types=[".txt", ".md"])
        loader_mng.register_loader(loader_class=DocxLoader, file_types=[".docx"])
        # 加载文档切分器，使用langchain的
        loader_mng.register_splitter(splitter_class=RecursiveCharacterTextSplitter,
                                     file_types=[".docx", ".txt", ".md"],
                                     splitter_params={"chunk_size": 750,
                                                      "chunk_overlap": 150,
                                                      "keep_separator": False
                                                      }
                                     )
        # 设置向量检索使用的npu卡，具体可以用的卡可执行npu-smi info查询获取
        dev = 0
        # 加载embedding模型，请根据模型具体路径适配
        emb = TextEmbedding(model_path=embedding_path, dev_id=dev)
        # 初始化向量数据库
        vector_store = MindFAISS(x_dim=embedding_dim,
                                 similarity_strategy=SimilarityStrategy.FLAT_L2,
                                 devs=[dev],
                                 load_local_index="./faiss.index"
                                 )
        # 初始化文档chunk关系数据库
        chunk_store = SQLiteDocstore(db_path="./sql.db")
        # 初始化知识管理关系数据库
        knowledge_store = KnowledgeStore(db_path="./sql.db")
        # 初始化知识库管理
        knowledge_db = KnowledgeDB(knowledge_store=knowledge_store,
                                   chunk_store=chunk_store,
                                   vector_store=vector_store,
                                   knowledge_name="test",
                                   white_paths=white_path
                                   )
        # 完成离线知识库构建,上传领域知识gaokao.docx文档。
        upload_files(knowledge=knowledge_db,
                     files=[file_path],
                     loader_mng=loader_mng,
                     embed_func=emb.embed_documents,
                     force=True
                     )
        # Step2在线问题答复,初始化检索器
        text_retriever = Retriever(vector_store=vector_store,
                                   document_store=chunk_store,
                                   embed_func=emb.embed_documents,
                                   k=1,
                                   score_threshold=score_threshold
                                   )
        # 配置reranker，请根据模型具体路径适配
        reranker_path = args.get("reranker_path")
        if reranker_path is not None:
            reranker = LocalReranker(model_path=reranker_path, dev_id=dev)
        else:
            reranker = None
        # 配置text生成text大模型chain，具体ip端口请根据实际情况适配修改
        text2text_chain = SingleText2TextChain(llm=Text2TextLLM(base_url=llm_url,
                                                                model_name=model_name,
                                                                use_http=True,
                                                                timeout=60),
                                               retriever=text_retriever,
                                               reranker=reranker
                                               )
        # 知识问答
        res = text2text_chain.query(text=query)
        # 打印结果
        print(res)
    except Exception as e:
        print(f"run demo failed: {e}")


if __name__ == '__main__':
    rag_demo_l2()