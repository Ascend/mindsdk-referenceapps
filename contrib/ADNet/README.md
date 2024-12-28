# ADNet图像去噪参考设计

## 1  介绍
### 1.1 简介
使用 ADNet 模型，在 MindX SDK 环境下实现灰度图像去噪功能。
由用户设置测试图片，传入到 pipeline 中先后实现前处理，模型推理，后处理等功能，最终输出结果图片实现可视化。

本模型在以下几种情况去噪效果良好：含有目标数量多、含有目标数量少、前景目标面积占比图像较大、前景目标面积占比图像较小、各目标边界清晰。

在以下两种情况去噪效果不太好：1. 图像中各目标之间的边界不清晰，可能会出现过度去噪、目标模糊的情况。 2. 图像中前景目标较多，可能会出现无法完成目标精确化降噪的情况。

```
ADNet 是一种包含注意力模块的卷积神经网络，主要包括用于图像去噪的稀疏块（SB）、特征增强块（FEB）、注意力块（AB）和重建块（RB）。

其中，SB 模块通过使用扩张卷积和公共卷积来去除噪声，在性能和效率之间进行权衡。FEB 模块通过长路径整合全局和局部特征信息，以增强去噪模型的表达能力。 

AB 模块用于精细提取复杂背景中的噪声信息，对于复杂噪声图像，尤其是真实噪声图像非常有效。 此外，FEB 模块与 AB 模块集成以提高效率并降低训练去噪模型的复杂度。

最后，RB 模块通过获得的噪声映射和给定的噪声图像来构造干净的图像。
```



实现流程图如下图所示：

![流程](./流程.png)


pipeline流程如下图所示：

![pipeline](./pipeline.png)


### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。


### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 


### 1.4 代码目录结构与说明

本工程名称为ADNet，工程目录如下图所示：

```
├── main.py  //运行工程项目的主函数
├── t.pipeline      //pipeline
├── model   //存放模型文件
|   └──aipp_adnet.cfg     //预处理配置文件
├── 流程.png          //流程图
├── pipeline.png      //pipeline流程图
└──README.md          
```

### 1.5 三方依赖
本项目除了依赖昇腾Driver、Firmware、CANN和mxVision及其要求的配套软件外，还需额外依赖以下python软件：

| 软件名称 | 版本        |
| -------- |-----------|
| opencv-python   | 4.10.0.84 |
| numpy   | 1.24.0    |


## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：


```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
# mxVision-path: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
```
## 3  模型转换
**步骤 1** 下载模型相关文件

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ADNet/ATC%20ADNet.zip)下载并解压文件。在解压后的`ATC ADNet/model`目录中获取得到ADNet.onnx模型文件放置在本项目的`ADNet/model`目录下。

**步骤 2** 转换模型

进入ADNet/model文件夹下执行命令

```
atc --framework=5 --model=ADNet.onnx --insert_op_conf=./aipp_adnet.cfg --output=ADNet_bs1 --input_format=NCHW -input_shape="image:1,1,321,481" --log=debug --soc_version=Ascend310P3 --output_type=FP32
 ```

执行该命令会在当前目录下生成项目需要的模型文件ADNet_bs1.om。执行后终端输出为

 ```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

表示命令执行成功。

## 4  运行

**步骤 1**  将任意一张jpg格式的灰度图片放到项目根目录下，命名为test.jpg。

**步骤 2**  在命令行输入下述命令运行整个工程。

```
python3 main.py
```

**步骤 3** 查看结果。模型输出的可视化结果保存在result.jpg文件，打开该文件即可查看结果。
