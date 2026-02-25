# Websearcher Agent 训练指南

## 1. 下载数据

- 嵌入模型：[e5-base-v2](https://huggingface.co/intfloat/e5-base-v2)
- 本地 RAG 数据：[Wiki 语料库文件](https://huggingface.co/datasets/inclusionAI/ASearcher-Local-Knowledge/tree/main)
- 训练数据集：[AsearcherBase35k](https://huggingface.co/datasets/inclusionAI/ASearcher-train-data)

## 2. 预处理数据集

### 2.1 分割数据集
```bash
cd /path/to/your/AgentSDK/websearcher/utils

python split_dataset.py input.jsonl train.jsonl test.jsonl 0.8
```

### 2.2 数据集字段转换
```bash
cd /path/to/your/AgentSDK/websearcher/utils

python process_data.py
# Note: 请确保已修改文件路径
```

## 2. 启动本地 RAG 服务

```bash 
pip install faiss-cpu==1.7.4

# 切换至工作目录
cd /path/to/your/AgentSDK

# 构建本地 wiki RAG 索引
bash examples/agents/websearcher/scripts/build_index.sh

# 启动本地 RAG 服务 (端口号 11101)
bash examples/agents/websearcher/scripts/launch_local.server.sh 11101
```

## 3. 训练 Websearcher Agent
使用AgentSDK训练智能体
```bash
agentic_rl --config-path="/your_config_dir/your_config_file_name.yaml"

# Note:
# 1. 请确保已启动本地 RAG 服务 (端口号 11101)。
# 2. 请根据实际情况修改配置文件中的各个参数。
# 3. 需要修改agents_configuration.py中tokenizer的路径
```

## 4. tensorboard 可视化
```bash
tensorboard --logdir=/path/to/your/tensorboard_logs
```
