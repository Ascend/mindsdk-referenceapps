# 基于mxBase的高速公路车辆火灾识别(Python)

## 1 介绍

### 1.1 简介
高速公路车辆火灾识别基于mxVision SDK 开发，在 Atlas 300V、Atlas 300V Pro 上进行目标检测。项目主要流程为：通过av模块打开本地视频文件、模拟视频流，然后进行视频解码，解码结果经过模型推理进行火灾和烟雾检测，如果检测到烟雾和火灾则在日志中进行告警。解码后的视频图像会再次编码保存至指定位置。

### 1.2 支持的产品
支持Atlas 300V和Atlas 300V Pro。

### 1.3 支持的版本

  | MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- | 
  | 6.0.RC2 | 8.0.RC2   |  24.1.RC2  | 

### 1.4 三方依赖
本项目除了依赖昇腾Driver、Firmware、CANN和mxVision及其要求的配套软件外，还需额外依赖以下python软件：

| 软件名称 | 版本   |
| -------- | ------ |
| av | 10.0.0 |
| numpy | 1.23.5 |

### 1.5 代码目录结构说明

本项目目录如下图所示：

```
├── frame_analyzer.py  // 视频帧分析
├── infer_config.json  // 服务配置
├── aipp_yolov5.cfg
├── utils.py  
├── main.py  
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
### 步骤1 下载模型相关文件
根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/FireDetection/models.zip)下载并解压得到firedetection.onnx文件。

###  步骤2 转换模型格式

将onnx格式模型转换为om格式模型(--soc_version的参数需根据实际NPU型号设置，Atlas 300V和Atlas 300V Pro设备下该参数为Ascend310P3)。

       atc --model=./firedetection.onnx --framework=5 --output=./firedetection --input_format=NCHW --input_shape="images:1,3,640,640"  --out_nodes="Transpose_217:0;Transpose_233:0;Transpose_249:0"  --enable_small_channel=1 --insert_op_conf=./aipp_yolov5.cfg --soc_version=Ascend310P3 --log=info

##  4 运行
### 步骤1 设置配置项
 设置高速公路车辆火灾识别服务配置（修改infer_config.json文件） ，支持的配置项如下所示 ：

|       配置项字段       | 配置项含义           |
|:-----------------:|-----------------|
|    video_path     | 用于火灾识别的视频文件路径   |
|    model_path     | om模型的路径         |
|     device_id     | 运行服务时使用的NPU设备编号 |
| skip_frame_number | 指定两次推理的帧间隔数量    |
| video_saved_path  | 指定编码后视频保存的文件路径  |
|       width       | 用于火灾识别的视频文件的宽度  |
|      height       | 用于火灾识别的视频文件的高度  |


*device_id需为整数，取值范围为[0, NPU设备个数-1]，`npu-smi info` 命令可以查看NPU设备个数；skip_frame_number需为整数，建议根据实际业务需求设置，推荐设置为3；width和height需为整数，取值范围为[128, 4096]；video_path所指定的视频文件需为H264编码；video_saved_path所指定的文件每次服务启动时会被覆盖重写。

### 步骤2 启动火灾检测服务

      python3 main.py
### 步骤3 停止高速公路火灾识别服务
停止服务有如下两种方式：

- 视频文件分析完毕后可自动停止服务。 
- 命令行输入Ctrl+C组合键可手动停止服务。

###  步骤4 查看结果

用户可在标准输出中查看火灾检测结果，在配置项video_saved_path所指定的文件中查看视频编码结果。

## 5 常见问题

### 5.1 获取视频流问题
问题描述：获取视频流失败。

  解决方案：检查av库的版本是否为10.0.0。
### 5.2 模型加载失败问题
问题描述：模型路径正常，但是运行时提示模型加载错误。

  解决方案：排查模型路径中是否包含加号等特殊符号。如有，则需要将特殊符号去掉。
  
### 5.3 模型转换失败问题
问题描述：模型转换失败，提示模型路径包含非法字符或提示NumPy版本不匹配。

解决方案：1.若提示模型路径包含非法字符，则检查模型路径中是否包含非法字符（如+、-等特殊符号）、修改相关目录名或文件名，从而使得模型路径中不包含非法字符；
2.若提示NumPy版本不匹配，则检查NumPy版本是否过高，建议安装1.23.5版本的NumPy供模型转换工具调用。