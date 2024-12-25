# MxBase异步目标检测

## 1 介绍

### 1.1 简介

异步目标检测样例基于Vision SDK进行开发，调用异步推理接口，对图像中的不同类目标进行检测，得到图像中大部分目标的类别和位置。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、Atlas 300V pro。

### 1.3 支持的版本

本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：

| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 代码目录结构说明

```
|-- AsyncInfer
|   |-- images          // 存放测试图片，需用户自己创建目录
|   |-- model           // 存放相关配置文件以及om模型
|       |-- yolov3
|           |-- coco.names
|           |-- yolov3_tf_bs1_fp16.cfg
|-- build.sh
|-- main.cpp
|-- CMakeLists.txt
|-- README.MD
```

### 1.5 相关约束

本项目支持通用场景下的jpg图片目标检测，支持图片格式为jpg、jpeg，并且图片的像素排布格式需为“RGB_888”。

## 2 设置环境变量

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh       # sdk安装路径，根据实际安装路径修改
```

## 3 准备模型

**步骤1：** 模型下载。本项目使用YoloV3模型，[模型下载链接](http://ascend-repo-modelzoo.obs.cn-east-2.myhuaweicloud.com/c-version/YoloV3_for_TensorFlow/zh/1.6/m/YOLOv3_TensorFlow_1.6_model.zip )

**步骤2：** 模型下载解压后，将`single/om/yolov3_tf_aipp.om`文件放到`model/yolov3/`文件夹下。

## 4 编译与运行

**步骤1：** 准备测试图片。将图片放在根目录的`images/`下，需为“RGB_888”的jpg图片。

**步骤2：** 编译。在项目根目录执行命令`bash build.sh`，会生成可执行文件`sample`。

**步骤3：** 运行。在项目根目录执行命令`./sample`。

**步骤4：** 查看结果。在运行时，会有相应的打屏日志，并展示图片的目标检测结果。

## 5 常见问题

### 5.1 无法下载模型

**问题描述：**

点击模型下载链接后，无法下载模型文件。

**解决方案：**

模型下载链接可能会被浏览器识别为不安全的下载，关闭拦截后重试或者尝试更换浏览器。

### 5.2 deviceId报错

**问题描述：**

运行过程中报deviceId相关错误。

**解决方案：**

将`main.cpp`文件中第27行的`g_deviceId`字段值替换为可用的deviceId值。

### 5.3 图片格式转换配置失败

**问题描述：**

运行过程中报错`Get convert format config failed. Current format is xx`。

**解决方案：**

不支持当前图片的像素格式，需要更换为像素格式是“RGB_888”的图片，或自行将当前图片转为"RGB_888"的像素格式。

### 5.4 报错图片格式不可用

**问题描述：**

运行过程中报错`Failed to check header bits of the image, only JPEG/PNG format is available`。

**解决方案：**

需要将`images`文件夹下不符合格式要求的文件删掉。