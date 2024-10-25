# 开源软件补丁目录说明

1. TEI————针对huggingface推出的text-embeddings-inference适配了昇腾torch_npu，方便用户基于昇腾使用高性能tei服务
2. optimize————针对transformers中常见的embedding和reranker模型进行了高度优化，包含融合算子和模型计算优化等方式。对本地或tei服务运行模型均有一定性能收益。
3. whisper————针对openai推出的whisper适配了昇腾torch_npu，方便用户基于昇腾使用whisper