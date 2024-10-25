# 安装性能优化补丁说明
用户根据需要选择相应模型的性能优化补丁，当前只支持bert类模型（常用于embedding模型，如bge-large-zh等）和xlm_roberta类模型（常用于reranker模型，如bge-reranker-large等）

## bert模型性能优化补丁

包含两种优化补丁，分别是BertSelfAttentionFast（融合算子优化），transformers（模型计算优化）

1. BertSelfAttentionFast————使用该性能优化补丁时需要编译算子及相应的torch_npu，并修改相应的transformers源文件，具体操作参考该目录下的使用说明。
2. transformers————针对transformers中的bert模型进行了相应的计算优化，执行该目录下的tei_patch.sh即可



## xlm_roberta模型性能优化补丁
当前只包含针对transformers的性能优化补丁

1. transformers————针对transformers中的xlm_roberta模型进行了相应的计算优化，执行该目录下的tei_patch.sh即可


## 注意事项
1. transformers版本保证在4.41.1
2. 如果想要提高tei服务的性能，那么需要在tei容器下执行相应模型的性能优化补丁。如果是在mxrag容器下本地运行模型，那么就在mxrag容器下执行性能优化补丁。
3. bert下的BertSelfAttentionFast和transformers只能同时打其中一种补丁，BertSelfAttentionFast的性能更优