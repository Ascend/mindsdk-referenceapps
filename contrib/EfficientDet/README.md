# EfficientDet 目标检测
## 1. 介绍

### 1.1 简介
EfficientDet 目标检测后处理插件基于 MindXSDK 开发，对图片中的不同类目标进行检测，将检测得到的不同类的目标用不同颜色的矩形框标记。输入一幅图像，可以检测得到图像中大部分类别目标的位置。本方案使用在 COCO2017 数据集上训练得到的 EfficientDet 模型进行目标检测，数据集中共包含 90 个目标类，包括行人、自行车、公共汽车、手机、沙发、猫、狗等，可以对不同类别、不同角度、不同密集程度的目标进行检测。

### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。


### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称 | 版本   |
| -------- | ------ |
| webcolors| 1.11.1 |

### 1.5 代码目录结构与说明

本工程名称为 EfficientDet，工程目录如下所示：
```
.
├── build.sh
├── images
│   ├── DetectionPipeline.png
│   ├── EvaluateInfo.png
│   ├── EvaluateInfoPrevious.png
│   └── VersionError.png
├── postprocess
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── EfficientdetPostProcess.cpp
│   └── EfficientdetPostProcess.h
├── python
│   ├── evaluate.py
│   ├── main.py
│   ├── models
│   │   ├── aipp-configs
│   │   │   ├── insert_op_d0.cfg
│   │   │   ├── insert_op_d0_previous_version.cfg
│   │   │   ├── insert_op_d1.cfg
│   │   │   ├── insert_op_d2.cfg
│   │   │   ├── insert_op_d3.cfg
│   │   │   ├── insert_op_d4.cfg
│   │   │   ├── insert_op_d5.cfg
│   │   │   └── insert_op_d6.cfg
│   │   ├── coco.names
│   │   ├── conversion-scripts
│   │   │   ├── model_conversion_d0_previous_version.sh
│   │   │   ├── model_conversion_d0.sh
│   │   │   ├── model_conversion_d1.sh
│   │   │   ├── model_conversion_d2.sh
│   │   │   ├── model_conversion_d3.sh
│   │   │   ├── model_conversion_d4.sh
│   │   │   ├── model_conversion_d5.sh
│   │   │   └── model_conversion_d6.sh
│   │   ├── efficient-det.cfg
│   │   ├── efficient-det-eval.cfg
│   │   └── onnx-models
│   └── pipeline
│       ├── EfficientDet-d0.pipeline
│       ├── EfficientDet-d0-previous-version.pipeline
│       ├── EfficientDet-d1.pipeline
│       ├── EfficientDet-d2.pipeline
│       ├── EfficientDet-d3.pipeline
│       ├── EfficientDet-d4.pipeline
│       ├── EfficientDet-d5.pipeline
│       └── EfficientDet-d6.pipeline
└── README.md

```

## 2. 设置环境变量

在执行后续步骤前，需要设置环境变量：


```bash
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
```
mxVision-path: mxVision安装路径

ascend-toolkit-path: CANN安装路径


## 3. 准备模型

**步骤1:**
本项目中采用的模型是 EfficientDet 模型，参考实现代码：https://github.com/zylo117/Yet-Another-EfficientDet-Pytorch， 选用的模型是该 pytorch 项目中提供的模型 efficientdet-d0.pth，本项目运行前需要将需下载相对应的onnx模型，模型链接：https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/EfficientDet/models.zip。

**步骤2:**
从上述 onnx 模型下载链接中下载 onnx 模型 simplified-efficient-det-d0-mindxsdk-order.onnx 和 simplified-efficient-det-d6-mindxsdk-order.onnx 至 ``python/models/onnx-models`` 文件夹下。

**步骤3:**
进入 ``python/models/conversion-scripts`` 文件夹下依次执行命令：
```
bash model_conversion_d0.sh
bash model_conversion_d6.sh
```
执行后会在当前文件夹下生成项目需要的模型文件 efficient-det-d0-mindxsdk-order.om 和 efficient-det-d6-mindxsdk-order.om，转换成功的终端输出为：
```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.

```
表示命令执行成功。


## 4. 编译与运行

**步骤1** 按照第 2 小节 **环境依赖** 中的步骤设置环境变量。

**步骤2** 如果使用的是上述链接提供的 onnx 模型或者 om 模型，按照第 3 小节 **模型转换** 中的步骤获得 om 模型文件，放置在 ``python/models`` 目录下。

**步骤3** 编译。在项目目录下执行bash build.sh命令。

此时会生成postprocess/build/libefficientdetpostprocess.so 文件

**步骤4** 图片检测。将一张图片放在项目目录下，命名为 img.jpg，在该图片上进行检测
>**如提示so库异常，则需要从 ```main.py``` 中找到使用的 pipeline 文件路径，将其中 mxpi_objectpostprocessor0 插件的 postProcessLibPath 属性值改为具体路径值**

执行命令：
```
cd python
python3 main.py
```

**步骤5**查看结果 **步骤4**执行成功后在当前目录下生成检测结果文件 img_detect_result.jpg，查看结果文件验证检测结果。



## 5 常见问题


### 5.1 MindXSDK 版本问题

**问题描述：**

要求 MindXSDK 的版本至少为 2.0.2.1，否则出现 ImageResize 插件不能设置 "cvProcessor": "opencv" 属性问题，如下图所示：
<center>
    <img src="./images/VersionError.png">
    <br>
</center>

**解决方案：**

确保 MindXSDK 版本至少为 2.0.2.1。

### 5.2 未修改 pipeline 文件中的 ${MX_SDK_HOME} 值为具体值
运行检测 demo 和评测时都需要将对应 pipeline 文件中 mxpi_objectpostprocessor0 插件的 postProcessLibPath 属性值中的 ${MX_SDK_HOME} 值改为具体路径值，否则会报错，如下图所示：
<center>
    <img src="./images/MindXSDKValueError.png">
    <br>
</center>

**解决方案：**

检测 main.py 和 evaluate.py 里所用的 pipeline 文件, 将文件中 mxpi_objectpostprocessor0 插件的 postProcessLibPath 属性值中的 ${MX_SDK_HOME} 值改为具体路径值。

### 5.3 未修改模型文件或生成so的权限
SDK对运行库so和模型文件有要求，如出现以下报错提示请参考FASQ中相关内容使用chmod指定权限640
```shell
Check Owner permission failed: Current permission is 7, but required no greater than 6.
```

**解决方案：**  
cd到对应目录并指定相关文件权限为640