# 基于mxBase的高速公路车辆火灾识别(C++)

## 1 介绍

### 1.1 简介
高速公路车辆火灾识别基于 mxVision SDK 开发，在 Atlas 300V、Atlas 300V Pro 上进行目标检测。项目主要流程为：通过ffmpeg打开本地视频文件、模拟视频流，然后进行视频解码，解码结果经过模型推理进行火灾和烟雾检测，如果检测到烟雾和火灾则在日志中进行告警。解码后的视频图像会编码保存至指定位置。

### 1.2 支持的产品
支持Atlas 300V和Atlas 300V Pro。

### 1.3 支持的版本

  | MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- | 
  | 6.0.RC2 | 8.0.RC2   |  24.1.RC2  | 
  | 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖

本项目除了依赖昇腾Driver、Firmware、CANN和MxVision及其要求的配套软件外，还需额外依赖以下软件：

| 软件名称   | 版本   |
|--------| ------ |
| ffmpeg | 3.4.11 |

### 1.5 代码目录结构说明

本项目目录如下图所示：

```
├── aipp_yolov5.cfg
├── BlockingQueue
│  └── BlockingQueue.h
├── ConfigParser    # 配置文件解析类
│   ├── ConfigParser.cpp
│   └── ConfigParser.h
├── FrameAnalyzer       # 视频帧分析类
│   ├── FrameAnalyzer.cpp
│   └── FrameAnalyzer.h
├── main.cpp
├── README.md
├── CMakeLists.txt
├── setup.config
└── VideoDecoder     # 视频解码类
    ├── VideoDecoder.cpp
    └── VideoDecoder.h
```
## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：



```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
export FFMPEG_PATH=${ffmpeg-path}
export LD_LIBRARY_PATH=${ffmpeg-lib-path}:$LD_LIBRARY_PATH
# mxVision: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
# ffmpeg-path: ffmpeg安装路径，通常为/usr/local/ffmpeg
# ffmpeg-lib-path: ffmpeg的lib库安装路径，通常为/usr/local/ffmpeg/lib
```
## 3 准备模型
步骤1 下载模型相关文件 

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/FireDetection/models.zip)下载并解压得到firedetection.onnx文件，并放在项目根目录下。

步骤2 转换模型格式
进入到项目根目录下，将onnx格式模型转换为om格式模型(--soc_version的参数需根据实际NPU型号设置，Atlas 300V和Atlas 300V Pro设备下该参数为Ascend310P3)。

       atc --model=./firedetection.onnx --framework=5 --output=./firedetection --input_format=NCHW --input_shape="images:1,3,640,640"  --out_nodes="Transpose_217:0;Transpose_233:0;Transpose_249:0"  --enable_small_channel=1 --insert_op_conf=./aipp_yolov5.cfg --soc_version=Ascend310P3 --log=info

##  4 编译与运行
步骤1 编译

- 在项目根目录创建cmakeDir目录并进入该目录。
- 执行cmake.. && make编译项目。编译的二进制文件main保存在项目根目录下。

步骤2 设置配置项

在setup.config文件中设置配置项，配置项含义如下表所示：

|      配置项字段      | 配置项含义           |
|:---------------:|-----------------|
|    videoPath    | 用于火灾识别的视频文件路径   |
|    modelPath    | om模型的路径         |
|    deviceId     | 运行服务时使用的NPU设备编号 |
| skipFrameNumber | 指定两次推理的帧间隔数量    |
| videoSavedPath  | 指定编码后视频保存的文件路径  |
|      width      | 用于火灾识别的视频文件的宽度  |
|     height      | 用于火灾识别的视频文件的高度  |


*deviceId需为整数，取值范围为[0, NPU设备个数-1]，`npu-smi info` 命令可以查看NPU设备个数；skipFrameNumber需为整数，建议根据实际业务需求设置，推荐设置为3；width和height需为整数，取值范围为[128, 4096]；videoPath所指定的视频文件需为H264编码；videoSavedPath所指定的文件每次服务启动时会被覆盖重写。

步骤3 运行高速公路火灾识别服务

进入项目根目录，执行如下指令：

      ./main
火灾检测结果在标准输出中体现；编码视频文件保存在配置文件指定的路径下。

步骤4 停止高速公路火灾识别服务
停止服务有如下两种方式：

- 视频文件分析完毕后可自动停止服务。
- 命令行输入Ctrl+C组合键可手动停止服务。

步骤5 查看结果

用户可在标准输出中查看火灾检测结果，在配置项videoSavedPath所指定的文件中查看视频编码结果。

##  5 常见问题
### 5.1 模型加载问题
问题描述：模型路径正常，但是运行时提示模型加载错误。

解决方案：排查模型路径中是否包含加号等特殊符号。如有，则需要将特殊符号去掉。

