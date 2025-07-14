# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
import gradio as gr
import os
import shutil
import sys
from langchain.retrievers import EnsembleRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from loguru import logger
from mx_rag.document.loader import DocxLoader, PdfLoader, ExcelLoader
from mx_rag.embedding.local import TextEmbedding
from mx_rag.embedding.service import TEIEmbedding
from mx_rag.knowledge import KnowledgeStore, KnowledgeDB
from mx_rag.knowledge.handler import upload_files, LoaderMng
from mx_rag.llm import Text2TextLLM, LLMParameterConfig
from mx_rag.reranker.local import LocalReranker
from mx_rag.reranker.service import TEIReranker
from mx_rag.retrievers import Retriever
from mx_rag.retrievers.full_text_retriever import FullTextRetriever
from mx_rag.storage.document_store import SQLiteDocstore, MilvusDocstore
from mx_rag.storage.vectorstore import MilvusDB
from mx_rag.utils import ClientParam
from paddle.base import libpaddle
from pymilvus import MilvusClient
from typing import List, Iterator, Dict

sys.tracebacklimit = 1000

user_id = "7d1d04c1-dd5f-43f8-bad5-99795f24bce6"

default_prompt = """<指令>以下是提供的背景知识，请简洁和专业地回答用户的问题。如果无法从已知信息中得到答案，请根据自身经验做出回答。<指令>\n背景知识：{context}\n用户问题：{question}"""
llm_prompt = default_prompt
# 初始化知识管理关系数据库
knowledge_store = KnowledgeStore(db_path="./knowledge_store_sql.db")

KnowledgeDB_Map = {}

milvus_url = "http://127.0.0.1:19530"


# 创建新的知识库
def get_knowledge_db(knowledge_name: str):
    knowledge_name = get_knowledge_ename(knowledge_name)
    if knowledge_name in KnowledgeDB_Map.keys():
        return KnowledgeDB_Map["knowledge_name"][2]
    logger.info(f"get knowledge_name:{knowledge_name}")
    index_name, db_name = get_db_file_names(knowledge_name)

    milvus_url = os.environ.get("milvus_url")
    milvus_client = MilvusClient(milvus_url)
    vector_store = MilvusDB.create(client=milvus_client, x_dim=int(os.environ.get("embedding_dim")),
                                   collection_name=f"{knowledge_name}_vector")
    chunk_store = MilvusDocstore(milvus_client, collection_name=f"{knowledge_name}_chunk")

    knowledge_store.add_knowledge(knowledge_name, user_id=user_id)
    # 初始化知识库管理
    knowledge_db = KnowledgeDB(knowledge_store=knowledge_store,
                               chunk_store=chunk_store,
                               vector_store=vector_store,
                               knowledge_name=knowledge_name,
                               white_paths=["/tmp"],
                               user_id=user_id)
    KnowledgeDB_Map["knowledge_name"] = (vector_store, chunk_store, knowledge_db)

    return vector_store, chunk_store, knowledge_db


# 创建检索器
def creat_dense_retriever(knowledge_name: str, top_k, score_threshold):
    vector_store, chunk_store, _ = get_knowledge_db(knowledge_name)
    # 初始化文档chunk关系数据库
    dense_retriever = Retriever(vector_store=vector_store,
                                document_store=chunk_store,
                                embed_func=text_emb.embed_documents,
                                k=top_k,
                                score_threshold=score_threshold)

    return dense_retriever


def creat_sparse_retriever(knowledge_name: str, top_k):
    _, chunk_store, _ = get_knowledge_db(knowledge_name)
    # 初始化文档chunk关系数据库
    sparse_retriever = FullTextRetriever(
        document_store=chunk_store,
        k=top_k)

    return sparse_retriever


# 删除知识库
def delete_knowledge_db(knowledge_name: str):
    knowledge_name = get_knowledge_ename(knowledge_name)
    knowledge_names = knowledge_store.get_all_knowledge_name(user_id)

    if knowledge_name in knowledge_names:
        _, _, knowledge_db = get_knowledge_db(knowledge_name)
        # 删除知识中的所有信息，包含文件，文本，向量
        knowledge_db.delete_all()
        milvus_url = os.environ.get("milvus_url")
        milvus_client = MilvusClient(milvus_url)
        vector_store = MilvusDB.create(client=milvus_client, x_dim=int(os.environ.get("embedding_dim")),
                                       collection_name=f"{knowledge_name}_vector")
        chunk_store = MilvusDocstore(milvus_client, collection_name=f"{knowledge_name}_chunk")

        vector_store.drop_collection()
        chunk_store.drop_collection()

    return get_knowledge_info()


# 获取知识库列表
def get_knowledge_info():
    knowledge_info = knowledge_store.get_all_knowledge_info(user_id)
    knowledge_names = [info.knowledge_name for info in knowledge_info]
    return knowledge_names, len(knowledge_names)


# 获取知识库中文档列表
def get_document(knowledge_name: str):
    _, _, knowledge_db = get_knowledge_db(knowledge_name)
    doc_names = [doc_model.document_name for doc_model in knowledge_db.get_all_documents()]
    return knowledge_name, doc_names, len(doc_names)


# 清空知识库中文档列表
def clear_file_in_kg(knowledge_name: str):
    knowledge_name, doc_names, doc_cnt = get_document(knowledge_name)
    if doc_cnt > 0:
        _, _, knowledge_db = get_knowledge_db(knowledge_name)
        for doc_name in doc_names:
            knowledge_db.delete_file(doc_name)
        return get_document(knowledge_name)
    else:
        return knowledge_name, doc_names, 0


# 删除知识库中的文件
def delete_document_in_kg(knowledge_name: str, files: str):
    _, _, knowledge_db = get_knowledge_db(knowledge_name)
    for file in files.split(","):
        knowledge_db.delete_file(file)

    doc_names = [doc_model.document_name for doc_model in knowledge_db.get_all_documents()]
    return knowledge_name, doc_names, len(doc_names)


def set_llm_prompt(prompt: str):
    global llm_prompt
    llm_prompt = prompt


def get_llm_prompt():
    global llm_prompt
    return llm_prompt


# 上传知识库
def file_upload(files,
                knowledge_db_name: str = 'test_poc',
                chunk_size: int = 750,
                chunk_overlap: int = 150
                ):
    save_file_path = "/tmp/document_files"
    knowledge_db_name = get_knowledge_ename(knowledge_db_name)
    # 指定保存文件的文件夹
    if not os.path.exists(save_file_path):
        os.makedirs(save_file_path)
    if files is None or len(files) == 0:
        print('no file need save')

    _, _, knowledge_db = get_knowledge_db(knowledge_db_name)

    # 注册文档处理器
    loader_mng = LoaderMng()
    # 加载文档加载器，可以使用mxrag自有的，也可以使用langchain的
    loader_mng.register_loader(loader_class=TextLoader, file_types=[".txt", ".md"])
    loader_mng.register_loader(loader_class=DocxLoader, file_types=[".docx"])
    loader_mng.register_loader(loader_class=PdfLoader, file_types=[".pdf"])
    loader_mng.register_loader(loader_class=ExcelLoader, file_types=[".xlsx", ".xls"])

    # 加载文档切分器，使用langchain的
    loader_mng.register_splitter(splitter_class=RecursiveCharacterTextSplitter,
                                 file_types=[".docx", ".txt", ".md", ".pdf", ".xlsx", ".xls"],
                                 splitter_params={"chunk_size": chunk_size,
                                                  "chunk_overlap": chunk_overlap,
                                                  "keep_separator": False
                                                  })
    for file in files:
        try:
            # 上传领域知识文档
            shutil.copy(file.name, save_file_path)
            # 知识库:chunk\embedding\add
            upload_files(knowledge_db, [file.name], loader_mng=loader_mng, embed_func=text_emb.embed_documents,
                         force=True)
            print(f"file {file.name} save to {save_file_path}.")
        except Exception as err:
            logger.error(f"save failed, find exception: {err}")


def file_change(files, upload_btn):
    print("file changes")


def get_db_file_names(knowledge_name: str):
    index_name = "./" + knowledge_name + "_faiss.index"
    db_name = "./" + knowledge_name + "_sql.db"
    return index_name, db_name


def get_knowledge_ename(knowledge_name: str):
    if knowledge_name is None or len(knowledge_name) == 0 or ' ' in knowledge_name:
        return 'test'
    else:
        return knowledge_name


# 历史问题改写
def generate_question(history, llm, history_n: int = 5):
    prompt = """现在你有一个上下文依赖问题补全任务，任务要求:请根据对话历史和用户当前的问句，重写问句。\n
    历史问题依次是:\n
    {}\n
    用户当前的问句:\n
    {}\n
    注意如果当前问题不依赖历史问题直接返回none即可\n
    请根据上述对话历史重写用户当前的问句,仅输出重写后的问句,不需要附加任何分析。\n
    重写问句: \n
    """
    if len(history) <= 2:
        return history
    cur_query = history[-1][0]
    history_qa = history[0:-1]
    history_list = [f"第{idx + 1}轮：{q_a[0]}" for idx, q_a in enumerate(history_qa) if q_a[0] is not None]
    history_list = history_list[:history_n]
    history_str = "\n\n".join(history_list)
    re_query = prompt.format(history_str, cur_query)
    new_query = llm.chat(query=re_query, llm_config=LLMParameterConfig(max_tokens=512,
                                                                       temperature=0.5,
                                                                       top_p=0.95))
    if new_query != "none":
        history[-1][0] = "原始问题: " + cur_query
        history += [[new_query, None]]
    return history


def merge_query_prompt_by_metadata(docs: List[Document], prompt: str):
    final_prompt = ""
    document_separator = "\n\n"
    if len(docs) != 0:
        last_doc = docs[-1]
        last_doc.metadata["answer"] = (last_doc.metadata["answer"]
                                       + f"{document_separator}{prompt}")
        docs[-1] = last_doc

        final_prompt = document_separator.join(x.metadata["answer"] for x in docs)

    return final_prompt


def merge_query_prompt_by_content(docs: List[Document], prompt: str):
    final_prompt = ""
    document_separator = "\n\n"
    if len(docs) != 0:
        last_doc = docs[-1]
        last_doc.page_content = (last_doc.page_content
                                 + f"{document_separator}{prompt}")
        docs[-1] = last_doc

        final_prompt = document_separator.join(x.page_content for x in docs)

    return final_prompt


def do_stream_query(q_with_prompt: str, llm, llm_config: LLMParameterConfig, question: str,
                    q_docs: List[Document] = None) -> Iterator[Dict]:
    logger.info("invoke stream query")
    resp = {"query": question, "result": ""}
    resp['source_documents'] = [{'metadata': x.metadata, 'page_content': x.page_content} for x in q_docs]

    for response in llm.chat_streamly(query=q_with_prompt, llm_config=llm_config):
        resp['result'] = response
        yield resp


# 聊天对话框
def bot_response(history,
                 history_r,
                 max_tokens: int = 512,
                 temperature: float = 0.5,
                 top_p: float = 0.95,
                 history_n: int = 5,
                 score_threshold: float = 0.5,
                 top_k: int = 1,
                 chat_type: str = "RAG检索增强对话",
                 show_type: str = "不显示",
                 is_rewrite: str = "否",
                 knowledge_name: str = 'test_poc'
                 ):
    chat_type_mapping = {"RAG检索增强对话": 1,
                         "仅大模型对话": 0}
    show_type_mapping = {"对话结束后显示": 1,
                         "检索框单独显示": 2,
                         "不显示": 0}
    is_rewrite_mapping = {"是": 1,
                          "否": 0}
    # 初始化检索器
    knowledge_name = get_knowledge_ename(knowledge_name)
    dense_retriever = creat_dense_retriever(knowledge_name, top_k, score_threshold)
    sparse_retriever = creat_sparse_retriever(knowledge_name, top_k)

    # 历史问题改写
    if is_rewrite_mapping.get(is_rewrite) == 1:
        history = generate_question(history, llm, history_n)
    history[-1][1] = '推理错误'
    try:
        # 仅使用大模型回答
        if chat_type_mapping.get(chat_type) == 0:
            response = llm.chat_streamly(query=history[-1][0],
                                         llm_config=LLMParameterConfig(max_tokens=max_tokens,
                                                                       temperature=temperature,
                                                                       top_p=top_p))
            # 返回迭代器
            for res in response:
                history[-1][1] = res
                yield history, history_r
        # 使用RAG增强回答
        elif chat_type_mapping.get(chat_type) == 1:
            hybrid_retriever = EnsembleRetriever(
                retrievers=[dense_retriever, sparse_retriever], weights=[0.7, 0.3]
            )
            q_docs = hybrid_retriever.invoke(history[-1][0])
            if reranker is not None:
                score = reranker.rerank(history[-1][0], [doc.page_content for doc in q_docs])
                q_docs = reranker.rerank_top_k(q_docs, score)

            prompt = PromptTemplate.from_template(llm_prompt)

            query = prompt.format(context="\n\n".join(doc.page_content for doc in q_docs), question=history[-1][0])

            response = do_stream_query(query, llm, q_docs=q_docs, question=history[-1][0],
                                       llm_config=LLMParameterConfig(max_tokens=max_tokens,
                                                                     temperature=temperature,
                                                                     top_p=top_p,
                                                                     stream=True))

            # 不展示检索内容
            if show_type_mapping.get(show_type) == 0:
                for res in response:
                    history[-1][1] = '推理错误' if res['result'] is None else res['result'].replace("<", "&lt").replace(
                        ">", "&gt")
                    yield history, history_r
            # 问答结尾展示
            elif show_type_mapping.get(show_type) == 1:
                for res in response:
                    history[-1][1] = '推理错误' if res['result'] is None else res['result'].replace("<", "&lt").replace(
                        ">", "&gt")
                    q_docs = res['source_documents']
                    yield history, history_r
                # 有检索到信息
                if len(q_docs) > 0:
                    history_last = ''
                    for i, source in enumerate(q_docs):
                        sources = "\n====检索信息来源:" + str(i + 1) + "[数据库名]:" + str(knowledge_name) + \
                                  "[文件名]:" + source['metadata']['source'] + "====" + "\n" + \
                                  "参考内容：" + source['page_content'] + "\n"
                        history_last += sources
                    history += [[None, history_last]]
                yield history, history_r
            # 检索窗口展示
            else:
                for res in response:
                    history[-1][1] = '推理错误' if res['result'] is None else res['result'].replace("<", "&lt").replace(
                        ">", "&gt")
                    q_docs = res['source_documents']
                    yield history, history_r
                # 有检索到信息
                if len(q_docs) > 0:
                    history_r_last = ''
                    for i, source in enumerate(q_docs):
                        sources = "\n====检索信息来源:" + str(i + 1) + "[数据库名]:" + str(knowledge_name) + \
                                  "[文件名]:" + source['metadata']['source'] + "====" + "\n" + \
                                  "参考内容：" + source['page_content'] + "\n"
                        history_r_last += sources
                    history_r += [[history[-1][0], history_r_last]]
                yield history, history_r
    except Exception as err:
        logger.error(f"query failed, find exception: {err}")
        yield history, history_r


# 检索对话框
def re_response(history_r,
                score_threshold: float = 0.5,
                top_k: int = 1,
                knowledge_name: str = 'test_poc'
                ):
    # 初始化检索器
    knowledge_name = get_knowledge_ename(knowledge_name)
    retriever_cls = creat_dense_retriever(knowledge_name, top_k, score_threshold)
    q_docs = retriever_cls.invoke(history_r[-1][0])
    if len(q_docs) > 0:
        history_r_last = ''
        for i, source in enumerate(q_docs):
            sources = "\n====检索信息来源:" + str(i + 1) + "[数据库名]:" + str(knowledge_name) + \
                      "[文件名]:" + source.metadata['source'] + "====" + "\n" + \
                      "参考内容：" + source.page_content + "\n"
            history_r_last += sources
        history_r[-1][1] = history_r_last
    else:
        history_r[-1][1] = "未检索到相关信息"
    return history_r


# 检索信息
def user_retriever(user_message, history_r):
    return "", history_r + [[user_message, None]]


# 聊天信息
def user_query(user_message, history):
    return "", history + [[user_message, None]]


def clear_history(history):
    return []


if __name__ == '__main__':
    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
        def _get_default_metavar_for_optional(self, action):
            return action.type.__name__

        def _get_default_metavar_for_positional(self, action):
            return action.type.__name__


    parse = argparse.ArgumentParser(formatter_class=CustomFormatter)
    parse.add_argument("--embedding_path", type=str, default="/home/data/acge_text_embedding",
                       help="embedding模型本地路径")
    parse.add_argument("--tei_emb", type=bool, default=False, help="是否使用TEI服务化的embedding模型")
    parse.add_argument("--embedding_url", type=str, default="http://127.0.0.1:8080/embed",
                       help="使用TEI服务化的embedding模型url地址")
    parse.add_argument("--embedding_dim", type=int, default=1024, help="embedding模型向量维度")
    parse.add_argument("--llm_url", type=str, default="http://127.0.0.1:1025/v1/chat/completions",
                       help="大模型url地址")
    parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat", help="大模型名称")
    parse.add_argument("--tei_reranker", type=bool, default=False, help="是否使用TEI服务化的reranker模型")
    parse.add_argument("--reranker_path", type=str, default=None, help="reranker模型本地路径")
    parse.add_argument("--reranker_url", type=str, default=None, help="使用TEI服务化的embedding模型url地址")
    parse.add_argument("--dev", type=int, default=0, help="使用的npu卡，可通过执行npu-smi info获取")
    parse.add_argument("--port", type=int, default=8080, help="web后端端口")
    parse.add_argument("--milvus_url", type=str, default="http://127.0.0.1:19530", help="milvus url地址")

    args = parse.parse_args().__dict__
    embedding_path: str = args.pop('embedding_path')
    tei_emb: bool = args.pop('tei_emb')
    embedding_url: str = args.pop('embedding_url')
    embedding_dim: int = args.pop('embedding_dim')
    llm_url: str = args.pop('llm_url')
    model_name: str = args.pop('model_name')
    tei_reranker: bool = args.pop('tei_reranker')
    reranker_path: str = args.pop('reranker_path')
    reranker_url: str = args.pop('reranker_url')
    dev: int = args.pop('dev')
    port: int = args.pop('port')

    os.environ["milvus_url"] = args.pop("milvus_url")
    os.environ["embedding_dim"] = str(embedding_dim)

    # 初始化test数据库
    knowledge_db = get_knowledge_db('test_poc')
    # 配置text生成text大模型chain，具体ip端口请根据实际情况适配修改
    llm = Text2TextLLM(base_url=llm_url, model_name=model_name, client_param=ClientParam(use_http=True))
    # 配置embedding模型，请根据模型具体路径适配
    if tei_emb:
        text_emb = TEIEmbedding(url=embedding_url, client_param=ClientParam(use_http=True))
    else:
        text_emb = TextEmbedding(model_path=embedding_path, dev_id=dev)
    # 配置reranker,请根据模型具体路径适配
    if tei_reranker:
        reranker = TEIReranker(url=reranker_url, client_param=ClientParam(use_http=True))
    elif reranker_path is not None:
        reranker = LocalReranker(model_path=reranker_path, dev_id=dev, k=3)
    else:
        reranker = None


    # 构建gradio框架
    def build_demo():
        with (gr.Blocks() as demo):
            gr.HTML("<center><h1>检索增强生成(RAG)对话</h1><p>powered by MindX RAG</p><center>")
            with gr.Row():
                with gr.Column(scale=100):
                    with gr.Row():
                        files = gr.components.File(
                            height=100,
                            file_count="multiple",
                            file_types=[".docx", ".txt", ".md", ".pdf", ".xlsx", ".xls"],
                            interactive=True,
                            label="上传知识库文档"
                        )
                    with gr.Row():
                        upload_btn = gr.Button("上传文件")
                    with gr.Row():
                        with gr.TabItem("知识库情况"):
                            knowledge_names, knowledge_name_num = get_knowledge_info()
                            set_knowledge_name = gr.Textbox(label='设置当前知识库',
                                                            value=knowledge_names[0],
                                                            placeholder="在此输入知识库名称,默认使用test知识库")
                            with gr.Row():
                                creat_knowledge_btn = gr.Button('创建知识库')
                                delete_knowledge_btn = gr.Button('删除知识库')

                            knowledge_name_output = gr.Textbox(label='知识库列表', value=knowledge_names)
                            knowledge_number_output = gr.Textbox(label='知识库数量', value=knowledge_name_num)
                            with gr.Row():
                                show_knowledge_btn = gr.Button('显示知识库')
                        with gr.TabItem("文件情况"):
                            knowledge_names, knowledge_name_num = get_knowledge_info()
                            knowledge_name = gr.Textbox(label='知识库名称', value=knowledge_names[0])
                            knowledge_file_output = gr.Textbox(label='知识库文件列表')
                            knowledge_file_num_output = gr.Textbox(label='知识库文件数量')
                            delete_knowledge_files = gr.Textbox(label='待删除知识库中的文件,使用逗号分隔', value="")
                            with gr.Row():
                                knowledge_file_out_btn = gr.Button('显示文件情况')
                                knowledge_file_delete_btn = gr.Button('删除指定文件')
                                knowledge_clear_btn = gr.Button('清空知识库')
                    with gr.Row():
                        with gr.TabItem("设置提示词"):
                            new_llm_prompt = gr.Textbox(label="提示词", value=default_prompt)
                            with gr.Row():
                                set_llm_prompt_btn = gr.Button('设置提示词')

                    with gr.Row():
                        with gr.Accordion(label='文档切分参数设置', open=False):
                            chunk_size = gr.Slider(
                                minimum=50,
                                maximum=5000,
                                value=750,
                                step=50,
                                interactive=True,
                                label="chunk_size",
                                info="文本切分长度"
                            )
                            chunk_overlap = gr.Slider(
                                minimum=10,
                                maximum=500,
                                value=150,
                                step=10,
                                interactive=True,
                                label="chunk_overlap",
                                info="文本切分填充长度"
                            )
                    with gr.Row():
                        with gr.Accordion(label='大模型参数设置', open=False):
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
                            is_rewrite = gr.Radio(['是', '否'], value="否", label="是否根据历史提问重写问题？")
                            history_n = gr.Slider(
                                minimum=1,
                                maximum=10,
                                value=5,
                                step=1,
                                interactive=True,
                                label="历史提问重写轮数",
                                info="问题重写时所参考的历史提问轮数"
                            )
                    with gr.Row():
                        with gr.Accordion(label='检索参数设置', open=False):
                            score_threshold = gr.Slider(
                                minimum=0,
                                maximum=1,
                                value=0.5,
                                step=0.01,
                                interactive=True,
                                label="score_threshold",
                                info="相似性检索阈值,值越大表示越相关,低于阈值不会被返回。"
                            )
                            top_k = gr.Slider(
                                minimum=1,
                                maximum=10,
                                value=3,
                                step=1,
                                interactive=True,
                                label="top_k",
                                info="相似性检索返回条数"
                            )
                            show_type = gr.Radio(['对话结束后显示', '检索框单独显示', '不显示'], value="对话结束后显示",
                                                 label="知识库文档匹配结果展示方式选择")
                with gr.Column(scale=200):
                    with gr.Tabs():
                        with gr.TabItem("对话窗口"):
                            chat_type = gr.Radio(['RAG检索增强对话', '仅大模型对话'], value="RAG检索增强对话",
                                                 label="请选择对话模式？")
                            chatbot = gr.Chatbot(height=550)
                            with gr.Row():
                                msg = gr.Textbox(placeholder="在此输入问题...", container=False)
                            with gr.Row():
                                send_btn = gr.Button(value="发送", variant="primary")
                                clean_btn = gr.Button(value="清空历史")
                        with gr.TabItem("检索窗口"):
                            chatbot_r = gr.Chatbot(height=550)
                            with gr.Row():
                                msg_r = gr.Textbox(placeholder="在此输入问题...", container=False)
                            with gr.Row():
                                send_btn_r = gr.Button(value="文档检索", variant="primary")
                                clean_btn_r = gr.Button(value="清空历史")
                # RAG发送
                send_btn.click(user_query, [msg, chatbot], [msg, chatbot], queue=False
                               ).then(bot_response,
                                      [chatbot, chatbot_r, max_tokens, temperature, top_p, history_n, score_threshold,
                                       top_k, chat_type, show_type, is_rewrite, set_knowledge_name],
                                      [chatbot, chatbot_r])
                # RAG清除历史
                clean_btn.click(clear_history, chatbot, chatbot)
                # 上传文件
                files.change(file_change, [], [])
                upload_btn.click(file_upload, [files, set_knowledge_name, chunk_size, chunk_overlap], files)
                # 管理所有知识库
                creat_knowledge_btn.click(get_knowledge_db, [set_knowledge_name], []).then(get_knowledge_info, [],
                                                                                           [knowledge_name_output,
                                                                                            knowledge_number_output])
                # 设置大模型提示词
                set_llm_prompt_btn.click(set_llm_prompt, [new_llm_prompt], [])

                show_knowledge_btn.click(get_knowledge_info, [], [knowledge_name_output, knowledge_number_output])
                delete_knowledge_btn.click(delete_knowledge_db, [set_knowledge_name],
                                           [knowledge_name_output, knowledge_number_output])
                # 管理知识库里文件
                knowledge_file_out_btn.click(get_document, [set_knowledge_name],
                                             [knowledge_name, knowledge_file_output, knowledge_file_num_output])
                knowledge_clear_btn.click(clear_file_in_kg, [set_knowledge_name],
                                          [knowledge_name, knowledge_file_output, knowledge_file_num_output])

                knowledge_file_delete_btn.click(delete_document_in_kg, [knowledge_name, delete_knowledge_files],
                                                [knowledge_name, knowledge_file_output, knowledge_file_num_output])
                # 检索发送
                send_btn_r.click(user_retriever, [msg_r, chatbot_r], [msg_r, chatbot_r], queue=False
                                 ).then(re_response, [chatbot_r, score_threshold, top_k, set_knowledge_name], chatbot_r)
                # 检索清除历史
                clean_btn_r.click(clear_history, chatbot_r, chatbot_r)
        return demo


    def create_gradio(ports):
        demo = build_demo()
        demo.queue()
        demo.launch(share=True, server_name="127.0.0.1", server_port=ports)


    # 启动gradio
    create_gradio(port)
