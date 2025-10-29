# RAG SDK运行说明

## 环境准备(容器化部署)

1.下载RAG
SDK镜像并按操作步骤启动容器,[参考地址](https://www.hiascend.com/developer/ascendhub/detail/ragsdk)

2.参考[vllm镜像](https://vllm-ascend.readthedocs.io/en/latest/tutorials/index.html)或者参考[mindie镜像](https://www.hiascend.com/developer/ascendhub/detail/af85b724a7e5469ebd7ea13c3439d48f)运行大模型服务

3.下载tei[镜像](https://www.hiascend.com/developer/ascendhub/detail/07a016975cc341f3a5ae131f2b52399d)，参考镜像使用指导部署embedding、reranker服务。

4.参考指导安装运行[milvus数据库](https://milvus.io/docs/zh/install_standalone-docker.md)


## 运行demo

1. 将app.py文件放至容器任意目录下，当前目录需保证有写权限

2. 运行web服务
```
streamlit run app.py --server.address "服务ip" --server.port 服务端口
```
3. 在web页面配置服务化参数并体验使用demo


![demo.png](./images/demo.png)

## 上传知识文档问答




