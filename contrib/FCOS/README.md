# FCOS

## 1 介绍

### 1.1 简介

本开发项目演示FCOS模型实现目标检测。本项目使用的模型是FCOS目标检测模型这个模型是一个无anchor检测器。FCOS直接把预测特征图上的每个位置$(x,y)$当作训练样本，若这个位置在某个ground truth box的内部，则视为正样本，该位置的类别标签$c$对应这个box的类别，反之则视为负样本。这个网络的输出为目标框的左上角坐标、右下角坐标、类别和置信度。

本系统基于Vision SDK进行开发，主要实现目标检测。待检测的图片中物体不能被遮挡太严重，并且物体要完全出现在图片中。图片亮度不能过低。输入一张图片，最后会输出图片中能检测到的物体信息、并输出可视化结果图片。

本项目实现对输入的图片进行目标检测，整体流程如下：

![avatar](./image/image1.png)



### 1.2 支持的产品

本项目以昇腾x86_64 Atlas 300l (型号3010)和arm Atlas 300l (型号3000)为主要的硬件平台。

### 1.3 支持的版本

| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0     | 7.0.0     |  23.0.0    |

### 1.4 三方依赖

本项目除了依赖昇腾Driver、Firmware、CANN和Vision SDK及其要求的配套软件外，还需额外依赖以下软件：

| 软件名称          | 版本       |
|---------------|----------|
| opencv-python | 4.6.0.66 |
| numpy         | 1.23.2   |
| mmcv          | 1.7.0    |
| webcolors     | 1.13     |

### 1.5 代码目录结构说明

本项目名为FCOS目标检测，项目的目录如下所示：

```
├── colorlist.txt
├── image
│   ├── image1.png
│   └── image2.png
├── main.py
├── models
│   ├── coco.names
│   └── Fcos_tf_bs.cfg
├── pipeline
│   └── FCOSdetection.pipeline
├── plugin
│   └── FCOSPostprocess
│       ├── build.sh
│       ├── CMakeLists.txt
│       ├── FCOSDetectionPostProcess.cpp
│       └── FCOSDetectionPostProcess.h
└── README.md
```

## 2 设置环境变量
在项目开始运行前需要设置环境变量：
```bash
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
# mxVision-path: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
```

## 3 准备模型

**步骤1：** 下载模型相关文件

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/Fcos/ATC%20Fcos.zip)下载并解压，在解压后的model目录下得到fcos.onnx文件，并放在项目根目录的``models`` 目录下。


**步骤2：** 转换模型格式

放在项目根目录的``models`` 目录下，执行如下命令：
```
atc --model=fcos.onnx --framework=5 --soc_version=Ascend310 --input_format=NCHW --input_shape="input:1,3,800,1333" --output=fcos_bs1 --precision_mode=allow_fp32_to_fp16
```

执行完该命令之后，会在models文件夹下生成fcos_bs1.om模型，并且转换成功之后会在终端输出：

```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```



## 4 编译与运行

**步骤1：** 准备一张jpg图片放到项目目录下，然后修改main.py


第**120**行 `IMAGENAME = '{image path}'`中的{image path}替换为实际的jpg图片路径。


**步骤2：** 编译

进入项目根目录的plugin/FCOSPostprocess目录，在该目录下运行下列命令：

```
bash build.sh
```


**步骤3：** 运行

在项目根目录下执行以下命令：

```
python3 main.py
```

**步骤4：** 查看结果

标准输出中会打印目标检测信息，项目根目录下result.jpg图片会保存可视化检测结果。

