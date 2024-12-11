# 使用说明
默认不使用双向认证，ssl为True时，需要传递ca_path，cert_path，key_path，pwd等字段

	不使用认证
	python3 llm_chain_stream.py --base_url http://127.0.0.1:1025/v1 --model_name Llama3-8B-Chinese-Chat

	使用双向认证：
	python3 llm_chain_stream.py --base_url https://127.0.0.1:1025/v1 --model_name Llama3-8B-Chinese-Chat --ssl True --ca_path xxx --cert_path xxx --key_path xxx --pwd xxx
