# 微调评估说明

使用mx_rag可以对embedding和reranker模型进行微调，这里提供微调模型的简单评估脚本

## 运行步骤

1.安装依赖

2.启动评估脚本

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.10/dist-packages/mx_rag/libs
python3 eval.py --eval_data /path/to/dataset --embedding_path /path/to/embedding --reranker_path /path/to/reranker
```

## 注意事项

1. 默认使用eval_data目录下的corpus_data.jsonl和eval_data.jsonl作为评估数据

## 版本依赖

| 配套     | 版本      | 环境准备指导 |
|--------|---------|--------|
| cann   | 8.0.RC1 | -      |
| python | 3.10    | -      |
| torch  | 2.1.0   | -      |
| mx_rag | 6.0     | -      |