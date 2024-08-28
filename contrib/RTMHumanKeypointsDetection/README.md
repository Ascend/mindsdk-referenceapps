# 实时人体关键点检测

## 1 介绍

### 1.1 简介
人体关键点检测是指在输入图像上对指定的 18 类人体骨骼关键点位置进行检测，然后将关键点正确配对组成相应的人体骨架，展示人体姿态。本项目基于MindX SDK，在昇腾平台上，实现了对RTSP视频流进行人体关键点检测并连接成人体骨架，最后将检测结果可视化并保存。
本系统技术流程图如下所示：

![pipeline](image/pipeline.png)

本系统设计了不同的功能模块。主要流程为：视频拉流传入业务流中，然后通过解码插件对视频进行解码，再对解码出来的YUV图像进行尺寸调整，然后利用OpenPose模型进行人体关键点检测，然后我们自己编写的后处理插件会把人体关键点信息传递给绘图插件，绘图完毕后进行视频编码，最后把结果输出。各模块功能描述如下表所示：


| 序号 | 子系统     | 功能描述                                                     |
| :--- | :--------- | :----------------------------------------------------------- |
| 1    | 视频拉流   | 调用MindX SDK的 **mxpi_rtspsrc**接收外部调用接口的输入视频路径，对视频进行拉流 |
| 2    | 视频解码   | 调用MindX SDK的**mxpi_videodecoder**                         |
| 3    | 图像缩放   | 调用**mxpi_imageresize**对解码后的YUV格式的图像进行指定宽高的缩放 |
| 4    | 检测推理   | 使用已经训练好的OpenPose模型，检测出图像中的车辆信息。插件：**mxpi_tensorinfer** |
| 5    | 模型后处理 | 使用自己编译的**mxpi_rtmopenposepostprocess**插件的后处理库libmxpi_rtmopenposepostprocess.so，进行人体关键点检测的后处理 |
| 6    | 绘图       | 调用OSD基础功能在YUV图片上绘制直线。插件：**mxpi_opencvosd** |
| 7    | 视频编码   | 调用MindX SDK的**mxpi_videoencoder**进行视频编码             |
| 8    | 输出       | 调用MindX SDK的**appsink**进行业务流结果的输出               |



使用测试视频应当人物清晰、光线充足、无环境背景干扰，而且人物在画面中占据范围不应太小、人物姿态不应过于扭曲、人物不应完全侧对镜头、背景不应太复杂；视频切勿有遮挡，不清晰等情况。
### 1.2 支持的产品

x86_64 Atlas 300I（型号3010）和arm Atlas 300I（型号3000）。

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0 | 7.0.0   |  23.0.0  |

### 1.4 三方依赖
本项目除了依赖昇腾Driver、Firmware、CANN和mxVision及其要求的配套软件外，还需额外依赖以下软件：

| 软件名称 | 版本   |
| -------- | ----- |
| live555  | 1.09 |

### 1.5 代码目录结构与说明

本工程名称为RTMHumanKeypointsDetection，工程目录如下图所示：

```
├── eval
│   ├── pipeline
│   ├── plugin
│   ├── proto
│   └── eval.py
├── image
│   ├── pipeline.png
├── models
│   └── insert_op.cfg
├── pipeline
│   └── rtmOpenpose.pipeline     # pipeline文件
├── plugins	                 # 实时人体关键点检测后处理库
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── MxpiRTMOpenposePostProcess.cpp
│   └── MxpiRTMOpenposePostProcess.h
├── CMakeLists.txt
├── README.md
├── build.sh     # 编译
├── main.cpp
└── run.sh       # 运行
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

本项目需要使用的模型包括用于人体姿态估计的模型和用于画图的osd模型，需要执行以下步骤得到：
### 步骤1 下载模型相关文件
根据[链接](https://gitee.com/link?target=https%3A%2F%2Fmindx.sdk.obs.cn-north-4.myhuaweicloud.com%2Fmindxsdk-referenceapps%2520%2Fcontrib%2FRTMHumanKeypointsDetection%2Fhuman-pose-estimation512.onnx)下载得到human-pose-estimation512.onnx文件。

###  步骤2 转换模型格式

将onnx模型拷贝至"${RTMHumanKeypointsDetection代码包目录}/models/"目录下，并在拷贝目标目录下执行以下命令将onnx模型转换成om模型：

       atc --model=./human-pose-estimation512.onnx --framework=5 --output=openpose_pytorch_512 --soc_version=Ascend310 --input_shape="data:1, 3, 512, 512" --input_format=NCHW --insert_op_conf=./insert_op.cfg

### 步骤3 生成osd模型文件

本项目需要使用 `mxpi_opencvosd` 插件，使用前需要生成所需的模型文件。执行MindX SDK开发套件包安装目录下 `operators/opencvosd/generate_osd_om.sh` 脚本生成所需模型文件。

## 4 编译与运行
### 步骤1 创建rtsp视频流

使用live555创建rtsp视频流，live555的使用方法可以参考[链接](https://gitee.com/ascend/docs-openmind/blob/master/guide/mindx/sdk/tutorials/reference_material/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md)。
### 步骤2 配置pipeline文件中的rtsp视频流地址、模型文件路径和视频的宽高

打开`RTMHumanKeypointsDetection/pipeline`目录下的rtmOpenpose.pipeline文件。根据步骤1创建的rtsp视频流地址，设置中mxpi_rtspsrc0的rtspUrl值，如下所示：

```
        "mxpi_rtspsrc0": {
            "factory": "mxpi_rtspsrc",
            "props": {
                "rtspUrl":"rtsp://xxx.xxx.xxx.xxx:xxxx/xxx.264",      // 修改为自己所使用的的服务器和文件名
                "channelId": "0"
            },
            "next": "mxpi_videodecoder0"
        },
```


根据om模型的文件路径，设置中mxpi_tensorinfer0的modelPath值，如下所示：

```
        "mxpi_tensorinfer0":{
            "next":"mxpi_rtmopenposepostprocess0",
            "factory":"mxpi_tensorinfer",
            "props":{
                "dataSource": "mxpi_imageresize0",
                "modelPath":"./models/openpose_pytorch_512.om"	//检查om模型文件名是否正确
            }
        },
```

根据rtsp视频流中视频的实际高和宽，设置中mxpi_videoencoder0的imageHeight和imageWidth值，如下所示：

```
        "mxpi_videoencoder0":{
            "props": {
                "inputFormat": "YUV420SP_NV12",
                "outputFormat": "H264",
                "fps": "1",
                "iFrameInterval": "50",
                "imageHeight": "720",		#rtsp视频流中视频的实际高
                "imageWidth": "1280"		#rtsp视频流中视频的实际宽
            },
```

### 步骤3 编译插件

在`plugins/`目录里面执行命令：

```bash
bash build.sh
```


### 步骤4 编译和运行主程序

回到项目主目录下执行命令：

```bash
bash run.sh
```

###  步骤5 停止服务

命令行输入Ctrl+C组合键可停止服务。

### 步骤6 查看结果

命令执行成功后会在控制台输出检测的帧率，并在当前目录下生成结果视频文件`out.h264`。

## 5 常见问题

### 5.1 检测输出帧率过低问题

问题描述：控制台输出检测的帧率严重低于25fps（如下10fps），如下所示：

```bash
I20220727 09:21:02.990229 32360 MxpiVideoEncoder.cpp:324] Plugin(mxpi_videoencoder0) fps (10).
```

解决方案： 确保输入的视频帧率高于25fps。

### 5.2 视频编码参数配置错误问题

问题描述：运行过程中报错如下：

```bash
E20220728 17:05:59.947093 19710 DvppWrapper.cpp:573] input width(888) is not same as venc input format(1280)
E20220728 17:05:59.947126 19710 MxpiVideoEncoder.cpp:310] [mxpi_videoencoder0][2010][DVPP: encode H264 or H265 fail] Encode fail.
```

`pipeline/rtmOpenpose.pipeline`中视频编码插件分辨率参数指定错误。手动指定imageHeight 和 imageWidth 属性，需要和rtsp视频流中视频的分配率相同。

解决方案：确保`pipeline/rtmOpenpose.pipeline`中 mxpi_videoencoder0 插件中的 imageHeight 和 imageWidth 为rtsp视频流中视频的实际高和宽。
