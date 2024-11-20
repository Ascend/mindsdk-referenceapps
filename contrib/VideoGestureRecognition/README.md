# 基于MxBase的视频手势识别运行

## 1 介绍

### 1.1 简介
手势识别是指对视频中出现的手势进行分类，实现对本地（H264）进行手势识别并分类，生成可视化结果。
使用测试视频中的手势尺寸大致应为视频大小的二分之一，同时应当符合国际标准，背景要单一，手势要清晰，光线充足；视频切勿有遮挡，不清晰等情况。

### 1.2 支持的产品

本项目支持昇腾Atlas 500 A2

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0     | 7.0.0     |  23.0.0    |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 依赖软件 | 版本       | 说明                           | 使用教程                                                     |
| -------- | ---------- | ------------------------------ | ------------------------------------------------------------ |
| live555  | 1.10       | 实现视频转rstp进行推流         | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) |
| ffmpeg   | 4.2.1 | 实现mp4格式视频转为264格式视频 | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/pc%E7%AB%AFffmpeg%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md#https://ffmpeg.org/download.html) |

**注意：**

第三方库默认全部安装到/usr/local/下面，全部安装完成后，请设置环境变量
```bash
export PATH=/usr/local/ffmpeg/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/ffmpeg/lib:$LD_LIBRARY_PATH
```

### 1.5 代码目录结构说明
```
.
|-------- BlockingQueue
|           |---- BlockingQueue.h                   // 阻塞队列 (视频帧缓存容器)
|-------- ImageResizer
|           |---- ImageResizer.cpp                  // 图片缩放.cpp
|           |---- ImageResizer.h                    // 图片缩放.h
|-------- FrameSkippingSampling
|           |---- FrameSkippingSampling.cpp         // 跳帧采样.cpp
|           |---- FrameSkippingSampling.h           // 跳帧采样.h
|-------- model
|           |---- resnet18.cfg                      // Resnet18 模型转换配置文件
|           |---- resnet18.names                    // Resnet18 标签文件
|-------- VideoGestureReasoner
|           |---- VideoGestureReasoner.cpp          // 视频手势推理业务逻辑封装.cpp
|           |---- VideoGestureReasoner.h            // 视频手势推理业务逻辑封装.h
|-------- result                                    // 推理结果存放处（图片的形式）
|-------- StreamPuller
|           |---- StreamPuller.cpp                  // 视频拉流.cpp
|           |---- StreamPuller.h                    // 视频拉流.h
|-------- Util
|           |---- Util.cpp                          // 工具类.cpp
|           |---- Util.h                            // 工具类.h
|-------- VideoDecoder
|           |---- VideoDecoder.cpp                  // 视频解码.cpp
|           |---- VideoDecoder.h                    // 视频解码.h
|-------- ResnetDetector
|           |---- ResnetDetector.cpp                  // Resnet识别.cpp
|           |---- ResnetDetector.h                    // Resnet识别.h
|-------- build.sh                                  // 样例编译脚本
|-------- CMakeLists.txt                            // CMake配置
|-------- main.cpp                                  // 视频手势识别测试样例
|-------- README.md                                 // ReadMe
|-------- run.sh                                    // 样例运行脚本

```

## 2 设置环境变量

```
# 请确认install_path路径是否正确
# Set environment PATH (Please confirm that the install_path is correct).

export install_path=/usr/local/Ascend/ascend-toolkit/latest
export PATH=/usr/local/python3.9.2/bin:${install_path}/atc/ccec_compiler/bin:${install_path}/atc/bin:$PATH
export PYTHONPATH=${install_path}/atc/python/site-packages:${install_path}/atc/python/site-packages/auto_tune.egg/auto_tune:${install_path}/atc/python/site-packages/schedule_search.egg
export LD_LIBRARY_PATH=${install_path}/atc/lib64:$LD_LIBRARY_PATH
export ASCEND_OPP_PATH=${install_path}/opp

export MX_SDK_HOME=${SDK安装路径}
export FFMPEG_PATH=${FFMPEG安装路径}
LD_LIBRARY_PATH=${MX_SDK_HOME}/lib:${MX_SDK_HOME}/opensource/lib:${MX_SDK_HOME}/opensource/lib64:${FFMPEG_PATH}/lib:/usr/local/Ascend/ascend-toolkit/latest/acllib/lib64:/usr/local/Ascend/driver/lib64/
export GST_PLUGIN_SCANNER=${MX_SDK_HOME}/opensource/libexec/gstreamer-1.0/gst-plugin-scanner
export GST_PLUGIN_PATH=${MX_SDK_HOME}/opensource/lib/gstreamer-1.0:${MX_SDK_HOME}/lib/plugins
```

### 3 准备模型

**步骤1：** 下载Resnet18模型权重和网络以及cfg文件。[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/VideoGestureRecognition/model.zip)

**步骤2：** 将获取到的文件存放至："样例项目所在目录/model/"

**步骤3：** 模型转换。在模型权重和网络文件所在目录下执行以下命令

```
atc --model=./resnet18_gesture.prototxt --weight=./resnet18_gesture.caffemodel --framework=0 --output=gesture_yuv --soc_version=Ascend310B1 --insert_op_conf=./insert_op.cfg --input_shape="data:1,3,224,224" --input_format=NCHW
```
注: --soc_version 需填写当前芯片类型，可通过`npu-smi info`查询

若终端输出：
```
ATC start working now, please wait for a moment.

ATC run success, welcome to the next use.
```
表示命令执行成功。执行完模型转换脚本后，会生成相应的.om模型文件。

模型转换使用了ATC工具，如需更多信息请参考:

 https://www.hiascend.com/document/detail/zh/canncommercial/80RC3/devaids/devtools/atc/atlasatc_16_0005.html

## 4 编译与运行

**步骤1：** 准备测试视频并配置rtsp流地址。

测试视频可自己准备，也可下载，视频流格式为H264（[测试视频下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/VideoGestureRecognition/data.zip)）。

main.cpp中配置rtsp流源地址

```
# 在 main.cpp 文件中第98行修改配置
rtspList.emplace_back("${本地或rtsp流地址}"); 
```

**步骤2：** 拉起Live555服务。[Live555拉流教程](../../docs/参考资料/Live555离线视频转RTSP说明文档.md)

**步骤3：** 编译
手动编译请参照 ①，脚本编译请参照 ②

>  ① 新建立build目录，进入build执行cmake ..（..代表包含CMakeLists.txt的源文件父目录），在build目录下生成了编译需要的Makefile和中间文件。执行make构建工程，构建成功后就会生成可执行文件。

```
mkdir build

cd build

cmake ..

make
```

>  ② 运行项目根目录下的`build.sh`
```bash
chmod +x build.sh
bash build.sh
```

**步骤4：** 运行。执行`run.sh`脚本前请先确认可执行文件 videoGestureRecognition 已生成。

```
chmod +x run.sh
bash run.sh
```

注：执行脚本后，当前样例会持续循环推流，使用`Ctrl + C`来停止流程

**步骤5：** 查看结果。执行`run.sh`后，会在工程目录下`result`中生成jpg格式的图片。

## 5 常见问题

### 5.1 硬件环境不支持

**问题描述：**

执行第4节**步骤4**运行时报错`Init is not allowed in xxx environment.`

**解决方案：**

更换硬件产品为项目支持的产品

### 5.2 rtsp推理地址错误

**问题描述：**

执行第4节**步骤4**运行时报错`Couldn't open input stream rtsp://xx.xxx.xx.xx:xx/xxxx.264`

**解决方案：**

需在 main.cpp 中正确配置rtsp流地址，其格式如下：
```
rtsp://${ip_address}:${port}/${h264_file}

# ${ip_address}：起流的机器ip地址
# ${port}：端口
# ${h264_file}：放置在与live555MediaServer和startNvr.sh文件同目录的h264视频文件
```