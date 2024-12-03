# FCOS

## 1 介绍

### 1.1 简介

本开发项目演示FCOS模型实现目标检测。本系统基于mxVision SDK进行开发，主要实现目标检测。待检测的图片中物体不能被遮挡太严重，并且物体要完全出现在图片中。图片亮度不能过低。输入一张图片，最后会输出图片中能检测到的物体。项目主要流程：

1.环境搭建；
2.模型转换；
3.生成后处理插件；
4.进行精度、性能对比。

### 1.2 支持的产品

本项目以昇腾x86_64 Atlas 300l (型号3010)和arm Atlas 300l (型号3000)为主要的硬件平台。

### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0     | 7.0.0     |  23.0.0    |

### 1.4 三方依赖

项目运行过程中涉及到的第三方软件依赖如下表所示：

| 软件名称     | 说明                 | 使用教程                                                  |
| ----------- | -------------------- | --------------------------------------------------------- |
| pycocotools | 用于实现代码测评     | [点击打开链接](https://cocodataset.org/)                  |
| mmdetection | 用于实现模型精度评估 | [点击打开链接](https://github.com/open-mmlab/mmdetection) |
| mmcv        | 用于实现图片前处理   | [点击打开链接](https://github.com/open-mmlab/mmcv)        |

安装python COCO测评工具,mmcv和mmdetection。执行命令：

```
pip3 install pycocotools
pip3 install mmcv-full
pip3 install mmdet
```

### 1.5 代码目录结构说明

本项目名为FCOS目标检测，项目的目录如下所示：

```
|- models
|	|- fcos.onnx				//onnx模型
|	|_ Fcos_tf_bs.cfg
|- pipeline
|	|_ FCOSdetection.pipeline
|- plugin
|	|_FCOSPostprocess
|		|- CMakeLists.txt
|		|- FCOSDetectionPostProcess.cpp
|		|- FCOSDetectionPostProcess.h
|		|_ build.sh
|- image
|   |- image1.png
|   |_ image2.png
|- build.sh
|- evaluate.py
|- colorlist.txt
|_ main.py
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

本项目使用的模型是FCOS目标检测模型这个模型是一个无anchor检测器。FCOS直接把预测特征图上的每个位置$(x,y)$当作训练样本，若这个位置在某个ground truth box的内部，则视为正样本，该位置的类别标签$c$对应这个box的类别，反之则视为负样本。这个网络的输出为目标框的左上角坐标、右下角坐标、类别和置信度。本项目的onnx模型可以直接[下载](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/Fcos/ATC%20Fcos.zip)。下载后，里面自带的om模型是可以直接使用的，或者自行使用ATC工具将onnx模型转换成为om模型，模型转换工具的使用说明参考[链接](https://gitee.com/ascend/docs-openmind/blob/master/guide/mindx/sdk/tutorials/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99.md)。

模型转换步骤如下：

**步骤1：**
从下载链接处下载onnx模型至FCOS/models文件夹下。

**步骤2：**
模型转换语句如下：

```
atc --model=fcos.onnx --framework=5 --soc_version=Ascend310 --input_format=NCHW --input_shape="input:1,3,800,1333" --output=fcos_bs1 --precision_mode=allow_fp32_to_fp16
```

**步骤3：**
执行完该命令之后，会在models文件夹下生成.om模型，并且转换成功之后会在终端输出：

```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```



## 4 编译与运行

**步骤1：**

准备一张待检测图片，并上传到FCOS文件夹下。然后修改main.py文件里面的图片路径为待检测的图片路径。并且从https://github.com/pjreddie/darknet/blob/master/data/coco.names   里面下载coco.names文件，并且将这个文件存放到models文件夹下。并且修改main.py里IMAGENAME为图片的路径：
```python
IMAGENAME = '{image path}'  // 120行
```
**步骤2：**

进入FCOS/plugin/FCOSPostprocess目录，在该目录下运行下列命令：

```
bash build.sh
```
这个后处理插件即可以使用。

**步骤3：**

在FCOS目录下执行命令：

```
python3 main.py
```

**步骤4：查看结果**

最后生成的结果会在FCOS文件夹目录下result.jpg图片中。


## 5 常见问题
### 5.1 模型路径配置问题：
问题描述：
检测过程中用到的模型以及模型后处理插件需配置路径属性。

后处理插件以及模型推理插件配置例子：

```json
// 模型推理插件
            "mxpi_tensorinfer0": {
                "props": {
                    "dataSource": "mxpi_imageresize0",
                    "modelPath": "./models/fcos_bs1.om"
                },
                "factory": "mxpi_tensorinfer",
                "next": "mxpi_objectpostprocessor0"
            },
// 模型后处理插件
            "mxpi_objectpostprocessor0":{
                "props": {
                    "dataSource" : "mxpi_tensorinfer0",
                    "postProcessConfigPath": "./models/Fcos_tf_bs.cfg",
                    "postProcessLibPath": "libFCOSDetectionPostProcess.so"
                },
                "factory": "mxpi_objectpostprocessor",
                "next": "mxpi_dataserialize0"
            },
```