# MxBase多路视频目标检测

## 1 介绍

### 1.1 简介

多路视频目标检测，实现同时对两路本地视频或RTSP视频流（H264）进行yolov3目标检测，生成可视化结果（可选）。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、Atlas 300V pro。

### 1.3 支持的版本

本样例配套的VisionSDK版本、CANN版本、Driver/Firmware版本如下所示：

| VisionSDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 依赖软件 | 版本       | 说明                           | 使用教程                                                     |
| -------- | ---------- | ------------------------------ | ------------------------------------------------------------ |
| live555  | 1.10       | 实现视频转rstp进行推流         | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) |
| ffmpeg   | 4.2.1 | 实现mp4格式视频转为264格式视频 | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/pc%E7%AB%AFffmpeg%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md#https://ffmpeg.org/download.html) |

注：live555和ffmpeg需要用户到相关网址下载源码编译安装。

### 1.5 代码目录结构说明

```
.
|-------- BlockingQueue
|           |---- BlockingQueue.h                   // 阻塞队列 (视频帧缓存容器)
|-------- test                                      // 需用户自己创建目录
|           |---- xxx1.264                          // 多路视频测试数据1 (本地测试自行准备)
|           |---- xxx2.264                          // 多路视频测试数据2 (本地测试自行准备)
|-------- ImageResizer
|           |---- ImageResizer.cpp                  // 图片缩放.cpp
|           |---- ImageResizer.h                    // 图片缩放.h
|-------- model
|           |---- aipp_yolov3_416_416.aippconfig    // yolov3 模型转换配置文件
|           |---- coco.names                        // yolov3 标签文件
|-------- MultiChannelVideoReasoner
|           |---- MultiChannelVideoReasoner.cpp     // 多路视频推理业务逻辑封装.cpp
|           |---- MultiChannelVideoReasoner.h       // 多路视频推理业务逻辑封装.h
|-------- result                                    // 视频推理结果存放处，程序会自动生成
|-------- StreamPuller
|           |---- StreamPuller.cpp                  // 视频拉流.cpp
|           |---- StreamPuller.h                    // 视频拉流.h
|-------- Util
|           |---- PerformanceMonitor
|                   |---- PerformanceMonitor.cpp    // 性能管理.cpp
|                   |---- PerformanceMonitor.h      // 性能管理.h
|           |---- Util.cpp                          // 工具类.cpp
|           |---- Util.h                            // 工具类.h
|-------- VideoDecoder
|           |---- VideoDecoder.cpp                  // 视频解码.cpp
|           |---- VideoDecoder.h                    // 视频解码.h
|-------- YoloDetector
|           |---- YoloDetector.cpp                  // Yolo检测.cpp
|           |---- YoloDetector.h                    // Yolo检测.h
|-------- build.sh                                  // 样例编译脚本
|-------- CMakeLists.txt                            // CMake配置
|-------- main.cpp                                  // 多路视频推理测试样例
|-------- README.md                                 // ReadMe
|-------- run.sh                                    // 样例运行脚本

```

## 2 设置环境变量

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh       # sdk安装路径，根据实际安装路径修改
export FFMPEG_HOME=/usr/local/ffmpeg            # ffmpeg默认安装路径，根据实际安装路径修改
```

## 3 准备模型

**步骤1：** 下载YOLOv3模型 。[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ActionRecognition/ATC%20YOLOv3%28FP16%29%20from%20TensorFlow%20-%20Ascend310.zip)

**步骤2：** 将获取到的YOLOv3模型的pb文件存放至`model/`文件夹下。

**步骤3：** 模型转换。在`model/`文件夹下，执行以下命令：

```bash
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
```
执行完模型转换脚本后，会生成相应的`.om`模型文件。执行后若终端输出如下命令，则表示命令执行成功：

```bash
ATC start working now, please wait for a moment.

ATC run success, welcome to the next use.
```

## 4 编译与运行


**步骤1：** 准备测试视频。视频流格式为264，放入`test/`文件夹下。

**步骤2：** 在`test/`文件夹下拉起Live555服务。[Live555拉流教程](../../docs/参考资料/Live555离线视频转RTSP说明文档.md)

**步骤3：** 修改`main.cpp`文件中的配置：

①：将文件中第47、48行的`${rtsp流地址1}`、`${rtsp流地址2}`字段值替换为可用的 rtsp 流源地址（目前只支持264格式的rtsp流，例："rtsp://xxx.xxx.xxx.xxx:xxx/xxx.264", 其中xxx.xxx.xxx.xxx:xxx为ip和端口号，端口号需同Live555服务的起流端口号一致，xxx.264为待测视频流文件名）；

```c++
rtspList.emplace_back("${rtsp流地址1}");
rtspList.emplace_back("${rtsp流地址2}");
```

②：将文件中第96行的`${MindXSDK安装路径}`字段值替换为实际使用的安装路径。

```c++
APP_ERROR ret = configUtil.LoadConfiguration("${MX_SDK_HOME}/config/logging.conf", configData, MxBase::ConfigMode::CONFIGFILE);
```

**步骤4：** 编译。在项目根目录下，执行命令`bash build.sh`，编译成功会在根目录下生成`multiChannelVideoReasoner`可执行文件。

**步骤5：** 运行。在项目根目录下，执行命令`bash run.sh`。

**步骤6：** 查看结果。在执行`bash run.sh`后会有打屏日志显示检测结果，同时会将目标检测结果保存在工程目录下`result`中。手动执行 `ctrl + C` 结束程序。
