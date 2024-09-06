# mxRAG Demo运行说明

## 前提条件

执行Demo前请先阅读《MindX SDK mxRAG用户指南》，并按照其中"安装部署"章节的要求完成必要软、硬件安装。
本章节为"应用开发"章节提供开发样例代码,便于开发者快速开发。

## 样例说明
详细的样例介绍请参考《MindX SDK mxRAG用户指南》"应用开发"章节说明。 其中：

rag_demo_l2.py对应"FLATL2检索方式本地启动模型"。

rag_demo_l2_tei.py对应"FLATL2检索方式服务化启动模型(TEI)"。

rag_demo_tree.py对应"递归树检索"。

rag_demo_cache_qa.py对应"MxRAGCache缓存和自动生成QA"。
## 运行及参数说明
1.修改对应参数
```commandline
以FLATL2检索方式本地启动模型为例,其他样例参数如有不同请参考《MindX SDK mxRAG用户指南》"接口参考"章节。
 --embedding_path表示embedding模型的本地路径，根据用户实际路径配置。
 --embedding_dim表示embedding模型向量维度，根据使用的具体模型修改，默认值1024。
 --white_path表示白名单地址，文件路径需在白名单路径下，根据用户实际路径配置。
 --file_path表示要上传的文件路径，需在白名单路径下，根据用户文件存在的实际路径配置。
 --llm_url表示大模型url地址。
 --model_name表示大模型名称。
 --score_threshold表示相似性得分计算阈值，距离越近表示越相似，低于阈值认为检索的信息与问题相关。
 --reranker_path表示reranker模型本地路径。
 --query表示用户问题
```
2.调用示例
```commandline
python3 rag_demo_l2.py --query "请描述2024年高考作为题目" 
```
说明:其他参数也可通过命令行的方式传入
