# 波比跳运动检测

## 1、 介绍

### 1.1 简介

基于昇腾硬件和MindX SDK 实现波比跳运动检，并将检测结果保存成视频。
主要流程：通过 live555 服务器进行拉流输入视频，然后进行视频解码将 H.264 格式的视频解码为图片，图片缩放后经过模型推理进行波比跳检测，识别结果经过后处理后利用 cv 可视化识别框，以视频的形式输出，同时生成文本文件记录视频中完成的波比跳个数。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称      | 版本             |
| ------------- | ---------------- |
| scipy         | 1.13.1           |
| opencv-python | 4.10.0.84       |
| google       | 3.0.0           |
| protobuf       | 3.19.0           |
| numpy         | 1.24.0           |
| live555  | 1.09  | 实现视频转rstp进行推流         | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) |

### 1.4 代码目录结构与说明

本 Sample 工程名称为 **Burpee_Detection**，工程目录如下图所示：

```
├── model
│   ├── atc.sh                   //atc运行脚本
├── pipeline
│   └── burpee_detection_v.pipeline          //视频流识别使用的pipeline文件
├── Video_burpee_detection
│   ├── video_main.py            //识别，保存结果，并进行性能测试
|   └── run.sh                   //运行脚本
└── README.md
```

## 2、 设置环境变量

在编译运行项目前，需要设置环境变量：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```

## 3、 准备模型

**步骤1**: onnx模型下载

[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/Burpee/models%E5%92%8C%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6.zip)

**步骤2**：模型转换

将步骤1中下载的models.zpi压缩包放到项目目录的modle文件夹并解压。拷贝其中的burpee_detection.onnx，yolov5.cfg，yolov5.names文件到modle文件夹。执行以下命令：

```bash
bash ./atc.sh
```
执行完模型转换脚本后，会在model文件夹生成相应的burpee_detection.om模型文件：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

## 4、 运行

**步骤1**：安装live555并创建视频流 

按照 [Live555离线视频转RTSP说明文档](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/参考资料/Live555离线视频转RTSP说明文档.md)，使用h264视频创建rtsp视频流。

**步骤2**：修改流程编排文件
进入pipeline文件夹
把burpee_detection_v.pipeline文件中的流地址替换为实际的地址：

```bash
#第8行 "rtspUrl": "rtsp://xxx.xxx.x.x:xxxx/burpee_detection.264",
```


**步骤3**：运行检测程序
进入Video_burpee_detection文件夹，执行以下命令：
```bash
python3 video_main.py
```
注意：检测程序不会自动停止，需要执行ctrl+c键盘命令停止程序

**步骤3**：查看结果

运行可视化结果会以`video_result.mp4`视频形式保存在`Burpee_Detection/Video_burpee_detection`目录下
波比跳识别个数会以`result.txt`文件形式保存在`Burpee_Detection/Video_burpee_detection`目录下
检测过程中的帧图片会保存在`Burpee_Detection/Video_burpee_detection/result_pic`目录下



 