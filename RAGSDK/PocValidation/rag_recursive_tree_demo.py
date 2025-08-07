# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
from loguru import logger
from langchain.text_splitter import RecursiveCharacterTextSplitter
from paddle.base import libpaddle
from mx_rag.document import LoaderMng
from mx_rag.document.loader import DocxLoader, PdfLoader
from mx_rag.embedding.local import TextEmbedding
from mx_rag.knowledge.handler import upload_files_build_tree
from mx_rag.knowledge.knowledge import KnowledgeStore, KnowledgeTreeDB
from mx_rag.llm import Text2TextLLM
from mx_rag.recursive_tree import TreeBuilderConfig, TreeRetrieverConfig, TreeRetriever, TreeText2TextChain
from mx_rag.recursive_tree.tree_structures import save_tree
from mx_rag.storage.document_store import SQLiteDocstore
from mx_rag.utils import ClientParam
from transformers import AutoTokenizer


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_default_metavar_for_optional(self, action):
        return action.type.__name__

    def _get_default_metavar_for_positional(self, action):
        return action.type.__name__


def rag_recursive_tree_demo():
    try:
        parse = argparse.ArgumentParser(formatter_class=CustomFormatter)
        parse.add_argument("--embedding_path", type=str, default="/home/data/acge_text_embedding",
                           help="embedding模型本地路径")
        parse.add_argument("--white_path", type=str, nargs='+', default=["/home"], help="文件白名单路径")
        parse.add_argument("--file_path", type=str,
                           default="/home/HwHiAiUser/MindIE 1.0.RC3 安装指南 01.pdf",
                           help="要上传的文件路径，需在白名单路径下")
        parse.add_argument("--llm_url", type=str, default="http://127.0.0.1:1025/v1/chat/completions",
                           help="大模型url地址")
        parse.add_argument("--query", type=str, default="请介绍MindIE容器化部署和制造镜像的步骤。", help="用户问题")
        parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat", help="大模型名称")
        parse.add_argument("--tokenizer_path", type=str, default="/home/data/Llama3-8B-Chinese-Chat/",
                           help="大模型tokenizer参数路径")
        args = parse.parse_args().__dict__

        embedding_path: str = args.pop('embedding_path')
        white_path: list[str] = args.pop('white_path')
        file_path: str = args.pop('file_path')
        llm_url: str = args.pop('llm_url')
        query: str = args.pop('query')
        model_name: str = args.pop('model_name')
        tokenizer_path: str = args.pop('tokenizer_path')

        # Step1离线构建知识库,首先注册文档处理器
        loader_mng = LoaderMng()
        # 加载文档加载器，可以使用mxrag自有的，也可以使用langchain的
        loader_mng.register_loader(loader_class=PdfLoader, file_types=[".pdf"])
        loader_mng.register_loader(loader_class=DocxLoader, file_types=[".docx"])
        # 加载文档切分器，使用langchain的
        loader_mng.register_splitter(splitter_class=RecursiveCharacterTextSplitter,
                                     file_types=[".pdf", ".docx"])
        # 设置向量检索使用的npu卡，具体可以用的卡可执行npu-smi info查询获取
        dev = 0
        # 加载embedding模型，请根据模型具体路径适配
        text_emb = TextEmbedding(model_path=embedding_path, dev_id=dev)
        # 初始化文档chunk关系数据库
        document_store = SQLiteDocstore(db_path="./sql.db")
        # 初始化TreeText2TextChain实例，具体ip、端口、llm请根据实际情况修改。
        # 在构建树过程中总结摘要时会使用，最后问答也会使用，问答调用前设置tree_retriever。
        tree_chain = TreeText2TextChain(
            llm=Text2TextLLM(base_url=llm_url, model_name=model_name,
                             client_param=ClientParam(use_http=True, timeout=600)))
        # 使用模型的tokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
        # 初始化递归树构建的参数
        tree_builder_config = TreeBuilderConfig(tokenizer=tokenizer, summarization_model=tree_chain)
        # 初始化递归树知识管理
        knowledge = KnowledgeTreeDB(KnowledgeStore("./sql.db"), chunk_store=document_store, knowledge_name="test",
                                    white_paths=white_path, tree_builder_config=tree_builder_config)
        # 上传领域知识文档，方法会返回构建树实例，当前仅支持同时上传一个文件
        tree = upload_files_build_tree(knowledge, file_path, loader_mng=loader_mng,
                                       embed_func=text_emb.embed_documents, force=True)
        # 初始化递归树检索器配置参数
        tree_retriver_config = TreeRetrieverConfig(tokenizer=tokenizer, embed_func=text_emb.embed_documents,
                                                   collapse_tree=False, top_k=3)
        # 初始化递归树检索器
        tree_retriever = TreeRetriever(tree_retriver_config, tree)
        # 设置TreeText2TextChain的检索器
        tree_chain.set_tree_retriever(tree_retriever)
        # 知识问答
        answer = tree_chain.query(query, max_tokens=1000)
        # 打印结果
        logger.info(answer)
        # 递归树Tree实例序列化保存为json文件，使用load_tree方法反序列化
        save_path = "./tree.json"
        save_tree(tree, save_path)
    except Exception as e:
        logger.error(f"run demo failed: {e}")


if __name__ == '__main__':
    rag_recursive_tree_demo()
