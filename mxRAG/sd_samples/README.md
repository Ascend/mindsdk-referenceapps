# 安装stable_diffusion运行说明

## 安装前准备
1）建议在容器中运行sd模型

2）注意运行的环境不能有torch-npu,如果存在，需卸载; 运行模型依赖MindIE 1.0.R2及以上的版本

下载MindIE SD适配代码，并切换到指定节点
```
git clone https://gitee.com/ascend/ModelZoo-PyTorch.git
git checkout a6cef84ca2cce2413a3c34baa1649e05def18b67
```

1.安装fastapi uvicorn python库
```bash
pip3 install fastapi>=0.110.0 uvicorn diffusers
```

2.对stable_diffusion_pipeline文件打补丁

复制补丁文件 stable_diffusion_pipeline_parallel_web.patch 和stable_diffusion_pipeline_web.patch到
ModelZoo-PyTorch/MindIE/MindIE-Torch/built-in/foundation/stable_diffusion目录下

```bash
patch -p0 stable_diffusion_pipeline_parallel.py < stable_diffusion_pipeline_parallel_web.patch
patch -p0 stable_diffusion_pipeline.py < stable_diffusion_pipeline_web.patch
```

3.其他步骤完全参考[MindIE](https://gitee.com/ascend/ModelZoo-PyTorch/tree/master/MindIE/MindIE-Torch/built-in/foundation/stable_diffusion#stable-diffusion%E6%A8%A1%E5%9E%8B-%E6%8E%A8%E7%90%86%E6%8C%87%E5%AF%BC)指导

4 SD模型启动成功后

可通过网页进行功能测试
访问url: 设备物理ip:端口/docs

