# mxRAG Demo运行说明

## 前提条件

执行Demo前请先阅读《MindX SDK mxRAG用户指南》，并按照其中"安装部署"章节的要求完成必要软、硬件安装。
本章节为"应用开发"章节提供开发样例代码,便于开发者快速开发。

## 样例说明
详细的样例介绍请参考《MindX SDK mxRAG用户指南》"应用开发"章节说明。 其中：

1.rag_demo_knowledge.py为"创建知识库"样例代码; rag_demo_query为"在线问答"样例代码。

2."创建知识库"样例和"在线问答"样例是以FLATL2检索方式为例，当参数tei_emb为False时为本地启动模型样例，embedding_path传入本地模型地址
，当参数tei_emb为True时，表示启动服务化模型，embedding_path传入服务化模型URI地址；reranker同理，其中reranker为可选过程，默认不使用。

3.rag_demo_cache_qa.py对应"MxRAGCache缓存和自动生成QA"样例。

4.rag_demo_tree.py对应"递归树检索"样例。


注意：
1.创建知识库过程和在线问答过程使用的 embedding模型、关系数据库路径、向量数据库路径需对应保持一致。其中关系数据库和向量数据库路径在样例代码中已经
默认设置成一致，embedding模型需用户手动设置成一致。


## 运行及参数说明
1.修改对应参数
```commandline
以FLATL2检索方式本地启动模型为例,其他样例参数如有不同请参考《MindX SDK mxRAG用户指南》"接口参考"章节。
 --embedding_path表示embedding模型的本地路径，根据用户实际路径配置。
 --tei_emb表示是否使用TEI服务化的embedding模型，默认False,为True时reranker_path表示模型url地址。
 --embedding_dim表示embedding模型向量维度，根据使用的具体模型修改，默认值1024。
 --white_path表示白名单地址，文件路径需在白名单路径下，根据用户实际路径配置。
 --file_path表示要上传的文件路径，需在白名单路径下，根据用户文件存在的实际路径配置。
 --llm_url表示大模型url地址。
 --model_name表示大模型名称。
 --score_threshold表示相似性得分的阈值，大于阈值认为检索的信息与问题越相关，取值范围[0,1]。
 --tei_reranker表示是否使用TEI服务化的reranker模型，默认False,为True时reranker_path表示模型url地址。
 --reranker_path表示reranker模型本地路径。
 --query表示用户问题
```
2.调用示例
```commandline
# 上传知识库
python3 rag_demo_knowledge.py  --file_path "/home/data/MindIE.docx" "/home/data/gaokao.docx"  

# 在线问答
python3 rag_demo_query.py --query "请描述2024年高考作为题目"   
```
说明:其他参数也可通过命令行的方式传入
