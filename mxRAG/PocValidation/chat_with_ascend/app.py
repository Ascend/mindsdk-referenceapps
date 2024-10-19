# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import os
import shutil
import gradio as gr
from pathlib import Path
from typing import List, Dict, Tuple
from mx_rag.chain import SingleText2TextChain, Text2ImgChain, Img2ImgChain
from mx_rag.document.loader import DocxLoader, ExcelLoader, PdfLoader
from mx_rag.document.splitter import CharTextSplitter
from mx_rag.embedding.local import TextEmbedding, ImageEmbedding
from mx_rag.knowledge import KnowledgeDB
from mx_rag.knowledge.knowledge import KnowledgeStore
from mx_rag.llm import Text2TextLLM, Text2ImgMultiModel, Img2ImgMultiModel
from mx_rag.reranker.local import LocalReranker
from mx_rag.retrievers import Retriever
from mx_rag.storage.document_store import SQLiteDocstore
from mx_rag.storage.vectorstore import MindFAISS
from mx_rag.knowledge.handler import upload_files, upload_dir, delete_files
from loguru import logger

DOC_PARSER_MAP = {
    ".docx": (DocxLoader, CharTextSplitter),
    ".xlsx": (ExcelLoader, CharTextSplitter),
    ".xls": (ExcelLoader, CharTextSplitter),
    ".csv": (ExcelLoader, CharTextSplitter),
    ".pdf": (PdfLoader, CharTextSplitter),
}
SUPPORT_IMAGE_TYPE = (".jpg", ".png")
SUPPORT_DOC_TYPE = (".docx", ".xlsx", ".xls", ".csv", ".pdf")


# 定义解析函数
def parse_file(filepath: str) -> Tuple[List[str], List[Dict[str, str]]]:
    def parse_image(file: Path) -> Tuple[List[str], List[Dict[str, str]]]:
        return [file.as_posix()], [{"path": file.as_posix()}]

    def parse_document(file: Path) -> Tuple[List[str], List[Dict[str, str]]]:
        loader, splitter = DOC_PARSER_MAP.get(file.suffix)
        metadatas = []
        texts = []
        for doc in loader(file.as_posix()).load():
            split_texts = splitter(separator="\n", chunk_size=4000, chunk_overlap=200).split_text(doc.page_content)
            metadatas.extend(doc.metadata for _ in split_texts)
            texts.extend(split_texts)
        return texts, metadatas

    file_obj = Path(filepath)
    if file_obj.suffix in DOC_PARSER_MAP.keys():
        texts, metadatas = parse_document(file_obj)
    elif file_obj.suffix in SUPPORT_IMAGE_TYPE:
        texts, metadatas = parse_image(file_obj)
    else:
        raise ValueError(f"{file_obj.suffix} is not support")
    return texts, metadatas


dev = 0

# 初始化文档chunk关系数据库
chunk_store = SQLiteDocstore(db_path="./sql.db")
# 初始化知识管理关系数据库
knowledge_store = KnowledgeStore(db_path="./sql.db")

text_emb = TextEmbedding("/data/bge-large-zh-v1.5/", dev_id=dev)

text_vector_store = MindFAISS(x_dim=1024, index_type="FLAT:L2", devs=[dev],
                              load_local_index="./text_faiss.index",
                              auto_save=True)

text_knowledge_db = KnowledgeDB(knowledge_store=knowledge_store, chunk_store=chunk_store,
                                vector_store=text_vector_store,
                                knowledge_name="text", white_paths=["/tmp"])

text_retriever = Retriever(text_vector_store, chunk_store, text_emb.embed_texts, k=1, score_threshold=1)

text2text_chain = SingleText2TextChain(
    llm=Text2TextLLM(url="http://51.38.66.29:1025/v1/chat/completions", model_name="chatglm2-6b", timeout=180, use_http=True), retriever=text_retriever)

# 知识文档存储路径
SAVE_FILE_PATH = "tmp/document_files"

def bot_response(history,
                 max_tokens: int = 512,
                 temperature: float = 0.5,
                 top_p: float = 0.95
                 ):
    # 将最新的问题传给RAG
    try:
        respons = text2text_chain.query(history[-1][0], max_tokens=max_tokens, temperature=temperature, top_p=top_p, stream=True)
        # 返回迭代器
        history[-1][1] = '推理错误'
        for res in respons:
            history[-1][1] = '推理错误' if res['result'] is None else res['result']
            yield history
        yield history
    except Exception as e:
        logger.info(f"query failed, find exception: {e}")
        history[-1][1] = "推理错误"
        yield history

def user_query(user_message, history):
    return "", history + [[user_message, None]]


def clear_history(history):
    return []


def check_file_type(file):
    file_type = os.path.splitext(file)[1].lower()
    support_typs = SUPPORT_DOC_TYPE + SUPPORT_IMAGE_TYPE
    return file_type in support_typs


def file_upload(files):
    # 指定保存文件的文件夹
    if not os.path.exists(SAVE_FILE_PATH):
        os.makedirs(SAVE_FILE_PATH)
    if files is None or len(files) == 0:
        print('no file need save')
    for file in files:
        try:
            if check_file_type(file):
                # 上传领域知识文档
                shutil.copy(file.name, SAVE_FILE_PATH)
                # 知识库:chunk\embedding\add
                upload_files(text_knowledge_db, [file.name], parse_func=parse_file, embed_func=text_emb.embed_texts, force=True)
                print(f"file {file.name} save to {SAVE_FILE_PATH}.")
            else:
                print(f"file {file.name} type error.")
        except Exception as e:
            logger.error(f"save failed, find exception: {e}")


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
                        file_types=[".docx", ".xlsx", ".xls", ".csv", ".pdf"],
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
            send_btn.click(user_query, [msg, chatbot], [msg, chatbot], queue=False).then(bot_response, [chatbot, max_tokens, temperature, top_p], chatbot)
            clean_btn.click(clear_history, chatbot, chatbot)
            files.change(file_change, [], [])
            upload_btn.click(file_upload, files, []).then(clear_history, files, files)
    return demo


def create_gradio():
    demo = build_demo()
    demo.queue()
    demo.launch(share=True, server_name="0.0.0.0", server_port=10001)


if __name__ == "__main__":
    create_gradio()
