# 全目标结构化

## 1 简介

全目标结构化样例基于mxVision SDK进行开发，以昇腾Atlas300卡为主要的硬件平台，主要支持以下功能：

1. 目标检测：在视频流中检测出目标，本样例选用基于Yolov4-tiny的目标检测，能达到快速精准检测。
2. 动态目标识别和属性分析：能够识别出检测出的目标类别，并对其属性进行分析。
3. 人体属性分类+PersonReID：能够根据人体属性和PersonReID进行分类.
4. 目标属性分类+FaceReID：能够根据目标属性和FaceReID进行分类.
5. 车辆属性分类：能够对车辆的属性进行分类。


## 2 环境依赖

- 支持的硬件形态和操作系统版本

| 硬件形态                             | 操作系统版本   |
| ----------------------------------- | -------------- |
| x86_64+Atlas 300I 推理卡（型号3010） | Ubuntu 18.04.1 |
| x86_64+Atlas 300I 推理卡 （型号3010）| CentOS 7.6     |
| ARM+Atlas 300I 推理卡 （型号3000）   | Ubuntu 18.04.1 |
| ARM+Atlas 300I 推理卡 （型号3000）   | CentOS 7.6     |

- 软件依赖

| 软件名称 | 版本   |
| -------- | ------ |
| cmake    | 3.5.1+ |
| mxVision | 0.2    |
| Python   | 3.9.2  |



## 3 代码主要目录介绍

本代码仓名称为mxSdkReferenceApps，工程目录如下图所示：

```
├── mxVision
│   ├── AllObjectsStructuring
│   |   ├── pipeline
│   |   │   └── AllObjectsStructuring.pipeline
│   |   ├── plugins
│   |   │   ├── MpObjectSelection
|   |   |   |   ├── CMakeLists.txt
|   |   |   |   ├── MpObjectSelection.cpp
|   |   |   |   └── MpObjectSelection.h
│   |   │   └── MxpiFaceSelection
│   |   |       ├── CMakeLists.txt
│   |   │       ├── MxpiFaceSelection.cpp
│   |   │       └── MxpiFaceSelection.h
│   |   ├── models
│   |   ├── CMakeLists.txt
│   |   ├── README.zh.md
│   |   ├── build.sh
│   |   ├── main.py
│   |   └── run.sh
```



## 4 准备

**步骤1：** 参考安装教程《mxVision 用户指南》安装 mxVision SDK。

**步骤2：** 配置 mxVision SDK 环境变量。

`export MX_SDK_HOME=${安装路径}/mxVision `

注：本例中mxVision SDK安装路径为 /root/MindX_SDK。

**步骤3：** 在项目根目录下 AllObjectStructuring/ 创建目录models `mkdir models` ，获取[模型](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/mxVision/AllObjectsStructuring/AllObjectsStructuring_models.zip)，并放到项目根目录下 AllObjectStructuring/models/ 目录下。

**步骤4：** 在项目根目录下 AllObjectStructuring/ 创建目录faces_to_register `mkdir faces_to_register` ，将用来注册入库的目标照片放到项目根目录下 AllObjectStructuring/faces_to_register/ 目录下。faces_to_register目录中可以存放子文件夹，照片格式必须为.jpg，且子文件夹名称必须为英文字符。如果不需要接入特征检索功能，此步骤可忽略。

**步骤5：** 修改项目根目录下 AllObjectStructuring/pipeline/AllObjectsStructuring.pipeline文件：

①：将所有“rtspUrl”字段值替换为可用的 rtsp 流源地址（需要自行准备可用的视频流，目前只支持264格式的rtsp流，264视频的分辨率范围最小为128 * 128，最大为4096 * 4096，不支持本地视频），配置参考如下：
```bash
rstp流格式为rtsp://${ip_addres}:${port}/${h264_file}
例：rtsp://xxx.xxx.xxx.xxx:xxxx/xxxx.264
```

②：将所有“deviceId”字段值替换为实际使用的device的id值，可用的 device id 值可以使用如下命令查看：

`npu-smi info`

**步骤6：** 修改项目根目录下 AllObjectStructuring/pipeline/face_registry.pipeline文件：

①：将所有“deviceId”字段值替换为实际使用的device的id值，勿与AllObjectStructuring.pipeline使用同一个deviceId。可用的 device id 值可以使用如下命令查看：

`npu-smi info`

**步骤7：** 编译mxSdkReferenceApps库中的插件：

在当前目录下，执行如下命令：

`bash build.sh`

**步骤8：** 在当前目录下，安装必要python库：

`pip3.9.2 install -r requirements.txt`



## 5 运行

运行
`bash run.sh`

正常启动后，控制台会输出检测到各类目标的对应信息。




## 6 参考链接

MindX SDK社区链接：https://www.hiascend.com/software/mindx-sdk



## 7 FAQ

### 7.1 运行程序时,LibGL.so.1缺失导致导入cv2报错 

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