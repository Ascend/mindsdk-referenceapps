# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import os
import time
from paddle.base import libpaddle
from langchain_community.document_loaders import TextLoader
import argparse
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer
from mx_rag.cache import CacheConfig, SimilarityCacheConfig, MxRAGCache,CacheChainChat,QAGenerationConfig,QAGenerate,MarkDownParser
from mx_rag.chain import SingleText2TextChain
from mx_rag.embedding.local import TextEmbedding
from mx_rag.knowledge import KnowledgeDB, KnowledgeStore, KnowledgeDB, upload_files, LoaderMng
from mx_rag.llm import Text2TextLLM
from mx_rag.retrievers import Retriever
from mx_rag.storage.document_store import SQLiteDocstore
from mx_rag.storage.vectorstore import MindFAISS, SimilarityStrategy
from mx_rag.utils import ClientParam
import traceback

def rag_cache_demo():
    parse = argparse.ArgumentParser()
    parse.add_argument("--embedding_path", type=str, default="/home/data/acge_text_embedding")
    parse.add_argument("--embedding_dim", type=int, default=1024)
    parse.add_argument("--reranker_path", type=str, default="home/data/bge-reranker-large")
    parse.add_argument("--white_path", type=list[str], default=["/home"])
    parse.add_argument("--file_path", type=str, default="/home/HwHiAiUser/gaokao.md")
    parse.add_argument("--cache_save_path", type=str, default="/home/HwHiAiUser/cache_dave_dir")
    parse.add_argument("--llm_url", type=str, default="http://<ip>:<port>/v1/chat/completions")
    parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat")
    parse.add_argument("--score_threshold", type=float, default=0.5)
    parse.add_argument("--query", type=str, default="请描述2024年高考作文题目")
    parse.add_argument("--tokenizer_path", type=str, default="/home/data/Llama3-8B-Chinese-Chat/")
    parse.add_argument("--npu_device_id", type=int, default=0)
    args = parse.parse_args()

    try:
        # memory cache缓存作为L1缓存
        cache_config = CacheConfig(cache_size=100, data_save_folder=args.cache_save_path)
        # similarity cache缓存作为L2缓存
        similarity_config = SimilarityCacheConfig(
            vector_config={"vector_type":"npu_faiss_db",
                           "x_dim":args.embedding_dim,
                           "devs":[args.npu_device_id],
                           "similarity_strategy":SimilarityStrategy.FLAT_L2},
            cache_config="sqlite",
            emb_config={"embedding_type":"local_text_embedding",
                        "x_dim": args.embedding_dim,
                        "model_path":args.embedding_path,
                        "dev_id":args.npu_device_id
                        },
            similarity_config={
                "similarity_type":"local_reranker",
                "model_path": args.embedding_path,
                "dev_id": args.npu_device_id
            },
            retrieval_top_k=5,
            cache_size=1000,
            similarity_threshold=0.8,
            data_save_folder=args.cache_save_path)

        # 构造memory cache实例
        memory_cache = MxRAGCache("memory_cache", cache_config)
        # 构造similarity cache实例
        similarity_cache = MxRAGCache("similarity_cache", similarity_config)
        # memory_cache和similarity_cache串联形成多级缓存入口是memory cache
        memory_cache.join(similarity_cache)
        # 定义用于生成QA的大模型
        client_param= ClientParam(use_http=True, timeout=600)
        llm = Text2TextLLM(base_url=args.llm_url, model_name=args.model_name, client_param=client_param)
        # 返回markdown的标题和内容，标题要和内容相关
        titles, contents = MarkDownParser(os.path.dirname(args.file_path)).parse()
        # 使用大模型计算token大小
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_path)
        # 组装生成QA的配置参数，qas_num为每个文件要生成的QA数量
        config = QAGenerationConfig(titles, contents, tokenizer, llm, qas_num=3)
        # 调用大模型生成QA对
        qas = QAGenerate(config).generate_qa()
        print(f"qas:{qas}")
        # 将QA存入缓存，答案部分需按照json格式保存
        for query, answer in qas.items():
            memory_cache.update(query, json.dumps({"result":answer}))

        # 离线构建知识库，首先注册文档处理器
        loader_mng = LoaderMng()
        # 加载文档加载器，可以使用mxrag自有的，也可以使用langchain的
        loader_mng.register_loader(loader_class=TextLoader, file_types=[".txt", ".md", ".docx"])
        # 加载文档切分器，使用langchain的
        loader_mng.register_splitter(splitter_class=RecursiveCharacterTextSplitter,
                                     file_types=[".txt", ".md", ".docx"],
                                     splitter_params={"chunk_size": 750,
                                                      "chunk_overlap": 150,
                                                      "keep_separator": False
                                                      }
                                     )

        # 初始化向量数据库
        vector_store = MindFAISS(x_dim=args.embedding_dim,
                                 similarity_strategy=SimilarityStrategy.FLAT_L2,
                                 devs=[args.npu_device_id],
                                 load_local_index=os.path.join(args.cache_save_path,"./faiss.index"))

        # 加载embedding模型，请根据模型具体路径适配
        emb = TextEmbedding(model_path=args.embedding_path, dev_id=args.npu_device_id)


        # 初始化文档chunk关系数据库
        chunk_store = SQLiteDocstore(db_path="./sql.db")
        # <可选>初始化知识管理关系数据库
        knowledge_store = KnowledgeStore(db_path="./sql.db")
        # <可选>初始化知识库管理
        knowledge_db = KnowledgeDB(knowledge_store=knowledge_store,
                                   chunk_store=chunk_store,
                                   vector_store=vector_store,
                                   knowledge_name="test",
                                   white_paths=args.white_path
                                   )
        # <可选> 完成离线知识库构建,上传领域知识gaokao.md文档。
        upload_files(knowledge=knowledge_db,
                     files=[args.file_path],
                     loader_mng=loader_mng,
                     embed_func=emb.embed_documents,
                     force=True
                     )

        # 初始化Retriever检索器
        text_retriever = Retriever(vector_store=vector_store,
                                   document_store=chunk_store,
                                   embed_func=emb.embed_documents,
                                   k=3,
                                   score_threshold=args.score_threshold
                                   )

        # 构造cache_chain, 缓存memory cache作为入口
        cache_chain = CacheChainChat(chain=SingleText2TextChain(llm, text_retriever), cache=memory_cache)
        # 提问和网页相关的问题，如果与已生成的QA近似，则会命中返回
        now_time = time.time()
        print(cache_chain.query(args.query))
        print(f"耗时:{time.time() - now_time}s")
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(stack_trace)

    
if __name__ == '__main__':
    rag_cache_demo()