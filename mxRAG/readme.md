# mxRAG

mxRAG是昇腾面向大预言模型的知识增强开发套件，为解决大模型知识更新缓慢以及垂直领域知识问答弱的问题，面向大模型知识库提供垂域调优、生成增强、知识管理等特性，帮助用户搭建专属的高性能、准确度高的大模型问答系统。


## 版本配套说明
本版是基于MindX SDK 6.0.RC3版本mxRAG的开发参考样例,使用前请先阅读《MindX SDK 6.0.RC3 mxRAG用户指南》。
## 支持的硬件和运行环境

| 产品系列                            | 产品型号                |
|---------------------------------|---------------------|
| Atlas 推理系列产品（Ascend 310P AI处理器） | Atlas 300I Duo 推理卡  |
| Atlas 800I A2推理产品               | Atlas 800I A2 推理服务器 | 
支持的软件运行环境为:Ubuntu 22.04，Python3.10或Python3.11

## 目录结构与说明
| 目录       | 说明                                                                                              |
|----------|-------------------------------------------------------------------------------------------------|
| Dockerfile     | 部署mxRAG容器,用户若自行准备镜像文件的参考样例，对应用户手册《安装mxRAG》章节。                                                   |
| Samples   | mxRAG完整开发流程的开发参考样例,包含"创建知识库"、"在线问答"、"MxRAGCache缓存和自动生成QA"、以及prompt压缩支持的长文档问答、长文档总结、日志分析场景提供样例代码 |
| chat_with_ascend    | 基于python的gradio前端框架构建的mxRAG"知识库创建"和"在线问答"系统。                                                    |
| code_with_ascend | 基于vscode插件开发的依赖大模型的代码补全、解释、生成测试用例等功能的参考样例。                                                      |
| finetune   | mxRAG对embedding和reranker模型进行微调模型评估脚本。                                                           |
| langgraph    | MxRAG基于LangGraph知识检索增强应用使能方案。                                                                   |
| llm_samples  | 基于fastchat快速拉起大模型参考样例。                                                                          |
| patches   | mxRAG补丁安装文件,包括支持融合算子、支持TEI、支持whisper模型。                                                         |
| rag_test    | RAG评测脚本，基于RAGAS, 采用中文prompt, 对相应API和本地模型接口进行适配。                                                 |
| sd_samples  | 安装并运行stable_diffusion模型参考样例。                                                                    |


 


