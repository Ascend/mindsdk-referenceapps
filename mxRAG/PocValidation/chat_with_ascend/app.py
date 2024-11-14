# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
import os
import shutil
import gradio as gr
from loguru import logger
from paddle.base import libpaddle
from mx_rag.chain import SingleText2TextChain
from mx_rag.embedding.local import TextEmbedding
from mx_rag.llm import Text2TextLLM, LLMParameterConfig
from mx_rag.retrievers import Retriever
from mx_rag.storage.document_store import SQLiteDocstore
from mx_rag.storage.vectorstore import MindFAISS
from mx_rag.storage.vectorstore.vectorstore import SimilarityStrategy
from mx_rag.utils import ClientParam
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from mx_rag.document.loader import DocxLoader, PdfLoader
from mx_rag.knowledge import KnowledgeDB
from mx_rag.knowledge.knowledge import KnowledgeStore
from mx_rag.knowledge.handler import upload_files, LoaderMng

global text2text_chain
global text_knowledge_db
global loader_mng
global text_emb


def bot_response(history,
                 max_tokens: int = 512,
                 temperature: float = 0.5,
                 top_p: float = 0.95
                 ):
    # 将最新的问题传给RAG
    try:
        response = text2text_chain.query(history[-1][0],
                                        LLMParameterConfig(max_tokens=max_tokens, temperature=temperature, top_p=top_p,
                                                           stream=True))
        # 返回迭代器
        history[-1][1] = '推理错误'
        for res in response:
            history[-1][1] = '推理错误' if res['result'] is None else res['result']
            yield history
        yield history
    except Exception as err:
        logger.info(f"query failed, find exception: {err}")
        history[-1][1] = "推理错误"
        yield history


def user_query(user_message, history):
    return "", history + [[user_message, None]]


def clear_history(history):
    return []


SAVE_FILE_PATH = "/tmp/document_files"


def file_upload(files):
    # 指定保存文件的文件夹
    if not os.path.exists(SAVE_FILE_PATH):
        os.makedirs(SAVE_FILE_PATH)
    if files is None or len(files) == 0:
        print('no file need save')
    for file in files:
        try:
            # 上传领域知识文档
            shutil.copy(file.name, SAVE_FILE_PATH)
            # 知识库:chunk\embedding\add
            upload_files(text_knowledge_db, [file.name], loader_mng=loader_mng, embed_func=text_emb.embed_documents,
                         force=True)
            print(f"file {file.name} save to {SAVE_FILE_PATH}.")
        except Exception as err:
            logger.error(f"save failed, find exception: {err}")


def file_change(files, upload_btn):
    print("file changes")


def build_demo():
    with gr.Blocks() as demo:
        gr.HTML("<center><h1>检索增强生成(RAG)对话</h1><p>powered by MindX RAG</p><center>")
        with gr.Row():
            with gr.Column(scale=100):
                with gr.Row():
                    model_select = gr.Dropdown(choices=["Default"], value="Default", container=False, interactive=True)
                with gr.Row():
                    files = gr.Files(
                        height=300,
                        file_count="multiple",
                        file_types=[".docx", ".txt", ".md", ".pdf"],
                        interactive=True,
                        label="上传知识库文档"
                    )
                with gr.Row():
                    upload_btn = gr.Button("上传文件")
                with gr.Row():
                    with gr.Accordion(label='知识库情况'):
                        temperature = gr.Slider(
                            minimum=0.01,
                            maximum=2,
                            value=0.5,
                            step=0.01,
                            interactive=True,
                            label="温度",
                            info="Token生成的随机性"
                        )
                        top_p = gr.Slider(
                            minimum=0.01,
                            maximum=1,
                            value=0.95,
                            step=0.05,
                            interactive=True,
                            label="Top P",
                            info="累计概率总和阈值"
                        )
                        max_tokens = gr.Slider(
                            minimum=100,
                            maximum=1024,
                            value=512,
                            step=1,
                            interactive=True,
                            label="最大tokens",
                            info="输入+输出最多的tokens数"
                        )
            with gr.Column(scale=200):
                chatbot = gr.Chatbot(height=500)
                with gr.Row():
                    msg = gr.Textbox(placeholder="在此输入问题...", container=False)
                with gr.Row():
                    send_btn = gr.Button(value="发送", variant="primary")
                    clean_btn = gr.Button(value="清空历史")
            send_btn.click(user_query, [msg, chatbot], [msg, chatbot], queue=False).then(bot_response,
                                                                                         [chatbot, max_tokens,
                                                                                          temperature, top_p], chatbot)
            clean_btn.click(clear_history, chatbot, chatbot)
            files.change(file_change, [], [])
            upload_btn.click(file_upload, files, []).then(clear_history, files, files)
    return demo


def create_gradio(port):
    demo = build_demo()
    demo.queue()
    demo.launch(share=True, server_name="0.0.0.0", server_port=port)


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_default_metavar_for_optional(self, action):
        return action.type.__name__

    def _get_default_metavar_for_positional(self, action):
        return action.type.__name__


if __name__ == '__main__':
    parse = argparse.ArgumentParser(formatter_class=CustomFormatter)
    parse.add_argument("--embedding_path", type=str, default="/home/data/acge_text_embedding",
                       help="embedding模型本地路径")
    parse.add_argument("--embedding_dim", type=int, default=1024, help="embedding模型向量维度")
    parse.add_argument("--llm_url", type=str, default="http://127.0.0.1:1025/v1/chat/completions", help="大模型url地址")
    parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat", help="大模型名称")
    parse.add_argument("--port", type=str, default=8080, help="web后端端口")

    args = parse.parse_args()

    try:
        # 离线构建知识库,首先注册文档处理器
        loader_mng = LoaderMng()
        # 加载文档加载器，可以使用mxrag自有的，也可以使用langchain的
        loader_mng.register_loader(loader_class=TextLoader, file_types=[".txt", ".md"])
        loader_mng.register_loader(loader_class=DocxLoader, file_types=[".docx"])
        loader_mng.register_loader(loader_class=PdfLoader, file_types=[".pdf"])

        # 加载文档切分器，使用langchain的
        loader_mng.register_splitter(splitter_class=RecursiveCharacterTextSplitter,
                                     file_types=[".docx", ".txt", ".md", ".pdf"],
                                     splitter_params={"chunk_size": 750,
                                                      "chunk_overlap": 150,
                                                      "keep_separator": False
                                                      }
                                     )

        # 设置向量检索使用的npu卡，具体可以用的卡可执行npu-smi info查询获取
        dev = 0

        # 初始化向量数据库
        vector_store = MindFAISS(x_dim=args.embedding_dim,
                                 similarity_strategy=SimilarityStrategy.FLAT_L2,
                                 devs=[dev],
                                 load_local_index="./faiss.index",
                                 auto_save=True
                                 )
        # 初始化文档chunk关系数据库
        chunk_store = SQLiteDocstore(db_path="./sql.db")
        # 初始化知识管理关系数据库
        knowledge_store = KnowledgeStore(db_path="./sql.db")
        # 初始化知识库管理
        text_knowledge_db = KnowledgeDB(knowledge_store=knowledge_store,
                                        chunk_store=chunk_store,
                                        vector_store=vector_store,
                                        knowledge_name="test",
                                        white_paths=["/tmp"]
                                        )

        # 加载embedding模型，请根据模型具体路径适配
        text_emb = TextEmbedding(model_path=args.embedding_path, dev_id=dev)

        # Step2在线问题答复,初始化检索器
        text_retriever = Retriever(vector_store=vector_store,
                                   document_store=chunk_store,
                                   embed_func=text_emb.embed_documents,
                                   k=1,
                                   score_threshold=0.4
                                   )
        # 配置text生成text大模型chain，具体ip端口请根据实际情况适配修改
        llm = Text2TextLLM(base_url=args.llm_url, model_name=args.model_name, client_param=ClientParam(use_http=True))
        text2text_chain = SingleText2TextChain(llm=llm,
                                               retriever=text_retriever,
                                               )
        create_gradio(int(args.port))
    except Exception as e:
        logger.info(f"exception happed :{e}")
