# CenterNet 目标检测
## 1. 介绍
### 1.1 简介
CenterNet 目标检测后处理插件基于 MindX SDK 开发，对图片中的不同类目标进行检测，将检测得到的不同类的目标用矩形框标记。输入一幅图像，可以检测得到图像中大部分类别目标的位置。本方案使用在 COCO2017 数据集上训练得到的 CenterNet 模型进行目标检测，数据集中共包含 80 个目标类，包括行人、自行车、公共汽车、手机、沙发、猫、狗等，可以对不同类别、不同角度、不同密集程度的目标进行检测。

整体业务流程为：待检测图片通过 appsrc 插件输入，然后使用图像解码插件 mxpi_imagedecoder 对图片进行解码，再通过图像缩放插件 mxpi_imageresize 将图像缩放至满足检测模型要求的输入图像大小要求，缩放后的图像输入模型推理插件 mxpi_tensorinfer 得到推理结果，推理结果输入 mxpi_objectpostprocessor 插件进行后处理，得到输入图片中所有的目标框位置和对应的置信度。最后通过输出插件 appsink 获取检测结果，并在外部进行可视化，将检测结果标记到原图上.
### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。


### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖

本项目除了依赖昇腾Driver、Firmware、CANN和MxVision及其要求的配套软件外，还需额外依赖以下软件：

| 软件名称   | 版本       |
|--------|----------|
| opencv-python | 4.9.0.80 |
| numpy | 1.24.0   |
| webcolors | 24.8.0   |
| NumCpp | 2.12.1   |

* NumCpp需要下载源码, 请用户至 https://github.com/dpilger26/NumCpp 进行下载。下载完成后，无需编译，仅需将NumCpp源码目录下的include/NumCpp目录拷贝至项目根目录下的postprocess/include目录（postprocess/include目录需要手动创建）。
### 1.5 代码目录结构与说明

本工程名称为 CenterNet，工程目录如下所示：
```
├── postprocess
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── CenterNetPostProcess.cpp
│   └── CenterNetPostProcess.h
├── python
│   ├── Main
│   │   ├── pre_post.py
│   │   └── colorlist.txt
│   ├── models
│   │   ├── aipp-configs
│   │   │   └── aipp_bgr.config
│   │   └──  centernet.cfg
│   └── pipeline
│       └── pre_post.pipeline
└── README.md

```

## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：


```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
# mxVision: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
```

## 3 准备模型
步骤1 下载模型相关文件

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/CenterNet/ATC%20CenterNet.zip)下载并解压，在解压后的310P_model目录下得到CenterNet.onnx文件，并放在``python/models`` 目录下。


根据[链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/contrib/Collision/model/coco.names)下载coco.names文件，并放在``python/models`` 目录下。

步骤2 转换模型格式
进入到``python/models`` 目录下，将onnx格式模型转换为om格式模型。

       atc --framework=5 --model=CenterNet.onnx  --output=CenterNet_pre_post --input_format=NCHW --input_shape="actual_input:1,3,512,512" --log=info --soc_version=Ascend310P3 --insert_op_conf=./aipp-configs/aipp_bgr.config

若终端输出：
```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

表示命令执行成功。


## 4. 编译与运行

### 4.1 业务流程加图像预处理

**步骤1** 在项目后处理目录执行命令：

```
bash build.sh  
```

**步骤2** 放入待测图片。将一张图片放在路径``python/test_img``下，命名为 test.jpg（python/test_img目录需用户自行创建）。

**步骤3** 图片检测。在项目路径``python/Main``下运行命令：

```
python3 pre_post.py
```
**步骤4** 查看结果

命令执行成功后在目录``python/test_img``下生成检测结果文件 pre_post.jpg，可打开该文件观察检测结果。