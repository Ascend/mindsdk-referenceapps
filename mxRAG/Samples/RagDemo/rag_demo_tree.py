# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
from paddle.base import libpaddle
from pathlib import Path
from typing import Tuple, List, Dict
from transformers import PreTrainedTokenizerBase, AutoTokenizer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from mx_rag.chain.tree_text_to_text import TreeText2TextChain
from mx_rag.document.loader import DocxLoader, ExcelLoader, PdfLoader
from mx_rag.embedding.local import TextEmbedding
from mx_rag.knowledge.handler import save_tree, upload_files_build_tree
from mx_rag.knowledge.knowledge import KnowledgeStore,KnowledgeTreeDB
from mx_rag.llm import Text2TextLLM
from mx_rag.retrievers import TreeBuilderConfig, TreeRetrieverConfig, TreeRetriever
from mx_rag.retrievers.tree_retriever import split_text
from mx_rag.storage.document_store import SQLiteDocstore
import traceback

def rag_demo_tree():
    parse = argparse.ArgumentParser()
    parse.add_argument("--embedding_path", type=str, default="/home/data/acge_text_embedding")
    parse.add_argument("--embedding_dim", type=int, default=1024)
    parse.add_argument("--white_path", type=list[str], default=["/home"])
    parse.add_argument("--file_path", type=str, default="/home/data/MindIE.docx")
    parse.add_argument("--llm_url", type=str, default="http://51.38.66.29.1025/v1/chat/completions")
    parse.add_argument("--llm_tokenizer", type=str, default="/home/mxaiagent/workspace/llama3-8B-Chinese-Chat/")
    parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat")
    parse.add_argument("--query", type=str, default="linux下如何安装MindIE?请介绍详细步骤，用中文回答")

    args = parse.parse_args().__dict__
    embedding_path: str = args.pop('embedding_path')
    white_path: list[str] = args.pop('white_path')
    file_path: str = args.pop('file_path')
    llm_url: str = args.pop('llm_url')
    model_name: str = args.pop('model_name')
    query: str = args.pop('query')
    llm_tokenizer: str = args.pop('llm_tokenizer')

    DOC_PARSER_MAP = {
        ".docx": (DocxLoader, RecursiveCharacterTextSplitter),
        ".xlsx": (ExcelLoader, RecursiveCharacterTextSplitter),
        ".xls": (ExcelLoader, RecursiveCharacterTextSplitter),
        ".csv": (ExcelLoader, RecursiveCharacterTextSplitter),
        ".pdf": (PdfLoader, RecursiveCharacterTextSplitter),
    }
    # 定义解析函数
    def token_parse_document_file(filepath: str,
                                  tokenizer: PreTrainedTokenizerBase,
                                  max_tokens: int) -> Tuple[List[str], List[Dict[str, str]]]:
        file = Path(filepath)
        loader, splitter = DOC_PARSER_MAP.get(file.suffix,(None, None))
        if loader is None:
            raise ValueError(f"{file.suffix} is not support")
        metadatas = []
        texts = []
        for doc in loader(file.as_posix()).load():
            split_texts = split_text(doc.page_content, tokenizer, max_tokens)
            metadatas.extend(doc.metadata for _ in split_texts)
            texts.extend(split_texts)
        return texts, metadatas

    try:
        # 设置向量检索使用的npu卡，具体可以用的卡可执行npu-smi info查询获取
        dev = 0
        # 加载embedding模型，请根据模型具体路径适配
        text_emb = TextEmbedding(model_path=embedding_path, dev_id=dev)
        # 初始化文档chunk关系数据库
        document_store = SQLiteDocstore(db_path="./sql.db")
        # 初始化TreeText2TextChain实例，具体ip、端口、llm请根据实际情况修改。在构建树总结摘要时会使用，最后问答也会使用，问答调用前设置tree_retriever
        tree_chain = TreeText2TextChain(llm=Text2TextLLM(base_url=llm_url,
                                                         model_name=model_name,
                                                         timeout=180,
                                                         use_http=True)
                                        )
        # 使用模型的tokenizer
        tokenizer = AutoTokenizer.from_pretrained(llm_tokenizer)
        # 初始化递归树构建的参数
        tree_builder_config = TreeBuilderConfig(tokenizer=tokenizer, summarization_model=tree_chain)
        # 初始化知识管理关系数据库
        knowledge_store = KnowledgeStore(db_path="./sql.db")
        # 初始化递归树知识管理
        knowledge = KnowledgeTreeDB(knowledge_store=knowledge_store,
                                    chunk_store=document_store,
                                    knowledge_name="test",
                                    white_path=white_path,
                                    tree_builder_config=tree_builder_config
                                    )
        # 上传领域知识文档，方法会返回构建树实例，当前仅支持同时上传一个文件
        tree = upload_files_build_tree(knowledge=knowledge,
                                       files=[file_path],
                                       parse_func=token_parse_document_file,
                                       embed_func=text_emb.embed_documents,
                                       force=True
                                       )
        # 初始化递归树检索器配置
        tree_retriever_config = TreeRetrieverConfig(tokenizer=tokenizer,
                                                   embed_func=text_emb.embed_documents,
                                                   collapse_tree=False,
                                                   top_k=3)
        # 初始化递归树检索器
        tree_retriever = TreeRetriever(config=tree_retriever_config, tree=tree)
        # 设置TreeText2TextChain的检索器
        tree_chain.set_tree_retriever(tree_retriver=tree_retriever)
        # 知识问答
        answer = tree_chain.query(text=query)
        # 打印结果
        print(answer)
        # 递归树Tree实例化保存为json文件，使用load_tree方法反序列化
        save_path = "./tree.json"
        save_tree(tree=tree, file_path=save_path)
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(stack_trace)
    finally:
        import acl
        acl.finalize()


if __name__ == '__main__':
    rag_demo_tree()



