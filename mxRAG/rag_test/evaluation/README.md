# RAG 评测

RAG评测基于RAGAS, 采用中文prompt, 并对相应API和本地模型接口进行适配，使用户更易于使用，评测结果更准确
包含以下评测指标:

| 评测指标 | 属性 | 说明 |
| ----- | -------- | -------- |
| faithfulness | 无参考度量指标 | 衡量了生成的答案与给定上下文的事实一致性 |
| answer_relevancy | 无参考度量指标 | 评估生成的答案与用户问题之间的相关程度 |
| context_precision | 基于真实答案度量指标 | 该指标确定最接近真实情况的上下文是否获得高分 |
| context_relevancy | 无参考度量指标 | 衡量检索到的上下文的相关性 |
| context_recall | 基于真实答案度量指标 | 衡量检索到的上下文与人类提供的真实答案的一致程度 |
| context_entity_recall | 基于真实答案度量指标 | 确定真实答案中存在的所有实体是否也存在于所提供的上下文中 |
| answer_similarity | 基于真实答案度量指标 | 对真实答案和生成答案之间的语义相似性进行评分 |
| answer_correctness | 基于真实答案度量指标 | 生成答案与真实答案之间的准确性评估 |
| harmfulness | 基于真实答案度量指标 | 根据预定义的无害性评估提交的内容 |
| maliciousness | 基于真实答案度量指标 | 根据预定义的恶意评估提交的内容 |
| coherence | 基于真实答案度量指标 | 根据预定义的连贯性评估提交的内容 |
| correctness | 基于真实答案度量指标 | 根据预定义的正确性评估提交的内容 |
| conciseness | 基于真实答案度量指标 | 根据预定义的简洁性评估提交的内容 |


## 基本使用方法
evaluation.py提供了rag的测试入口
以下为该脚本的参数项说明

    --language          测试集语言类型，支持chinese(中文)和english(英文)
    --llm_url           采用LLM服务方法时，LLM的url地址
    --llm_model_name    采用LLM服务方法时，LLM的模型名称
    --embed_url         采用Embedding服务方法时，Embedding的url地址
    --embed_path        采用本地Embedding方法时，Embedding的模型权重路径
    --metric            评测指标，名称和上表一致，多个指标用逗号连接
    --output_path       评测结果输出路径
    --dataset_path      评测集路径，当前在datasets下有baseline.csv,可供用户简单测试url或本地模型

调用示例
```shell
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.10/dist-packages/mx_rag/libs
python3 evaluation.py --language chinese --llm_url http://localhost:9001 --llm_model_name Qwen1.5-7B-Chat --embed_path /data/acge-text-embedding --metric faithfulness --output_path . --dataset_path datasets/baseline.csv
```

## 评测集构建
按question、ground_truth、answer、contexts列名称构建评测集，文件类型为csv。

    question        string
    ground_truth    List[string]
    answer          string
    contexts        List[string]

## 版本依赖
| 配套     | 版本      | 环境准备指导 |
|--------|---------|--------|
| cann   | 8.0.RC1 | -      |
| python | 3.10    | -      |
| torch  | 2.1.0   | -      |
| mx_rag | 6.0     | -      |