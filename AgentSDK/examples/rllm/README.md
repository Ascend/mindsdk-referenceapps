# Agent SDK快速入门——BaseEngineWrapper抽象类基本使用教程

## 1 介绍

### 1.1 简介
BaseEngineWrapper 类提供统一的抽象接口，允许不同的 AgentEngine 自行适配，从而实现 AgentSDK AgenticRL 训推调 API 与多种类型 AgentEngine 的功能对接。本教程以 rLLM agent 引擎为例，提供 BaseEngineWrapper 的实现类 RllmEngineWrapper，并提供 math agent 的特定场景，实现 rLLM 与 AgentSDK AgenticRL 训推调 API 的功能对接。

### 1.2 支持的产品
本教程支持昇腾 Atlas A2 训练系列产品，如 Atlas 800T A2。

### 1.3 支持的版本
| Agent SDK 版本 | CANN 版本 | Driver / Firmware 版本 |
|----|----|----|  
| 7.3.0 | 8.3.RC1   | 25.3.RC1   |

## 2 安装 Agent 软件包
### 2.1 获取软件包
联系华为工程师获取 `Ascend-mindsdk-agentsdk_7.3.0_linux-aarch64.run`

### 2.2 安装软件包
**步骤1：** 将 Agent SDK 软件包下载到安装环境的任意路径下，并进入软件包所在路径。

**步骤2：** 执行安装命令。
```sh
chmod u+x Ascend-mindsdk-agentsdk_7.3.0_linux-aarch64.run
./Ascend-mindsdk-agentsdk_7.3.0_linux-aarch64.run --install
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
git checkout v2.2.0
cd ..

git clone https://github.com/rllm-org/rllm.git
cd rllm
git checkout v0.1
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

# 使能环境变量，根据实际安装的情况调整目录
source /usr/local/Ascend/driver/bin/setenv.sh
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
export PYTHONPATH=$PYTHONPATH:/home/third-party/Megatron-LM/:/home/third-party/MindSpeed/:/home/third-party/MindSpeed-LLM/:/home/third-party/MindSpeed-RL:/home/third-party/rllm/
```

## 4 运行
**步骤1：** 下载示例代码 `AgentSDK/examples/rllm` 至工作文件夹。


**步骤2：** 新建 yaml 配置文件，编辑配置参数:
```sh
vim /your_config_dir/your_config_file_name.yaml

# 编辑配置参数
tokenizer_name_or_path: ...
data_path: ...
load_params_path: ...
save_params_path: ...
epochs: ...
agent_name: math
agent_engine_wrapper: /your_workdir/AgentSDK/examples/rllm/rllm_engine_wrapper.py
```

**步骤3：** 进入`AgentSDK`目录，启动训练任务。
```sh
cd /your_workdir/AgentSDK
agentic_rl --config-path="/your_config_dir/your_config_file_name.yaml"
```

**步骤4：** 查看结果；运行后会在 `save_params_path` 目录下保存模型权重文件。
