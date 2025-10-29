import os
import shutil
from pathlib import Path

import sys
import httpx
from langchain_openai import ChatOpenAI
from loguru import logger
from openai import OpenAI

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from mx_rag.document import LoaderMng
from mx_rag.document.loader import DocxLoader, PdfLoader
from mx_rag.embedding.service import TEIEmbedding
from mx_rag.knowledge import KnowledgeStore, KnowledgeDB
# from mx_rag.reranker.local import MixRetrieveReranker
from mx_rag.reranker.service import TEIReranker
from mx_rag.retrievers import Retriever, FullTextRetriever
from mx_rag.storage.document_store import MilvusDocstore
from mx_rag.storage.vectorstore import MilvusDB
from mx_rag.utils import ClientParam
from pymilvus import MilvusClient

import streamlit as st

sys.tracebacklimit = 1000

user_id = "7d1d04c1-dd5f-43f8-bad5-99795f24bce6"

default_prompt = """<指令>以下是提供的背景知识，请简洁和专业地回答用户的问题。如果无法从已知信息中得到答案，请根据自身经验做出回答。<指令>\n背景知识：{context}\n用户问题：{question}"""


def refresh_chat():
    print_history_message()


# clear 按钮
def on_btn_click():
    del st.session_state['messages']


knowledge_store = KnowledgeStore(db_path="./knowledge_store_sql.db")

KnowledgeDB_Map = {}


def query_knowledge(knowledge_name):
    return get_document(knowledge_name)[1]


# 删除知识库中的文件
def delete_document_in_knowledge(knowledge_name: str):
    file_names = st.session_state.file_to_delete
    _, _, knowledge_db = get_knowledge_db(knowledge_name)
    upload_file_dir = get_knowledge_dir(knowledge_name)
    try:
        for file_name in file_names.split(","):
            knowledge_db.delete_file(file_name)

            # 删除web上传时存放的文件
            os.remove(os.path.join(upload_file_dir, file_name))

    except Exception as e:
        logger.error(f"delete file [{file_names}] failed: {e}")


def get_knowledge_dir(knowledge_name):
    return "./" + knowledge_name + "_data"


def get_knowledge_name(knowledge_name: str):
    if knowledge_name is None or len(knowledge_name) == 0 or ' ' in knowledge_name:
        return 'test'
    else:
        return knowledge_name


def get_embedding():
    # 初始化embedding客户端对象
    return TEIEmbedding(url=st.session_state["embedding_url"], client_param=ClientParam(use_http=True))


# 获取向量数据库对象
def get_vector_store(knowledge_name: str):
    # 初始化向量数据库
    knowledge_name = get_knowledge_name(knowledge_name)
    milvus_client = MilvusClient(st.session_state["milvus_url"])
    return MilvusDB.create(client=milvus_client, x_dim=int(st.session_state["embedding_dim"]),
                           collection_name=f"{knowledge_name}_vector")


# 获取文本数据库对象
def get_chunk_store(knowledge_name: str):
    knowledge_name = get_knowledge_name(knowledge_name)
    milvus_client = MilvusClient(st.session_state["milvus_url"])
    return MilvusDocstore(milvus_client, collection_name=f"{knowledge_name}_chunk")


# 创建新的知识库
def get_knowledge_db(knowledge_name: str):
    knowledge_name = get_knowledge_name(knowledge_name)
    if knowledge_name in KnowledgeDB_Map.keys():
        return KnowledgeDB_Map["knowledge_name"][2]
    logger.info(f"get knowledge_name:{knowledge_name}")

    # 初始化向量数据库
    vector_store = get_vector_store(knowledge_name)
    # 初始化文档chunk关系数据库
    chunk_store = get_chunk_store(knowledge_name)

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


# 获取知识库中文档列表
def get_document(knowledge_name: str):
    knowledge_db = get_knowledge_db(knowledge_name)[2]
    doc_names = [doc_model.document_name for doc_model in knowledge_db.get_all_documents()]
    return knowledge_name, doc_names, len(doc_names)


# 清空知识库中文档列表
def clear_knowledge(knowledge_name: str):
    logger.info(f"start to delete all files")
    knowledge_name = get_knowledge_name(knowledge_name)
    vector_store, chunk_store, knowledge_db = get_knowledge_db(knowledge_name)
    knowledge_db.delete_all()

    upload_file_dir = get_knowledge_dir(knowledge_name)
    # 删除从文件解析出来的图片
    try:
        shutil.rmtree(upload_file_dir)
    except Exception as e:
        logger.info(f"-------- delete {upload_file_dir} failed: {e}")


def upload_file(knowledge_name: str, file):
    logger.info(f"start to upload file: {file}")

    upload_file_dir = get_knowledge_dir(knowledge_name)

    if not os.path.exists(upload_file_dir):
        os.makedirs(upload_file_dir)

    # Construct the full path for the saved file
    file_path = os.path.join(upload_file_dir, file.name)

    # Write the file content to disk in binary write mode
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())

    file_obj = Path(file_path)

    # 根据文类型，获取loader类和splitter类信息
    loader_info, splitter_info = get_document_loader_splitter(file_obj.suffix)

    # 获取embedding对象
    emb = get_embedding()
    # 获取知识库管理对象
    knowledge_db = get_knowledge_db(knowledge_name)[2]

    file_base_name = os.path.basename(file_path)

    # 检查当前文件是否已经入过库
    if knowledge_db.check_document_exist(file_base_name):
        logger.warning(f"file {file_base_name} exists in knowledge db")
        return

    # 创建文件解析器和切分器
    loader = loader_info.loader_class(file_path=file_obj.as_posix(), **loader_info.loader_params)
    splitter = splitter_info.splitter_class(**splitter_info.splitter_params)
    # 解析文件并切分
    docs = loader.load_and_split(splitter)

    # 获取文档片段chunk内容和元数据信息
    texts = [doc.page_content for doc in docs if doc.page_content]
    meta_data = [doc.metadata for doc in docs]

    # 存储到文本、向量数据库中
    knowledge_db.add_file(file_obj, texts, {"dense": emb.embed_documents}, meta_data)

    logger.info(f"upload file {file.name} to knowledge successfully")


def file_upload(knowledge_name: str):
    if st.session_state.new_file is None:
        return
    upload_file(knowledge_name, st.session_state.new_file)

    print_history_message()


def create_new_db():
    get_knowledge_db(st.session_state.knowledge_name)

    print_history_message()


# 创建llm_chain 客户端
def create_llm_chain(base_url, model_name):
    http_client = httpx.Client()
    root_client = OpenAI(
        base_url=base_url,
        api_key='sk-1234',
        http_client=http_client
    )

    client = root_client.chat.completions

    llm = ChatOpenAI(
        api_key="sk_fake",
        client=client,
        model=model_name,
        temperature=st.session_state.temperature,
        streaming=True,
    )

    return llm


# 获取文档加载器，和切分器
def get_document_loader_splitter(file_suffix):
    # 初始化文档加载切分管理器
    loader_mng = LoaderMng()

    # 注册文档加载器，可以使用mxrag提供的，也可以使用langchain提供的，同时也可实现langchain_community.document_loaders.base.BaseLoader
    # 接口类自定义实现文档解析功能
    loader_mng.register_loader(loader_class=TextLoader, file_types=[".txt", ".md"])
    loader_mng.register_loader(loader_class=DocxLoader, file_types=[".docx"])
    loader_mng.register_loader(loader_class=PdfLoader, file_types=[".pdf"])
    # 注册文档切分器，可自定义实现langchain_text_splitters.base.TextSplitter基类对文档进行切分
    loader_mng.register_splitter(splitter_class=RecursiveCharacterTextSplitter,
                                 file_types=[".docx", ".txt", ".md", ".pdf"],
                                 splitter_params={"chunk_size": 750,
                                                  "chunk_overlap": 150,
                                                  "keep_separator": False
                                                  }
                                 )

    # 根据文件后缀获取对应的文件解析器信息，包含解析类，及参数
    loader_info = loader_mng.get_loader(file_suffix)
    # 根据文件后缀获取对应的文件切分器信息，包含切分类，及参数
    splitter_info = loader_mng.get_splitter(file_suffix)

    return loader_info, splitter_info


# 根据问题从数据库中检索相似片段
def retrieve_similarity_docs(knowledge_name: str, query, top_k, score_threshold):
    knowledge_name = get_knowledge_name(knowledge_name)
    # 获取embedding对象
    emb = get_embedding()
    # 获取文本和向量数据库对象
    chunk_store = get_chunk_store(knowledge_name)
    vector_store = get_vector_store(knowledge_name)

    # 配置向量检索器，
    dense_retriever = Retriever(vector_store=vector_store,
                                document_store=chunk_store,
                                embed_func=emb.embed_documents,
                                k=top_k,
                                score_threshold=score_threshold
                                )

    # 调用检索器从向量数据库中查找出和query最相近的tok个文档chunk
    dense_res = dense_retriever.invoke(query)

    # 配置全文检索器，其实现原理为BM25检索
    full_text_retriever = FullTextRetriever(document_store=chunk_store, k=top_k)

    full_text_res = full_text_retriever.invoke(query)

    # mix_reranker = MixRetrieveReranker(k=top_k)

    # 对bm25和稠密向量两路检索进行融合排序
    # docs = mix_reranker.rerank(query, dense_res + full_text_res)

    logger.info(f"retrieve similarity chunks from knowledge successfully")
    return dense_res + full_text_res


# 检查会话状态中是否存在 messages 列表，如果不存在，则初始化为空列表
# 用于存储交流过程中的消息
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    st.title("Chat with Mind RAG SDK")  # 显示聊天界面的标题


def print_history_message():
    st.title("Chat with Mind RAG SDK")  # 显示聊天界面的标题
    # 遍历保存在会话状态中的消息，并根据消息类型（人类或AI）分别显示
    for message in st.session_state["messages"]:
        if message["type"] == "human":  # 这里不应该用 system message
            with st.chat_message("user"):  # 不用 container; user
                st.markdown(message["content"])
        elif message["type"] == "ai":
            with st.chat_message("assistant"):  # 不用 container；assistant
                st.markdown(message["content"])
            with st.expander("背景知识"):
                for i, context in enumerate(message.get("contexts", [])):
                    st.markdown(f"-----------------context {i}----------------------")
                    st.markdown(context)


def generate_question(query, llm):
    prompt = """现在你有一个上下文依赖问题补全任务，任务要求:请根据对话历史和用户当前的问句，重写问句。\n
    历史问题依次是:\n
    {}\n
    注意如果当前问题不依赖历史问题直接返回none即可\n
    请根据上述对话历史重写用户当前的问句,仅输出重写后的问句,不需要附加任何分析。\n
    重写问句: \n
    """
    if len(st.session_state["messages"]) <= 2:
        return query

    history_n = st.session_state["history_n"]
    messages = st.session_state["messages"]
    history_list = [f"第{idx + 1}轮：{message['content']}"
                    for idx, message in enumerate(messages[len(messages) - history_n:]) if message['type'] == "human"]

    history_str = "\n\n".join(history_list)
    re_query = prompt.format(history_str)

    invoke_message = [
        {"role": "system", "content": re_query},
        {"role": "user", "content": query}
    ]

    logger.info(f"======================改写前问题：{query}")

    try:
        new_query = ""
        for chunk in llm.stream(invoke_message):
            new_query += chunk.content

        if new_query == "":
            query = new_query
        else:
            pos = new_query.rfind("</think>")
            pos += len("</think>")
            query = new_query[pos:].strip()
    except Exception as e:
        logger.error(f"call llm invoke failed:{e}")

    logger.info(f"======================改写后问题：{query}")
    return query


def generate_text_answer(query, q_docs, llm_chain):
    context = "\n".join([text.page_content for text in q_docs])
    llm_prompt = st.session_state["text_prompt"].format(context=context, question=query)
    # 构造请求消息
    messages = [
        {"role": "system", "content": "你是一个专业的知识问答助手"},
        {"role": "user", "content": llm_prompt}
    ]

    return llm_chain.stream(messages)


def answer_without_knowledge(llm_chain, query):
    # 构造请求消息
    messages = [
        {"role": "system", "content": "你是一个专业的知识问答助手"},
        {"role": "user", "content": query}
    ]

    with st.chat_message("user"):  # 不用 container; user
        st.markdown(query)

    placeholder = st.empty()
    full_answer = ""
    for chunk in llm_chain.stream(messages):
        content = chunk.content.strip()
        full_answer += content
        placeholder.markdown(full_answer)

    placeholder.empty()
    with st.chat_message("ai"):  # 不用 container; user
        st.markdown(full_answer)

    st.session_state["messages"].append({'content': full_answer, 'type': "ai"})  # 保存ai msg


def answer_with_knowledge(llm_chain, query):
    q_docs = retrieve_similarity_docs(st.session_state.knowledge_name, query, st.session_state.top_k,
                                      st.session_state.similarity_threshold)

    text_reranker = TEIReranker(url=st.session_state["reranker_url"], k=st.session_state.top_k,
                                client_param=ClientParam(use_http=True))

    if text_reranker is not None and len(q_docs) > 0:
        score = text_reranker.rerank(query, [doc.page_content for doc in q_docs])
        q_docs = text_reranker.rerank_top_k(q_docs, score)

    full_answer = ""
    with st.chat_message("user"):  # 不用 container; user
        st.markdown(query)

    placeholder = st.empty()

    answer = generate_text_answer(query, q_docs, llm_chain)
    # 流式显示
    for chunk in answer:
        content = chunk.content.strip()
        full_answer += content
        placeholder.markdown(full_answer)

    # 删除临时流式结果
    placeholder.empty()
    with st.chat_message("ai"):
        st.markdown(full_answer)

    # 存储到历史消息中
    contexts = q_docs
    st.session_state["messages"].append({'content': full_answer, 'type': "ai",
                                         "contexts": contexts})  # 保存ai msg
    with st.expander("背景知识"):
        for i, context in enumerate(contexts):
            st.markdown(f"-----------------context {i}----------------------")
            st.markdown(context)


# 用户查询处理
def deal_user_query():
    print_history_message()
    user_query = st.session_state["query"]

    # 配置大模型客户端对象
    llm_chain = create_llm_chain(base_url=st.session_state["llm_url"], model_name=st.session_state["llm_name"])

    if st.session_state.modify_query == "True":
        user_query = generate_question(user_query, llm_chain)

    st.session_state["messages"].append({'content': user_query, 'type': "human"})  # 保存human

    if st.session_state.use_knowledge == "False":
        answer_without_knowledge(llm_chain, user_query)
    else:
        answer_with_knowledge(llm_chain, user_query)


def set_service_para():
    with st.expander("服务参数配置"):
        llm_columns = st.columns([3, 2])
        emb_columns = st.columns([3, 2])
        reranker_columns = st.columns([3, 2])
        with llm_columns[0]:
            st.text_input("llm_base_url", "http://127.0.0.1:1025/v1", key="llm_url", help="llm服务基地址")
        with llm_columns[1]:
            st.text_input("llm模型名", "Llama3-8B-Chinese-Chat", key="llm_name", help="llm模型名")

        with emb_columns[0]:
            st.text_input("embedding url", "http://127.0.0.1:8085/embed", key="embedding_url", help="emb 服务地址")
        with emb_columns[1]:
            st.number_input("embedding dim", value=1024, key="embedding_dim", help="emb 向量维度")

        with reranker_columns[0]:
            st.text_input("reranker url", "http://127.0.0.1:8086/rerank", key="reranker_url",
                          help="reranker服务地址")
        with reranker_columns[1]:
            st.number_input("rerank_top_k", value=3, key="rerank_top_k", help="rerank_top_k值")

        st.text_input("milvus_url", "http://127.0.0.1:19530", key="milvus_url", help="milvus服务基地址")


def set_web():
    with st.sidebar:
        set_service_para()
        st.radio("是否使用外部知识库问答：", ["True", "False"], index=0, on_change=refresh_chat, key="use_knowledge")
        st.text_input("设置知识库名", "test", key="knowledge_name", on_change=create_new_db)

        cur_knowledge_name = st.session_state.get("knowledge_name", "test")
        st.file_uploader("上传知识文档", key="new_file", on_change=file_upload, args=(cur_knowledge_name,))
        st.text_input("待删除知识文档名", key="file_to_delete")
        st.button("删除知识库中文档", key="delete_document", help="删除知识库中的文档", type="primary",
                  on_click=delete_document_in_knowledge, args=(cur_knowledge_name,))

        st.button("清空知识库", key="clear_knowledge", help="删除知识库中的所有文档", type="primary",
                  on_click=clear_knowledge, args=(cur_knowledge_name,))

        st.text_area("知识库文件详情", value=query_knowledge(cur_knowledge_name))

        parse_image = st.radio("是否从文档中提取图片", ["True", "False"], index=0, help="调用vlm解析文档中的图片信息",
                               on_change=refresh_chat, key="parse_image")

        st.text_area("设置提示词", default_prompt, help="设置的提示词需包含{context}和{question}",
                     key="text_prompt")

        with st.expander("设置大模型对话参数"):
            st.slider("temperature", 0.1, 1.0, 0.95, step=0.1, on_change=refresh_chat, key="temperature")
            st.slider("top_p", 0.1, 1.0, 0.95, step=0.1, on_change=refresh_chat, key="top_p")
            st.slider("max_length", min_value=64, max_value=2048, step=128, value=1024,
                      key="max_length", on_change=refresh_chat, help="大模型输出的最大token数")

        with st.expander("设置检索参数"):
            st.slider('top_k', 1, 100, 3, step=1, key="top_k", on_change=refresh_chat,
                      help="最相似的k个知识片段")
            st.slider('similarity_threshold', 0.1, 1.0, 0.5, step=0.1, key="similarity_threshold",
                      on_change=refresh_chat,
                      help="值越大，越相似")

        st.radio("是否开启问题改写：", ["True", "False"], index=1,
                 help="开启问题改写，会根据历史问题进行改写当前问题，更准确理解当前问题语义", on_change=refresh_chat,
                 key="modify_query")
        st.slider('历史对话轮数', 1, 20, 3, step=1, key="history_n", help="改写问题时采纳的历史对话轮数")

        st.button("clear chat history", on_click=on_btn_click, type="primary")

    st.chat_input("请输入内容...", key="query", on_submit=deal_user_query)


if __name__ == "__main__":
    set_web()
