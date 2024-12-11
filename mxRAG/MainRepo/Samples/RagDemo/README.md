# mxRAG Demo运行说明

## 前提条件

执行Demo前请先阅读《MindX SDK mxRAG用户指南》，并按照其中"安装部署"章节的要求完成必要软、硬件安装。
本章节为"应用开发"章节提供开发样例代码,便于开发者快速开发。

## 样例说明
详细的样例介绍请参考《MindX SDK mxRAG用户指南》"应用开发"章节说明。 其中：

1.rag_demo_knowledge.py为"创建知识库"样例代码; rag_demo_query为"在线问答"样例代码。

2."创建知识库"样例和"在线问答"样例是以FLATL2检索方式为例，当参数tei_emb为False时表示本地启动embedding模型，需传入参数embedding_path,当参数tei_emb为True时，表示启动服务化模型，需传入参数embedding_url；reranker同理，其中reranker为可选过程，默认不使用。

3.rag_demo_cache_qa.py对应"MxRAGCache缓存和自动生成QA"样例。

4.fastapi_demo目录下为fastapi多线程并发调用在线问答的样例。

5.langchain_chains目录下为使用langchain llm chain支持双向认证样例。

注意：
1.创建知识库过程和在线问答过程使用的embedding模型、关系数据库路径、向量数据库路径需对应保持一致。其中关系数据库和向量数据库路径在样例代码中已经默认设置成一致，embedding模型需用户手动设置成一致。


## 运行及参数说明

1.调用示例
```commandline
# 上传知识库
python3 rag_demo_knowledge.py  --file_path "/home/data/MindIE.docx" "/home/data/gaokao.docx"  

# 在线问答
python3 rag_demo_query.py --query "请描述2024年高考作为题目"   

# fastapi多线程并发调用
python3 fastapi_multithread.py --llm_url http://x.x.x.x:port/v1/chat/completions 为启动fastapi服务端在线问答，python3 fastapi_request.py为客户端多线程并发请求在线问答的样例，若想单次请求也可以使用curl指令，请求示例如下：
curl -X 'POST' 'http://127.0.0.1:8000/query/' -H 'Content-Type: application/json' -d '{"question": "介绍一下2024年高考题目"}'
```
说明:调用示例前请先根据用户实际情况完成参数配置,确保embedding模型路径正确，大模型能正常访问，文件路径正确等，参数可以通过修改样例代码，也可通过命令行的方式传入。

2.参数说明
```commandline
以"创建知识库"为例,用户可以通过以下命令查看参数情况;如需开发其他样例,请详细参考《MindX SDK mxRAG用户指南》"接口参考"章节。
python3 rag_demo_knowledge.py  --help
```