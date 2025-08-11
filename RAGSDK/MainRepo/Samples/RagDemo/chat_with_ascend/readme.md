# RAG SDK运行说明

## 环境准备(容器化部署)

1.下载RAG
SDK镜像并按操作步骤启动容器,下载参考地址：https://www.hiascend.com/developer/ascendhub/detail/ragsdk

2.下载mindie镜像并按操作步骤启动大模型,下载参考地址：https://www.hiascend.com/developer/ascendhub/detail/af85b724a7e5469ebd7ea13c3439d48f

注意：按照操作步骤完成并执行推理脚本成功后，需按以下步骤继续启动MindIE server大模型推理服务，以供RAG
SDK调用。参考地址：https://www.hiascend.com/document/detail/zh/mindie/10RC2/envdeployment/instg/mindie_instg_0025.html

3.下载embedding模型,存放在指定目录：如/data/bge-large-zh-v1.5/（与app.py中embedding模型路径对应一致）

4.下载reranker模型(可选),存放在指定目录：如/data/bge-reranker-large/（启动时配置tei_reranker参数 ）

5.参考指导安装运行milvus数据库

链接：https://milvus.io/docs/zh/install_standalone-docker.md

## demo运行

1.将app.py文件放至容器任意目录下

2.调用示例

```
python3 app.py  --llm_url "http://127.0.0.1:1025/v1/chat/completions" --port 8080
```

可通过以下命令查看，并完善其他参数的传入

```
python3 app.py  --help
```

3.运行demo打开前端网页

![demo.png](images%2Fdemo.png)

说明：此demo适配POC版本的RAG
SDK软件包,如果使用了网络代理启动框架前先关闭代理。如果遇到pydantic.errors.PydanticSchemaGenerationError类错误，请将gradio版本切换至3.50.2。




