# 全目标结构化

## 1 介绍
### 1.1 简介

全目标结构化样例基于Vision SDK进行开发，以昇腾Atlas 300I pro、 Atlas 300V pro卡为主要的硬件平台，主要支持以下功能：

* 目标检测：在视频流中检测出目标，本样例选用基于Yolov4-tiny的目标检测，能达到快速精准检测。
* 动态目标识别和属性分析：能够识别检测出的目标类别，并对其属性进行分析。
* 人体属性分类+PersonReID：能够根据人体属性和PersonReID进行分类。
* 目标属性分类+FaceReID：能够根据目标属性和FaceReID进行分类。 
* 车辆属性分类：能够对车辆的属性进行分类。

### 1.2 支持的产品
本项目支持昇腾Atlas 300I pro、 Atlas 300V pro。

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本：

| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称 | 版本        |
| -------- |-----------|
| cmake    | 3.5.1+    |
| Python   | 3.9.2     |
| numpy   | 1.23.1    |
| opencv-python   | 4.10.0.84 |
| Pillow   | 8.0.1     |
| protobuf   | 4.24.4    |
| websocket-server   | 0.4       |


### 1.5 代码目录结构说明

```
├── VisionSDK
│   ├── AllObjectsStructuring
│   |   ├── main_pipeline
│   |   │   └── __init__.py
│   |   │   └── main_pipeline.py
│   |   ├── pipeline
│   |   │   └── AllObjectsStructuring.pipeline
│   |   │   └── face_registry.pipeline
│   |   ├── plugins
│   |   │   ├── MpObjectSelection
|   |   |   |   ├── CMakeLists.txt
|   |   |   |   ├── MpObjectSelection.cpp
|   |   |   |   └── MpObjectSelection.h
│   |   │   └── MxpiFaceSelection
│   |   |   |   ├── CMakeLists.txt
│   |   |   │   ├── MxpiFaceSelection.cpp
│   |   │   |   └── MxpiFaceSelection.h
│   |   │   └── MxpiFrameAlign
│   |   |   |   ├── BlockingMap.h
│   |   |   │   ├── CMakeLists.txt
│   |   |   │   ├── MxpiFrameAlign.cpp
│   |   |   │   └── MxpiFrameAlign.h
│   |   │   └── MxpiSkipFrame
│   |   |       ├── CMakeLists.txt
│   |   │       ├── MxpiSkipFrame.cpp
│   |   │       └── MxpiSkipFrame.h
│   |   ├── Proto
│   |   │   ├── CMakeLists.txt
│   |   │   ├── MxpiAllObjectsStructuringDataType.proto
│   |   ├── retrieval
│   |   │   ├── __init__.py
│   |   │   ├── feature_retrieval.py
│   |   │   ├── register.py
│   |   ├── util
│   |   │   ├── __init__.py
│   |   │   ├── channel_status.py
│   |   │   ├── checker.py
│   |   │   ├── display.py
│   |   │   ├── main_entry.py
│   |   │   ├── multi_process.py
│   |   │   ├── pipeline.py
│   |   │   ├── yuv.py
│   |   ├── models                  # 需用户创建
│   |   ├── build.sh
│   |   ├── CMakeLists.txt
│   |   ├── main.py
│   |   ├── README.md
│   |   └── run.sh
```


## 2 设置环境变量

```bash
#设置CANN环境变量，ascend-toolkit-path为cann安装路径
. ${ascend-toolkit-path}/set_env.sh

#设置Vision SDK环境变量，SDK-path为Vision SDK 安装路径
. ${SDK-path}/set_env.sh
```

## 3 准备模型

**步骤1：** 在项目根目录下 AllObjectStructuring/ 创建目录models `mkdir models` ，获取[模型](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/mxVision/AllObjectsStructuring/AllObjectsStructuring_models.zip)，并放到项目根目录下 AllObjectStructuring/models/ 目录下。

**步骤2：** 进入到AllObjectStructuring/models目录下，执行以下命令：

```bash
atc --model=./yolov4_improve/yolov4-tiny-customized.pb --framework=3 -output=./yolov4_improve/yolov4_detection --insert_op_conf=./yolov4_improve/aipp_yolov4.cfg --soc_version=Ascend310P3
atc --model=./facequality/face_quality_batch_8.prototxt --weight=./facequality/face_quality.caffemodel --framework=0 -output=./facequality/face_quality_improve --insert_op_conf=./facequality/aipp.cfg --soc_version=Ascend310P3
atc --model=./faceembedding/face_embedding_batch_8.prototxt --weight=./faceembedding/face_embedding.caffemodel --framework=0 -output=./faceembedding/face_embedding --insert_op_conf=./faceembedding/aipp.cfg --soc_version=Ascend310P3
atc --model=./faceattr/face_attribute_batch_4.prototxt --weight=./faceattr/face_attribute.caffemodel --framework=0 -output=./faceattr/face_attribute_batch_4 --insert_op_conf=./faceattr/aipp.cfg --soc_version=Ascend310P3
atc --model=./facefeature/face_feature_batch_1.prototxt --weight=./facefeature/face_feature.caffemodel --framework=0 -output=./facefeature/face_feature_batch_1 --insert_op_conf=./facefeature/aipp.cfg --soc_version=Ascend310P3
atc --model=./motorattr/car_color.prototxt --weight=./motorattr/car_color.caffemodel --framework=0 -output=./motorattr/car_color --insert_op_conf=./motorattr/aipp.cfg --soc_version=Ascend310P3
atc --model=./motorattr/vehicle_attribute.pb --framework=3 -output=./motorattr/vehicle_attribute --insert_op_conf=./motorattr/aipp.cfg --soc_version=Ascend310P3
atc --model=./pedestrianattribute/pedestrian_attribute.prototxt --weight=./pedestrianattribute/pedestrian_attribute.caffemodel --framework=0 -output=./pedestrianattribute/pede_attr --insert_op_conf=./pedestrianattribute/aipp.cfg --soc_version=Ascend310P3
atc --model=./pedereid/pedestrian_reid.prototxt --weight=./pedereid/pedestrian_reid.caffemodel --framework=0 -output=./pedereid/pede_reid --insert_op_conf=./pedereid/aipp.cfg --soc_version=Ascend310P3
atc --model=./car_plate_detection/car_plate_detection.prototxt --weight=./car_plate_detection/car_plate_detection.caffemodel --framework=0 -output=./car_plate_detection/car_plate_detection --insert_op_conf=./car_plate_detection/aipp.cfg --soc_version=Ascend310P3
atc --model=./car_plate_recognition/car_plate_recognition.prototxt --weight=./car_plate_recognition/car_plate_recognition.caffemodel --framework=0 -output=./car_plate_recognition/car_plate_recognition --insert_op_conf=./car_plate_recognition/aipp.cfg --soc_version=Ascend310P3
```
**步骤3：** 查看結果 

执行完模型转换后，若提示如下信息说明模型转换成功。

```
ATC run success, welcome to the next use.
```

## 4 编译与运行

**步骤1：** 根据下面的文档，创建视频流：

[创建视频流](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md)

**步骤2：** 修改项目根目录下 AllObjectStructuring/pipeline/AllObjectsStructuring.pipeline文件：

1、将所有“rtspUrl”字段值替换为可用的 rtsp 流源地址（需要自行准备可用的视频流，目前只支持264格式的rtsp流，264视频的分辨率范围最小为128 * 128，最大为4096 * 4096，不支持本地视频），配置参考如下：
```bash
rstp流格式为rtsp://${ip_addres}:${port}/${h264_file}
例：rtsp://xxx.xxx.xxx.xxx:xxxx/xxxx.264
```

2、将所有“deviceId”字段值替换为实际使用的device的id值，可用的 device id 值可以使用如下命令查看：

```bash
npu-smi info
```

**步骤3：** 修改项目根目录下 AllObjectStructuring/pipeline/face_registry.pipeline文件：

将所有“deviceId”字段值替换为实际使用的device的id值，勿与AllObjectStructuring.pipeline使用同一个deviceId。可用的 device id 值可以使用如下命令查看：

```bash
npu-smi info
```

**步骤4：** 编译插件：

在当前目录下，执行如下命令：

```bash
bash build.sh
```

**步骤5：** 运行程序 

```bash
python3 main.py -main-pipeline-only=True
```

**步骤6：** 查看结果

正常启动后，控制台会输出检测到各类目标的对应信息。


## 5 常见问题

### 5.1 运行程序时，LibGL.so.1缺失导致导入cv2报错 

**问题描述：**
运行程序时报错："ImportError: libGL.so.1: cannot open shared object file: No such file or directory"

**解决方案：**

如果服务器系统是Debian系列，如Ubantu，执行下列语句：
```bash
sudo apt update
sudo apt install libgl1-mesa-glx
```

如果服务器系统是RedHat系列，如Centos，执行下列语句：
```bash
yum install mesa-libGL
```

### 5.2 运行程序时，导入MxpiDataType_pb2.py中的数据结构时报错

**问题描述：**
运行程序时报错：“Type Error: Descriptors cannot be created directly.”

**解决方案：**

执行以下命令：
```bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```
