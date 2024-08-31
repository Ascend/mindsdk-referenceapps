#!/bin/bash
#在patches/whisper目录下执行一键补丁脚本
set -e

MODEL_NAME='tiny'
DEVICE=2
SOC_VERSION="Ascend310P3"

PATCH_DIR=$(dirname $(readlink -f $0))
dist_packages=$(python3 -c "import site;print(site.getsitepackages()[0])")
dist_packages_path=$(echo "$dist_packages" | sed "s/[',\[\]]//g")
echo "dist-packages path is: $dist_packages_path"

# 初始化模型参数
declare -A params
params[tiny]="4 384 80"
params[base]="6 512 80"
params[small]="12 768 80"
params[medium]="24 1024 80"
params[large]="32 1280 128"

# 提取模型
IFS=' ' read -r -a model_params <<< "${params[$MODEL_NAME]}"
N_BLOCKS=${model_params[0]}
HIDDEN=${model_params[1]}
N_MEIS=${model_params[2]}

# 提取DEVICE参数
sed -E -i "s/set_device\([0-9]+\)/set_device($DEVICE)/g" mindietorch_infer.patch
sed -E -i "s/npu:[0-9]+/npu:$DEVICE/g" mindietorch_infer.patch
echo "set device is: $DEVICE"

function install_packages(){
    pip3 install onnx==1.16.1
    pip3 uninstall -y openai-whisper==20231117
    pip3 install openai-whisper==20231117

}

function patch_trace_model(){
    cd $dist_packages_path
    patch -p1 < $PATCH_DIR/trace_model.patch
    cd $PATCH_DIR
    DIRS=("/tmp/models"
    "/tmp/models/onnx"
    "/tmp/models/onnx/encode"
    "/tmp/models/onnx/decode"
    "/tmp/models/onnx/prefill"
    )
    for dir in "${DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            echo "Directory $dir created."
        else
            echo "Directory $dir already exists."
        fi 
        done
    whisper zh.wav --model $MODEL_NAME
}

function compile_model(){
    source /usr/local/Ascend/ascend-toolkit/set_env.sh
    source /usr/local/Ascend/mindie/set_env.sh
    source /usr/local/Ascend/ascend-toolkit/set_env.sh
    python3 compile.py --nblocks $N_BLOCKS --hidden $HIDDEN --n_mels $N_MEIS --soc_version $SOC_VERSION
}

function patch_mindietorch(){
    pip3 uninstall -y openai-whisper==20231117
    pip3 install openai-whisper==20231117
    cd $dist_packages_path
    patch -p1 < $PATCH_DIR/mindietorch_infer.patch
}

function main(){
    install_packages
    patch_trace_model
    compile_model
    patch_mindietorch
}

main