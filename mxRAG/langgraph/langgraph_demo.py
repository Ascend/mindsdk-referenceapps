import os
import time
from paddle.base import libpaddle
from loguru import logger
from typing import List, TypedDict, Any, Dict

from langchain_core.retrievers import BaseRetriever
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate


def evaluate_creator(evaluator, evaluate_type: str):
    language="chinese"

    # prompt_dir is ragas cache_dir will speed evaluate
    prompt_dir="/usr/local/lib/python3.11/dist-packages/mx_rag/evaluate/prompt"

    def evaluate_context_relevancy(state):
        question = state["question"]
        documents = state["documents"]

        datasets = {
            "question": [question] * len(documents),
            "contexts": [[doc] for doc in documents]
        }

        scores = evaluator.evaluate_scores(metrics_name=["context_relevancy"],
                                           datasets=datasets,
                                           is_async=False,
                                           language=language,
                                           prompt_dir=prompt_dir)
        return scores["context_relevancy"]
    
    if evaluate_type == "context_relevancy":
        return evaluate_context_relevancy
    
    def evaluate_generate_relevancy(state):
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]

        datasets = {
            "question": [question],
            "contexts": [[documents]],
            "answer": [generation]
        }

        scores = evaluator.evaluate_scores(metrics_name=["answer_relevancy", "faithfulness"],
                                           datasets=datasets,
                                           is_async=False,
                                           language=language,
                                           prompt_dir=prompt_dir)
        return scores["answer_relevancy"], scores["faithfulness"]
    
    if evaluate_type == "generate_relevancy":
        return evaluate_generate_relevancy
    
    raise KeyError("evaluate_type not support")

def cache_search(cache):
    def cache_search_process(state):
        logger.info("---QUERY SEARCH ---")
        question = state["question"]
        generation = cache.search(question)
        return {"question": question, "generation": generation}
    
    return cache_search_process


def cache_update(cache):
    def cache_update_process(state):
        logger.info("---QUERY UPDATE ---")
        question = state["question"]
        generation = state["generation"]

        cache.update(question, generation)

        return state
    
    return cache_update_process


def decide_to_decompose(state):
    logger.info("---DECIDE TO DECOMPOSE---")
    cache_generation = state["generation"]

    if cache_generation is None:
        logger.warning(
            "---DECISION: CACHE MISS GO DECOMPOSE---"
        )
        return "cache_miss"
    
    logger.info("---DECISION: CACHE HIT END---")
    return "cache_hit"


def decompose(llm):
    sub_question_key_words = "Q:"
    prompt = PromptTemplate(
        template="""
                    请你参考如下示例，拆分用户的问题为独立子问题，如果无法拆分则返回原始问题:
                    示例一:
                    用户问题: 今天的天气如何, 你今天过的怎么样?

                    {sub_question_key_words}今天的天气如何?
                    {sub_question_key_words}你今天过的怎么样?

                    示例二:
                    用户问题: 汉堡好吃吗?

                    {sub_question_key_words}汉堡好吃吗?

                    现在请你参考示例拆分以下用户问题:
                    用户的问题:{question}
                    """,
        input_variables=["question", "sub_question_key_words"]
    )

    sub_question_generator = LLMChain(llm=llm, prompt=prompt)

    def decompose_process(state):
        logger.info("---QUERY DECOMPOSITION ---")
        question = state["question"]

        sub_queries = sub_question_generator.predict(question=question, sub_question_key_words=sub_question_key_words)
        if sub_question_key_words not in sub_queries:
            sub_queries = None
        else:
            sub_queries = sub_queries.split(sub_question_key_words)
            sub_queries = sub_queries[1:]

        return {"sub_questions": sub_queries, "question": question}
    
    return decompose_process


def retrieve(retriever: BaseRetriever):
    def retrieve_process(state):
        logger.info("---RETRIEVE---")
        sub_questions = state["sub_questions"]
        question = state["question"]

        documents = []
        docs = []
        if sub_questions is None:
            docs = retriever.get_relevant_documents(question)
        else:
            for query in sub_questions:
                docs.extend(retriever.get_relevant_documents(query))
        
        for doc in docs:
            if doc.page_content not in documents:
                documents.append(doc.page_content)
        
        return {"documents": documents, "question": question}
    
    return retrieve_process


def rerank(reranker):
    def rerank_process(state):
        logger.info("---RERANK---")
        question = state["question"]
        documents = state["documents"]

        scores = reranker.rerank(query=question, texts=documents)
        documents = reranker.rerank_top_k(objs=documents, scores=scores)

        return {"documents": documents, "question": question}

    return rerank_process


def generate(llm):
    prompt = PromptTemplate(
        template="""{context}
                 
                 根据上述已知信息,简洁和专业的来回答用户问题。如果无法从中已知信息中得到答案，请根据自身经验做出回答

                 {question}
                 """,
        input_variables=["context", "question"]
    )

    rag_chain = LLMChain(llm=llm, prompt=prompt)

    def generate_process(state):
        logger.info("---GENERATE---")
        question = state["question"]
        documents = state["documents"]

        generation = rag_chain.predict(context=documents, question=question)
        return {"documents": documents, "question": question, "generation": generation}
    
    return generate_process


def grade_documents(evaluate, score_threshold: float = 0.3):
    evalutor = evaluate_creator(evaluate, "context_relevancy")

    def grade_documents_process(state):
        logger.info("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        question = state["question"]
        documents = state["documents"]

        scores = evalutor(state)

        filtered_docs = ""
        for i, score in enumerate(scores):
            if score >= score_threshold:
                logger.info(f"---RAGAS GRADE: DOCUMENT RELEVANT--- score:{score} score_threshold:{score_threshold}")
                filtered_docs = filtered_docs + "{}\n".format(documents[i])
            else:
                logger.warning(
                    f"---RAGAS GRADE: DOCUMENT NOT RELEVANT--- score:{score} score_threshold:{score_threshold}"
                )
                continue
        return {"documents": filtered_docs, "question": question}
    
    return grade_documents_process


def transform_query(llm):
    prompt = PromptTemplate(
        template="""
                 你是一个用户问题重写员, 请仔细理解用户问题的内容和语义和检索的文档，在不修改用户问题
                 语义的前提下，将用户问题重写为可以更好被矢量检索的形式

                 用户问题:{question}
                 """,
        input_variables=["question"]
    )

    question_rewriter = LLMChain(llm=llm, prompt=prompt)

    def transform_query_process(state):
        logger.info("---TRANSFORM QUERY---")
        question = state["question"]
        documents = state["documents"]

        better_question = question_rewriter.predict(question=question)

        return {"documents": documents, "question": better_question}
    
    return transform_query_process


def decide_to_generate(state):
    logger.info("---ASSESS GRADED DOCUMENTS---")
    filtered_documents = state["documents"]

    if not filtered_documents:
        logger.warning(
            "---DECISION:ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    logger.info("---DECISION: GENERATE---")
    return "generate"


def grade_generation_v_documents_and_question(evaluate,
                                              context_score_threshold: float = 0.6,
                                              answer_score_threshold: float = 0.6):
    generate_evalutor = evaluate_creator(evaluate, "generate_relevancy")

    def grade_generation_v_documents_and_question_process(state):
        logger.info("---CHECK HALLUCINATIONS---")

        answer_score, context_score = generate_evalutor(state)

        answer_score = answer_score[0]
        logger.info("---GRADE GENERATION vs QUESTION---")
        if answer_score < answer_score_threshold:
            logger.warning(f"---DECISION: GENERATION DOES NOT ADDRESS QUESTION,"
                           f" RE-TRY--- answer_score:{answer_score},"
                           f"answer_score_threshold:{answer_score_threshold}")
            return "not useful"
        
        logger.info(f"---DECISION: GENERATION ADDRESSES QUESTION--- "
                    f"answer_score:{answer_score},"
                    f"answer_score_threshold:{answer_score_threshold}")
        
        context_score = context_score[0]
        logger.info("---GRADE GENERATION vs DOCUMENTS---")
        if context_score < context_score_threshold:
            logger.warning(f"---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, "
                           f" RE-TRY--- context_score:{context_score},"
                           f"context_score_threshold:{context_score_threshold}")
            return "not useful"
        
        logger.info(f"---DECISION: GENERATION GROUNDED IN DOCUMENTS---"
                    f"context_score:{context_score},"
                    f"context_score_threshold:{context_score_threshold}")
        return "useful"
    
    return grade_generation_v_documents_and_question_process


def create_loader_and_spliter(mxrag_component: Dict[str, Any],
                              chunk_size:int = 200,
                              chunk_overlap:int = 50):
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    from mx_rag.knowledge.doc_loader_mng import LoaderMng
    from mx_rag.document.loader import DocxLoader

    loader_mng = LoaderMng()
    loader_mng.register_loader(DocxLoader, [".docx"])
    loader_mng.register_splitter(RecursiveCharacterTextSplitter, [".docx"],
                                 {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap, "keep_separator": False})
    mxrag_component["loader_mng"] = loader_mng


def create_remote_connector(mxrag_component: Dict[str, Any],
                            reranker_url: str,
                            embedding_url: str,
                            llm_url: str,
                            llm_model_name: str):
    from mx_rag.llm.text2text import Text2TextLLM
    from mx_rag.embedding import EmbeddingFactory
    from mx_rag.reranker.reranker_factory import RerankerFactory

    reranker = RerankerFactory.create_reranker(similarity_type="tei_reranker",
                                               url=reranker_url,
                                               use_http=True,
                                               k=3)
    mxrag_component['reranker_connector'] = reranker

    embedding = EmbeddingFactory.create_embedding(embedding_type="tei_embedding",
                                                  url=embedding_url,
                                                  use_http=True)
    mxrag_component['embedding_connector'] = embedding

    llm = Text2TextLLM(base_url=llm_url, model_name=llm_model_name,
                       use_http=True,
                       timeout=240,
                       max_tokens=4096)
    mxrag_component['llm_connector'] = llm


def create_knowledge_storage(mxrag_component: Dict[str, Any], knowledge_files: List[str]):
    from mx_rag.knowledge.knowledge import KnowledgeStore
    from mx_rag.knowledge import KnowledgeDB
    from mx_rag.knowledge.handler import upload_files
    from mx_rag.storage.vectorstore import MindFAISS, SimilarityStrategy
    from mx_rag.storage.document_store import SQLiteDocstore

    npu_dev_id = 1
    
    # faiss_index_save_file is your faiss index save dir
    faiss_index_save_file:str = "/usr/local/Ascend/mx_rag/rag_npu_faiss.index"
    vector_store = MindFAISS(x_dim=1024,
                             similarity_strategy=SimilarityStrategy.FLAT_L2,
                             devs=[npu_dev_id],
                             load_local_index=faiss_index_save_file)
    mxrag_component["vector_store"] = vector_store


    # sqlite_save_file is your sqlite save dir
    sqlite_save_file:str = "/usr/local/Ascend/mx_rag/rag_sql.db"
    chunk_store = SQLiteDocstore(db_path=sqlite_save_file)
    mxrag_component["chunk_store"] = chunk_store

    # your knowledge file white paths if docx not in white paths will raise exception
    white_paths=["/usr/local/Ascend/mx_rag/knowledge"]
    knowledge_store = KnowledgeStore(db_path=sqlite_save_file)
    Knowledge_db = KnowledgeDB(knowledge_store=knowledge_store, chunk_store=chunk_store, vector_store=vector_store,
                               knowledge_name="rag", white_paths=white_paths)
    
    upload_files(Knowledge_db, knowledge_files, loader_mng=mxrag_component.get("loader_mng"),
                 embed_func=mxrag_component.get("embedding_connector").embed_documents,
                 force=True)
    

def create_hybrid_search_retriever(mxrag_component: Dict[str, Any]):
    from langchain.retrievers import EnsembleRetriever

    from mx_rag.retrievers.retriever import Retriever
    from mx_rag.retrievers import BMRetriever

    chunk_store = mxrag_component.get("chunk_store")
    vector_store = mxrag_component.get("vector_store")
    embedding = mxrag_component.get("embedding_connector")

    npu_faiss_retriever = Retriever(vector_store=vector_store, document_store=chunk_store,
                                    embed_func=embedding.embed_documents, k=10, score_threshold=0.4)

    hybrid_retriever = EnsembleRetriever(
        retrievers=[npu_faiss_retriever], weights=[1.0]
    )

    mxrag_component["retriever"] = hybrid_retriever


def create_cache(mxrag_component: Dict[str, Any],
                 reranker_url: str,
                 embedding_url: str):
    from mx_rag.cache import SimilarityCacheConfig
    from mx_rag.cache import EvictPolicy
    from mx_rag.cache import MxRAGCache

    npu_dev_id = 1
    # data_save_folder is your cache file when you next run your rag applicate it will read form disk
    cache_data_save_folder = "/usr/local/Ascend/mx_rag/cache_save_folder/"

    similarity_config = SimilarityCacheConfig(
        vector_config={
            "vector_type": "npu_faiss_db",
            "x_dim": 1024,
            "devs": [npu_dev_id],
            "index_type": "FLAT:L2"
        },
        cache_config="sqlite",
        emb_config={
            "embedding_type": "tei_embedding",
            "url": embedding_url,
            "use_http": True
        },
        similarity_config={
            "similarity_type": "tei_reranker",
            "url": reranker_url,
            "use_http": True
        },
        retrieval_top_k=3,
        cache_size=100,
        auto_flush=100,
        similarity_threshold=0.70,
        data_save_folder=cache_data_save_folder,
        disable_report=True,
        eviction_policy=EvictPolicy.LRU
    )

    similarity_cache = MxRAGCache("similarity_cache", similarity_config)
    mxrag_component["cache"] = similarity_cache

def create_evaluate(mxrag_component):
    from mx_rag.evaluate import Evaluate

    llm = mxrag_component.get("llm_connector")
    embedding = mxrag_component.get("embedding_connector")
    mxrag_component["evaluator"] = Evaluate(llm=llm, embedding=embedding)


def build_mxrag_application(mxrag_component):
    from langgraph.graph import END, START, StateGraph

    class GraphState(TypedDict):
        question: str
        sub_questions: List[str]
        generation: str
        documents: List[str]

    llm = mxrag_component.get("llm_connector")
    retriever = mxrag_component.get("retriever")
    reranker = mxrag_component.get("reranker_connector")
    cache = mxrag_component.get("cache")
    evaluate = mxrag_component.get("evaluator")

    workflow = StateGraph(GraphState)
    workflow.add_node("cache_search", cache_search(cache))
    workflow.add_node("cache_update", cache_update(cache))
    workflow.add_node("decompose", decompose(llm))
    workflow.add_node("retrieve", retrieve(retriever))
    workflow.add_node("rerank", rerank(reranker))
    workflow.add_node("grade_documents", grade_documents(evaluate))
    workflow.add_node("generate", generate(llm))
    workflow.add_node("transform_query", transform_query(llm))

    workflow.add_edge(START, "cache_search")

    workflow.add_conditional_edges(
        "cache_search",
        decide_to_decompose,
        {
            "cache_hit": END,
            "cache_miss": "decompose",
        },
    )

    workflow.add_edge("decompose", "retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "grade_documents")

    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        }
    )

    workflow.add_edge("transform_query", "cache_search")
    workflow.add_conditional_edges(
        "generate",
        grade_generation_v_documents_and_question(evaluate),
        {
            "useful": "cache_update",
            "not useful": "transform_query"
        },
    )

    workflow.add_edge("cache_update", END)  
    app = workflow.compile()
    return app


if __name__ == "__main__":
    mxrag_component: Dict[str, Any] = {}

    # nim tei rerank
    nim_tei_reranker_url = "http://ip:port/rerank"
    # nim tei embed
    nim_tei_embedding_url = "http://ip:port/embed"

    # mind-ie llm server
    llm_url = "http://ip:port/v1/chat/completions"

    # llm model name like Llama3-8B-Chinese-Chat etc
    llm_model_name = "Llama3-8B-Chinese-Chat"

    # your knowledge list
    knowledge_files = ["/usr/local/Ascend/mx_rag/knowledge/doc1.docx",
                       "/usr/local/Ascend/mx_rag/knowledge/doc2.docx",
                       "/usr/local/Ascend/mx_rag/knowledge/doc3.docx"]

    create_loader_and_spliter(mxrag_component, chunk_size=200, chunk_overlap=50)

    create_remote_connector(mxrag_component,
                            reranker_url=nim_tei_reranker_url,
                            embedding_url=nim_tei_embedding_url,
                            llm_url=llm_url,
                            llm_model_name=llm_model_name)

    create_knowledge_storage(mxrag_component, knowledge_files=knowledge_files)

    create_cache(mxrag_component,
                 reranker_url=nim_tei_reranker_url,
                 embedding_url=nim_tei_embedding_url)

    create_hybrid_search_retriever(mxrag_component)

    create_evaluate(mxrag_component)

    rag_app = build_mxrag_application(mxrag_component)

    user_question = "your question"

    start_time = time.time()
    user_answer = rag_app.invoke({"question": user_question})
    end_time = time.time()

    print(f"user_question:{user_question}")
    print(f"user_answer:{user_answer}")
    print(f"app time cost:{(end_time - start_time) * 1000} ms")
