# 伪装目标分割

## 1、 介绍

### 1.1 简介

在本系统中，目的是基于MindX SDK，在华为云昇腾平台上，开发端到端**伪装目标分割**的参考设计，实现**对图像中的伪装目标进行识别检测**的功能，达到功能要求

本项目主要基于用于通用伪装目标分割任务的DGNet模型

- 模型的具体描述和细节可以参考原文：https://arxiv.org/abs/2205.12853

- 具体实现细节可以参考基于PyTorch深度学习框架的代码：https://github.com/GewelsJI/DGNet/tree/main/lib_pytorch

- 所使用的公开数据集是NC4K，可以在此处下载：https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/snapshots/data.tar

- 所使用的模型是EfficientNet-B4版本的DGNet模型，原始的PyTorch模型文件可以在此处下载：https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/snapshots/DGNet.zip

**注意：由于模型限制，本项目暂只支持自然场景下伪装动物的检测，不能用于其他用途**

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

|   软件名称    |    版本     |
| :-----------: | :---------: |
|     numpy     |   1.24.0  |
| opencv-python |  4.9.0.80  |
| mindspore (cpu) |  1.9.0  |
| Pillow |  9.4.0  |
| imageio |  2.36.0  |
| protobuf |  3.19.6  |


## 2、 设置环境变量

在编译运行项目前，需要设置环境变量：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```


## 3、 准备模型

### 3.1 模型获取

**步骤1** 

下载DGNet (Efficient-B4) 的ONNX模型：[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/snapshots/DGNet.zip)

### 3.2 模型转换

**步骤1** 

在项目目录./CamouflagedObjectDetection下创建models文件夹，将上一小节下载的模型文件解压后，把其中的DGNet.onnx模型文件拷贝至models文件夹

**步骤2** 

在模型所在的文件夹执行以下命令

```bash
# 进入对应目录
cd ./models
# 执行以下命令将ONNX模型（.onnx）转换为昇腾离线模型（.om）
atc --framework=5 --model=DGNet.onnx --output=DGNet --input_shape="image:1,3,352,352" --log=debug --soc_version=Ascend310P3
```

执行完模型转换脚本后，会生成相应的.om模型文件。 执行后终端输出为：

```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

## 4 运行

步骤如下：

**步骤1** 

下载测试数据集并放到项目文件夹./CamouflagedObjectDetection：[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/snapshots/data.tar)

**步骤2** 

执行以下命令将下载后的文件解压缩
```bash
tar -xf data.tar
```

**步骤3** 

执行以下命令创建项目输出文件夹
```bash
mkdir result
```

**步骤4** 

执行离线推理Python脚本
```bash
python inference_om.py --om_path ./models/DGNet.om --save_path ./result/ --data_path ./data/NC4K/Imgs
```
**注意：由于数据集图片较多，推理时间较长，可选择性输入部分图片来进行推理验证**


**步骤5**

查看结果 
推理完成的输出图片在result文件夹中

输入输出如下两图所示
输入伪装图片：![](./assets/74.jpg)
预测分割结果：![](./assets/74.png)
