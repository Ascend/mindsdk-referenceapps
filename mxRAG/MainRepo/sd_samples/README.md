# 安装stable-diffusion运行文生图参考样例说明

## 安装前准备
1）安装部署mindie容器，镜像及部署指导参考[链接](https://www.hiascend.com/developer/ascendhub/detail/af85b724a7e5469ebd7ea13c3439d48f)

此处只需使用mindie镜像和软件包安装包，无需执行部署大模型相关操作

2）注意运行的环境不能有torch-npu,如果存在，需卸载; 运行模型依赖MindIE 1.0.R2及以上的版本

3）下载SD 模型，下载链接如下

https://huggingface.co/stabilityai/stable-diffusion-2-1-base

4） 下载MindIE SD适配代码，并切换到指定节点
```
git clone https://gitee.com/ascend/ModelZoo-PyTorch.git
git checkout a6cef84ca2cce2413a3c34baa1649e05def18b67
```

5）对stable_diffusion_pipeline文件打补丁

复制当前指导文件所在目录下的补丁文件 stable_diffusion_pipeline_parallel_web.patch 和stable_diffusion_pipeline_web.patch到
ModelZoo-PyTorch/MindIE/MindIE-Torch/built-in/foundation/stable_diffusion目录下

```bash
cd ModelZoo-PyTorch/MindIE/MindIE-Torch/built-in/foundation/stable_diffusion
patch -p0 stable_diffusion_pipeline_parallel.py < stable_diffusion_pipeline_parallel_web.patch
patch -p0 stable_diffusion_pipeline.py < stable_diffusion_pipeline_web.patch
```

6）安装MindIE依赖
```
pip3 install fastapi>=0.110.0 uvicorn diffusers

pip3 install -r requirements.txt
```

7）设置环境变量
```
source /usr/local/Ascend/mindie/set_env.sh
```
8）打stable_diffusion补丁
```
python3 stable_diffusion_clip_patch.py
python3 stable_diffusion_attention_patch.py
python3 stable_diffusion_unet_patch.py
```

9）导出pt模型并进行编译
```
(根据执行步骤3下载权重路径适配修改如下变量)
model_base="./stable-diffusion-2-1-base"
```

导出pt模型：
```
python3 export_ts.py --model ${model_base} --output_dir ./models \
        --parallel \
        --use_cache
```
参数说明：

--model：模型名称或本地模型目录的路径

--output_dir: pt模型输出目录

--parallel：【可选】模型使用双芯/双卡并行推理

--use_cache: 【可选】模型使用UnetCache优化

--use_cache_faster: 【可选】模型使用deepcache+faster融合方案

10）启动web服务执行推理

不使用并行：
```
python3 stable_diffusion_pipeline.py \
        --model ${model_base} \
        --prompt_file ./prompts.txt \
        --device 0 \
        --save_dir ./results \
        --steps 50 \
        --scheduler DDIM \
        --soc Duo \
        --output_dir ./models \
        --use_cache
```

使用并行时：
```
 python3 stable_diffusion_pipeline_parallel.py \
        --model ${model_base} \
        --prompt_file ./prompts.txt \
        --device 0,1 \
        --save_dir ./results \
        --steps 50 \
        --scheduler DDIM \
        --soc Duo \
        --output_dir ./models \
        --use_cache
```
参数说明：

--model：模型名称或本地模型目录的路径。

--prompt_file：输入文本文件，按行分割。

--save_dir：生成图片的存放目录。

--steps：生成图片迭代次数。

--device：推理设备ID；可用逗号分割传入两个设备ID，此时会使用并行方式进行推理。

--scheduler: 【可选】推荐使用DDIM采样器。

--soc: 硬件配置，根据硬件配置选择Duo或者A2。A2特指910B4。

--output_dir: 编译好的模型路径。

--use_cache: 【可选】推荐使用UnetCache策略。

--use_cache_faster: 【可选】模型使用deepcache+faster融合方案。


上面步骤可参考[MindIE](https://gitee.com/ascend/ModelZoo-PyTorch/tree/master/MindIE/MindIE-Torch/built-in/foundation/stable_diffusion#stable-diffusion%E6%A8%A1%E5%9E%8B-%E6%8E%A8%E7%90%86%E6%8C%87%E5%AF%BC)指导

# 大模型测试
执行如下命令生成dog.jpeg文件
```
curl http://127.0.0.1:7860/text2img \
    -X POST \
    -d '{"prompt":"dog wearing black glasses", "output_format": "jpeg", "size": "512*512"}' \
    -H 'Content-Type: application/json' | awk -F '"' '{print $2}' | base64 --decode > dog.jpeg
```


