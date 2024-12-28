# 实时人脸检测

## 1 介绍

### 1.1 简介

yunet基于MindXSDK开发，在昇腾芯片上进行人脸检测，并实现可视化呈现。输入3路视频，对其进行推理，输出推理结果。

技术实现流程图如下：

<img src="images/process.png" width="700" height="40"/>

表 1.1 系统方案各子系统功能描述：

| 序号 | 子系统         | 功能描述                                                     |
| ---- | -------------- | ------------------------------------------------------------ |
| 1    | 视频输入流     | 接收外部调用接口的输入视频路径，对视频进行拉流，并将拉去的裸流存储到缓冲区（buffer）中，并发送到下游插件。 |
| 2    | 视频解码       | 用于视频解码，当前只支持H264格式。                           |
| 3    | 数据分发       | 对单个输入数据进行2次分发。                                  |
| 4    | 数据缓存       | 输出时为后续处理过程创建一个线程，用于将输入数据与输出数据解耦，并创建缓存队列，存储尚未输入到下流插件的数据。 |
| 5    | 图像处理       | 对解码后的YUV格式的图像进行放缩。                            |
| 6    | 模型推理插件   | 目标检测。                                                   |
| 7    | 模型后处理插件 | 对模型输出的张量进行后处理，得到物体类型数据。               |
| 8    | 目标框转绘插件 | 物体类型转化为OSD实例。                                        |
| 9    | OSD可视化插件  | 实现对视频流的每一帧图像进行绘制。                           |
| 10   | 视频编码插件   | 用于将OSD可视化插件输出的图片进行视频编码，输出视频。        |

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、Atlas 300V pro。

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称 | 版本  | 说明                           | 使用教程                                                     |
| -------- | ----- | ------------------------------ | ------------------------------------------------------------ |
| live555  | 1.09  | 实现视频转rstp进行推流         | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) |
| ffmpeg   | 4.2.1 | 实现mp4格式视频转为264格式视频 | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/pc%E7%AB%AFffmpeg%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md#https://ffmpeg.org/download.html) |

注：live555和ffmpeg需要用户到相关网址下载源码编译安装。

### 1.5 代码目录结构说明

本项目名为yunet实时人脸检测，项目目录如下所示：

````
├── build.sh
├── config
│   ├── face_yunet.cfg      # yunet配置文件
│   └── Yunet.aippconfig    # 模型转换aipp配置文件
├── images
│   ├── error1.png
│   ├── error2.png
│   └── process.png
├── main.py		# 单路视频输出代码
├── test.py		# 三路后处理性能测试代码
├── models      # 用于存放模型，需用户自己创建目录
├── pipeline
│   ├── InferTest.pipeline	# 三路后处理性能测试pipeline
│   └── Yunet.pipeline   	# 单路视频输出pipeline
├── plugin
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── YunetPostProcess.cpp	# 人脸检测框后处理代码
│   └── YunetPostProcess.h
├── plugin1
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── TotalYunetPostProcess.cpp	# 人脸检测框与关键点后处理代码（以供可视化）
│   └── TotalYunetPostProcess.h
├── test                        # 需用户自己创建目录
├── README.md
└── run.sh
````

### 1.6 相关约束

本项目适用于单人及多人正脸视频。对于人脸侧面视频，可以将人脸位置正确标出，但关键点信息标注准确率较低。本项目可以适用于仰卧人脸，但不适用于侧卧人脸。

另外，本项目要求输入视频为 1920*1080 25fps 视频，不支持25帧率以上视频。

## 2 设置环境变量

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh       # sdk安装路径，根据实际安装路径修改
```

## 3 准备模型

**步骤1：** yunet模型下载。本项目中使用的模型是yunet模型，onnx模型可以直接下载，[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/yunet/yunet.onnx)

**步骤2：** 将获取到的文件存放至样例项目所在目录`/models/`下。

**步骤3：** 模型转换。`cd`到`models`文件夹，使用模型转换工具ATC将onnx模型转换为om模型，命令如下：

````
atc --framework=5 --model=yunet.onnx --output=yunet --input_format=NCHW --input_shape="input:1,3,120,160" --log=debug --soc_version=Ascend310P3 --insert_op_conf=../config/Yunet.aippconfig
````

执行该命令后会在`/models/`下生成项目指定模型文件`yunet.om`。若模型转换成功则输出：

```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

## 4 编译与运行

**步骤1：** 准备测试视频。视频流格式为264，放入 `test/` 文件夹下。

**步骤2：** 在 `test/` 文件夹下拉起Live555服务。[Live555拉流教程](../../docs/参考资料/Live555离线视频转RTSP说明文档.md)

**步骤3：** 修改`pipeline/Yunet.pipeline`文件：

①：将文件中第8、196、282行的 “rtspUrl” 字段值替换为可用的 rtsp 流源地址（目前只支持264格式的rtsp流，例："rtsp://xxx.xxx.xxx.xxx:xxx/xxx.264", 其中xxx.xxx.xxx.xxx:xxx为ip和端口号，端口号需同Live555服务的起流端口号一致，xxx.264为待测视频流文件名）；

②：将文件中第4行的 “deviceId” 字段值替换为实际使用的device的id值。

注意：由于本项目是支持端对端3路推理，故需设置3个视频源，请使用者自行将pipeline中的所有对应位置修改为自己所使用的源流地址和文件名。

**步骤4：** 编译。在项目根目录下，先执行命令`bash ${MX_SDK_HOME}/operators/opencvosd/generate_osd_om.sh`编译opencv_osd算子，然后再执行命令`bash build.sh`

**步骤5：** 拷贝so文件至MindXSDK安装路径的`lib/modelpostprocessors/`目录下。在根目录下执行命令：

```bash
chmod 640 plugin/build/libyunetpostprocess.so
cp plugin/build/libyunetpostprocess.so ${MX_SDK_HOME}/lib/modelpostprocessors/
```

**步骤6：** 运行。在项目根目录下，执行命令`bash run.sh`，可手动执行`ctrl + c`终止程序运行。

**步骤7：** 查看结果。在根目录下得到输出结果`result.264`。

## 5 性能验证

在第 4 节的基础上，继续进行如下步骤

**步骤1：** 修改`pipeline/InferTest.pipeline`文件。操作方式参考[第4节步骤3](#4-编译与运行)

**步骤2：** 拷贝so文件至MindXSDK安装路径的`lib/modelpostprocessors/`目录下。在根目录下执行命令：

```bash
chmod 640 plugin1/build/libtotalyunetpostprocess.so
cp plugin1/build/libtotalyunetpostprocess.so ${MX_SDK_HOME}/lib/modelpostprocessors/
```

**步骤3：** 性能测试。修改根目录下`run.sh`文件中第32行，由`python3 main.py`改为`python3 test.py`，再次在根目录下运行`bash run.sh`，即可获得`libtotalyunetpostprocess.so`的性能结果。

**步骤4：** 查看结果。因为性能检测结果实时输出，使用者在`test.py`运行过程中可以实时查看检测结果，并且在需要时可以在输出帧率后立刻按`ctrl + c`终止程序运行，以查看帧率。

## 6 常见问题

### 6.1 视频解码器负荷过高，报内存相关错误

**问题描述：**

若视频解码器负荷过高则会出现以下问题：

![error1](images/error1.png)
![error2](images/error2.png)

**解决方案：**

导致此问题的可能原因为：视频帧率过高、视频尺寸过大或解码器正在同时解码过多其他视频。

解决方案：确保三路视频都为 1920*1080 25fps 并且减少其它任务的运行。

### 6.2 无法打开视频流

**问题描述：**

在运行的过程中，无法打开视频流。

**解决方案：**

pipeline中需要配置多路rtsp视频地址，完善pipeline中的配置项。

### 6.3 运行过程中报错`Realpath parsing failed`

**问题描述：**

未编译opencv_osd算子，运行过程中报错`Realpath parsing failed`。

**解决方案：**

在项目根目录下，执行命令`bash ${MX_SDK_HOME}/operators/opencvosd/generate_osd_om.sh`编译opencv_osd算子。

### 6.4 推流失败

**问题描述：**

运行过程中报错`streamInstance GetResult return nullptr`。

**解决方案：**

检查pipeline中的配置项中rtsp流地址是否正确，如确认正确则重新起流（可能由于某些原因导致已启动的live555服务不可用）。