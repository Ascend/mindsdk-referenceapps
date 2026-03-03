# Agent SDK——Meta ARE 训练

## 1 介绍

### 1.1 简介
使用AgentSDK对Meta ARE在GAIA2的search数据集下的轨迹进行GRPO训练的示例。

### 1.2 支持的产品
本教程支持昇腾 Atlas A2 训练系列产品，如 Atlas 800T A2。

### 1.3 支持的版本
| Agent SDK 版本 | CANN 版本 | Driver / Firmware 版本 |
|--------------|---------|----------------------|  
| 26.0.0       | 8.3.RC1 | 25.3.RC1             |

## 2 安装 Agent 软件包
### 2.1 获取软件包
参考[AgentSDK开源仓库](https://gitcode.com/Ascend/AgentSDK/blob/master/docs/zh/installation_guide.md)进行操作。

### 2.2 安装软件包
**步骤1：** 将 Agent SDK 软件包下载到安装环境的任意路径下，并进入软件包所在路径。

**步骤2：** 执行安装命令。
```sh
chmod u+x Ascend-mindsdk-agentsdk_{version}_linux-aarch64.run
./Ascend-mindsdk-agentsdk_{version}_linux-aarch64.run --install
```

**步骤3：** 设置环境变量。
```sh
export PATH=$PATH:~/.local/bin
```

## 3 安装开源软件及设置环境变量
通过 AgentSDK 使用 MindSpeed-RL 进行训练时，需安装以下指定版本开源软件至指定位置，并设置相应环境变量。

```sh
mkdir -p /home/third-party # 可自定义目录
cd /home/third-party

git clone https://github.com/NVIDIA/Megatron-LM.git
cd Megatron-LM
git checkout core_r0.8.0
cd ..

git clone https://github.com/Ascend/MindSpeed.git
cd MindSpeed
git checkout 2.1.0_core_r0.8.0
cd ..

git clone https://github.com/Ascend/MindSpeed-LLM.git
cd MindSpeed-LLM
git checkout 2.1.0
cd ..

git clone https://github.com/Ascend/MindSpeed-RL.git
cd MindSpeed-RL
git checkout 2.2.0
cd ..

git clone https://github.com/vllm-project/vllm.git
cd vllm
git checkout v0.9.1
VLLM_TARGET_DEVICE=empty pip3 install -e .
cd ..

pip3 install --ignore-installed --upgrade blinker=1.9.0
git clone https://github.com/vllm-project/vllm-ascend.git
cd vllm-ascend
git checkout v0.9.1-dev
pip3 install -e .
cd ..

pip3 install -r MindSpeed/requirements.txt
pip3 install -r MindSpeed-LLM/requirements.txt
pip3 install -r MindSpeed-RL/requirements.txt

# 安装Meta are
git clone https://github.com/facebookresearch/meta-agents-research-environments.git
cd meta-agents-research-enviroments
git checkout mortimer/cachefilesystem
pip3 install inputimeout==1.0.4
pip3 install termcolor==2.5.0
pip3 install mammoth==1.8.0
pip3 install markdownify==0.14.1
pip3 install pdfminer.six==20231228
pip3 install python-pptx==1.0.2
pip3 install puremagic==1.27
pip3 install rapidfuzz==3.12.1
pip3 install polars-lts-cpu==1.33.1
pip3 install Jinja2==3.1.6
pip3 install python-dotenv==1.0.1
pip3 install docstring-parser==0.16
pip3 install click==8.1.8
cd ..
 
# 使能环境变量，根据实际安装的情况调整目录
source /usr/local/Ascend/driver/bin/setenv.sh
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
export PYTHONPATH=$PYTHONPATH:/home/third-party/Megatron-LM/\
:/home/third-party/MindSpeed/\
:/home/third-party/MindSpeed-LLM/\
:/home/third-party/MindSpeed-RL\
:/home/third-party/rllm/\
:/home/third-party/meta-agents-research-environments/

```

## 4 运行
**步骤1：** 下载示例代码[meta-are](../meta-are)至工作文件夹。

**步驟2：** 下載模型Qwen3-4B的huggingface权重，并完成权重转换
```shell
# 转换脚本，需要进入Mindspeed-LLM目录
python convert_ckpt.py \
  --use-mcore-models \
  --model-type GPT \
  --load-model-type hf \
  --save-model-type mg \
  --target-tensor-parallel-size 8 \
  --target-pipeline-parallel-size 1 \
  --spec mindspeed_llm.tasks.models.spec.qwen3_spec layer_spec \
  --load-dir /path/to/Qwen3-4B \
  --save-dir /path/to/Qwen3-4B-mcore-tp8 \
  --tokenizer-model /path/to/Qwen3-4B/tokenizer.json \
  --params-dtype bf16 \
  --model-type-hf qwen3
```

**步骤3：** 参考[gaia2](https://huggingface.co/datasets/meta-agents-research-environments/gaia2)下载数据集，然后处理数据集
```shell
# 默认会在当前目录下生成search.jsonl文件，也可以通过--output指定保存路径
python3 process_datasets --path ./gaia2
```

**步骤4：** 新建 yaml 配置文件，编辑配置参数:
```sh
vim meta-are-conf.yaml

# 编辑配置参数
tokenizer_name_or_path: /path/to/Qwen3-4B
agent_name: math
model_name: qwen3-4b
agent_engine_wrapper_path: /path/to/are_engine_wrapper.py
use_stepwise_advantage: false
max_steps: 40
rollout_n: 8
use_tensorboard: true

num_gpus_per_node: 8
kl_penalty: low_var_kl
entropy_coeff: 0.001

max_model_len: 40960
infer_tensor_parallel_size: 8
gpu_memory_utilization: 0.4
dataset_additional_keys: ["data"]

top_k: 40
top_p: 0.9
min_p: 0.0
temperature: 0.8

train_backend: mindspeed_rl
mindspeed_rl:
  data_path: /path/to/search.jsonl
  load_params_path: /path/to/Qwen3-4B-mcore-tp8/
  save_params_path: /path/to/Qwen3-4B-mcore-tp8-new/
  tensor_model_parallel_size: 8
  global_batch_size: 8
  mini_batch_size: 8
  seq_length: 40960
  train_iters: 160
  save_interval: 20
```

**步骤5：** 启动训练任务。
```sh
agentic_rl --config-path="/path/to/meta-are-conf.yaml"
```

**步骤6：** 查看结果；运行后会在 `save_params_path` 目录下保存模型权重文件，当前路径会生成runs目录保存tensorboard信息。
```sh
# 修改ip即可查看各项指标数据
tensorboard --logdir runs --host {your_ip}
```
