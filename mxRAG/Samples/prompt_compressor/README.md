# prompt compressor运行说明

## 前提条件
执行前请先阅读《MindX SDK mxRAG用户指南》，并按照其中"安装部署"章节的要求完成必要软、硬件安装。

本章节为prompt压缩支持的长文档问答、长文档总结、日志分析场景提供样例代码，便于开发者快速开发。

此demo适配MindX 6.0.T157（POC）版本的mxrag软件包。

## 框架说明
压缩流程抽象为三个步骤：

pre_processor：预处理，主要是一些长文本切分方法，和场景强相关。

core_processor：sentences排序和其他核心处理，也包括ranker、cluster等用于压缩过滤的方法。

core_processor：排序或者聚类后的处理，筛选出保留的sentences，和场景强相关。

用户需要根据自身数据特征，去判断当前提供的方法是否适用，若不适用，可自己二次开发。

## 场景划分
长文档问答：class DocQaCompressor 封装了端到端的处理流程，根据文档结构不同，区分出了结构化文档处理和非结构化文档处理在。

长文档总结：class ClusterSummary 封装了端到端的处理流程。

日志分析：class LogAnalyseCompressor 封装了端到端的处理流程。

## 数据说明
./data目录提供了prompt压缩可用的参考数据。

./data/doc/structured.json: 用于长文档问答结构化文档场景。

./data/doc/unstructured.txt: 用于长文档问答非结构化文档场景。

./data/doc/summary.txt: 用于长文档总结场景。

./data/log/valid_log.jsonl：用于日志分析场景。

./data/log/history_label.jsonl：用于辅助日志分析场景构造prompt时，提取部分数据作为few-shot。

## Rest服务化样例
server.py：此文件将DocQaCompressor，LogAnalyseCompressor，ClusterSummary 实例化，并提供了对外的访问接口。

client.py：通过requests请求，访问server发布的接口，实现对应的prompt压缩功能。

此处仅仅提供调用的示例，用户也可不通过服务化，直接调用对应的接口，例如：
```commandline
doc_qa = DocQaCompressor(model_path, device_id)
compressed_text = doc_qa.run_doc_qa(context, question, target_tokens, target_rate)
```

## server 服务启动
```commandline
uvicorn server:app
更多启动参数见 uvicorn --help
```

## client 参数说明
```commandline
 --host表示server服务的主机地址，默认 127.0.0.1
 --port表示server服务的端口号，默认 8000
 --scenes表示想要调用的场景，目前支持：doc_qa_unstructured, doc_qa_structured, log_analyse, doc_summary
 --file_path表示数据所在文件路径
 --question表示针对数据想要执行的指令，或者要问的问题
 --topk表示要召回的sentences数量，用于长文档问答结构化文本的场景
 --target_tokens表示压缩后的目标token数量，用于长文档问答非结构化文本的场景
 --target_rate表示压缩后剩余文本的比例，用于长文档问答非结构化文本的场景
 --compress_rate表示需要删除的sentences的比例，是一个大致的删除比例，用于长文档总结场景
 --embedding_batch_size表示embedding时候的并发度，用于长文档总结场景
 --min_cluster_size表示密度聚类时候的最小尺寸，值越小，划分的社区个数越多，用于长文档总结场景
```

## client 使用示例
```commandline
python3 client.py --scenes doc_qa_structured --file_path './data/doc/structured.json' --question '故障处理原则是什么' --topk 5
python3 client.py --scenes doc_qa_unstructured --file_path './data/doc/unstructured.txt' --question '故障处理原则是什么' --target_tokens 3000 --target_rate 0.5
python3 client.py --scenes log_analyse --file_path './data/log/valid_log.jsonl' --question '请将断言失败之前的信息以及error message 提取出来'
python3 client.py --scenes doc_summary --file_path './data/doc/summary.txt' --question '请给上述内容起一个标题' --compress_rate 0.6 --embedding_batch_size 64 --min_cluster_size 2
```
