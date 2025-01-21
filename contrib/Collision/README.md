# 车辆碰撞识别

## 1 介绍
### 1.1 简介
此项目的碰撞插件基于Vision SDK开发，在昇腾芯片上进行目标检测和跟踪，可以对车辆进行画框和编号，检测到车辆碰撞后，可将动向编号提示为“Collision”并将检测结果可视化并保存。

项目主要流程为：通过live555服务器进行拉流输入视频，然后进行视频解码将264格式的视频解码为YUV格式的图片，图片缩放后经过模型推理进行车辆识别，识别结果经过yolov3后处理后得到识别框，对识别框进行跟踪并编号，用编号覆盖原有的类别信息，如检测到车辆发生碰撞，碰撞的车辆的编号将会被“Collision”所替换，再将识别框和类别信息分别转绘到图片上，最后将图片编码成视频进行输出。

本案例可以满足对视频的检测，对检测到的碰撞的车辆在碰撞时刻，输出“Collision”的字样进行提醒。经过测试我们可以知道有以下限制条件：

1.对一个正常清晰的路面，我们可以完成绝大多数正常的一个车辆碰撞检测。

2.当视频清晰度不够，或者车辆速度过快，yolov3并不能很好的识别目标，或者当大车与小车发生碰撞，导致小车被遮挡，或者碰撞事故严重，导致受损车辆无法被检测出来，那么我们对碰撞就会检测失败。

3.当车辆很密集时，障碍物很多时，就会导致物体画框增多，画框不同角度的重叠就可能导致碰撞误判。

本案例的车辆碰撞识别业务流程为：待检测视频存放在live555服务器上经mxpi_rtspsrc拉流插件输入，然后使用视频解码插件mxpi_videodecoder将视频解码成图片，再通过图像缩放插件mxpi_imageresize将图像缩放至满足检测模型要求的输入图像大小要求，缩放后的图像输入模型推理插件mxpi_tensorinfer得到检测结果，再经yolov3后处理插件处理推理结果，得到识别框。再接入跟踪插件中识别框进行目标跟踪，得到目标的跟踪编号，然后在使用mxpi_trackidreplaceclassname插件将跟踪编号覆盖类名信息，再接入本项目开发的碰撞检测插件mxpi_collisionclassname，使用mxpi_object2osdinstances和mxpi_opencvosd分别将识别框和类名（更替写入跟踪编号或者“Collison”碰撞提醒）绘制到原图片，再通过mxpi_videoencoder将图片合成视频

表1.1 系统方案各子系统功能描述：

| 序号 | 子系统               | 功能描述                                                     |
| ---- | -------------------- | ------------------------------------------------------------ |
| 1    | 视频输入             | 接收外部调用接口的输入视频路径，对视频进行拉流，并将拉取的裸流存储到缓冲区（buffer）中，并发送到下游插件。 |
| 2    | 视频解码             | 用于视频解码，当前只支持H264/H265格式。                      |
| 3    | 数据分发             | 对单个输入数据分发多次。                                     |
| 4    | 数据缓存             | 输出时为后续处理过程另创建一个线程，用于将输入数据与输出数据解耦，并创建缓存队列，存储尚未输出到下流插件的数据。 |
| 5    | 图像处理             | 对解码后的YUV格式的图像进行指定宽高的缩放，暂时只支持YUV格式 的图像。 |
| 6    | 模型推理插件         | 目标分类或检测，目前只支持单tensor输入（图像数据）的推理模型。 |
| 7    | 模型后处理插件       | 采用yolov3后处理插件输出的tensor解析，获取目标检测框以及对应的ReID向量，传输到跟踪模块。 |
| 8    | 跟踪插件             | 实现多目标（包括机非人、目标）路径记录功能。                 |
| 9    | 跟踪编号取代类名插件 | 用跟踪插件产生的编号信息取代后处理插件产生的类名信息，再将数据传入数据流中。 |
| 10   | 碰撞检测插件         | 检测到车辆碰撞后，碰撞车辆的编号将会被“Collision”所替换，再将数据传入数据流中。 |
| 11   | 目标框转绘插件       | 将流中传进的MxpiObjectList数据类型转换可用于OSD插件绘图所使用的的 MxpiOsdInstancesList数据类型。 |
| 12   | OSD可视化插件        | 主要实现对每帧图像标注跟踪结果。                             |
| 13   | 视频编码插件         | 用于将OSD可视化插件输出的图片进行视频编码，输出视频。        |

本案例的技术实现流程图如下所示：

![SDK流程图](../Collision/image/SDK_process.png)

注：红色和蓝色字体表示相关插件为本项目开发插件，其余为SDK内置插件。
### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。

### 1.3 支持的版本

| Vision SDK版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 代码目录结构与说明

```
├── build.sh
├── collision.pipeline     # pipeline文件
├── collision.py
├── image
│   ├── after_collision.png
│   ├── before_collision.png
│   ├── collision.png
│   ├── error.png
│   ├── SDK_process.png
│   └── video_conversion.png
├── model
│   ├── aipp_yolov3_416_416.aippconfig      # 模型转换aipp配置文件
│   ├── coco.names         # 类名
│   └── yolov3.cfg        # yolov3配置文件
├── plugins
│   ├── MxpiCollisionClassName      # 碰撞检测插件
│   │   ├── build.sh
│   │   ├── CMakeLists.txt
│   │   ├── MxpiCollisionClassName.cpp
│   │   └── MxpiCollisionClassName.h
│   └── MxpiTrackIdReplaceClassName    # 跟踪编号取代类名插件
│       ├── build.sh
│       ├── CMakeLists.txt
│       ├── MxpiTrackIdReplaceClassName.cpp
│       └── MxpiTrackIdReplaceClassName.h
└── README.md


```


## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：

```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${Vision-SDK-path}/set_env.sh
# Vision-SDK-path: Vision SDK安装路径
# ascend-toolkit-path: CANN安装路径
```


## 3 准备模型
**步骤1：** 下载模型相关文件

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ActionRecognition/ATC%20YOLOv3%28FP16%29%20from%20TensorFlow%20-%20Ascend310.zip)下载得到yolov3_tf.pb文件，并放到项目根目录的`model`文件夹。

**步骤2：** 转换模型格式

进入项目根目录的`model`文件夹下执行命令：

```
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
```

执行该命令后会在当前文件夹下生成项目需要的模型文件 yolov3.om。执行后终端输出为：

```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

表示命令执行成功。


## 4 编译与运行

**步骤1：**  启动rtsp服务

按照 [教程](https://gitee.com/ascend/mindsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) 自行准备视频数据，并启动rtsp服务。

**步骤2：** 修改collision.pipeline配置文件

第**9**行 `"rtspUrl":"rtsp://xxx.xxx.xxx.xxx:xxxx/xxx.264"`中的rtsp://xxx.xxx.xxx.xxx:xxxx/xxx.264替换为可用的 rtsp 流地址。

第**152**行 `"imageHeight":"720"`中的720替换为视频帧实际的高。

第**153**行 `"imageWidth":"1280"`中的1280替换为视频帧实际的宽。

**步骤3：** 编译

进入Vision SDK安装目录的`operators/opencvosd`目录下执行命令：

```
bash generate_osd_om.sh
```

进入 `Collision` 目录，在 `Collision` 目录下执行命令：

```
bash build.sh
```


**步骤4：** 启动服务

回到主目录下，在主目录下执行命令：

```
python3 collision.py
```

命令执行成功后会在标准输出实时打印已保存的视频帧数量。


**步骤5：**  停止服务

命令行输入Ctrl+C组合键可手动停止服务。

注意：考虑到保存检测结果的视频会占用较大存储空间，请用户合理控制服务运行时间、及时停止服务，避免视频文件过大、影响服务器正常工作。


**步骤6：**  查看结果

命令执行成功后会在当前目录下生成检测结果视频文件out_collision.h264，打开out_collision.h264查看文件、观测目标跟踪结果。
