# 疲劳驾驶识别（Fatigue driving recognition）

## 1 介绍

### 1.1 简介
本开发样例演示驾驶人员疲劳状态识别系统（Fatigue driving recognition），供用户参考。本系统基于Vision SDK进行开发，实现在驾驶环境下驾驶人员疲劳状态识别与预警。项目的整体流程如下：
1. 利用目标检测模型采集视频中的目标图像
2. 利用PFLD模型进行目标关键点检测，获取眼部位置信息
3. 通过计算度量疲劳/瞌睡的物理量识别驾驶人员的疲劳状态

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：
| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖

| 依赖软件 | 版本       | 说明                           | 使用教程                                                     |
| -------- | ---------- | ------------------------------ | ------------------------------------------------------------ |
| live555  | 1.10       | 实现视频转rstp进行推流         | [链接](https://gitee.com/ascend/mindsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) |

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：下载yolo模型：[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/faceswap/yolov4_improve.zip)，解压后将获取到的所有文件存放至本案例代码的FatigueDrivingRecognition/model 目录下。

**步骤2**：下载pfld模型：[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/FatigueDrivingRecognition/model.zip)，解压后将获取到的pfld_106.onnx存放至本案例代码的FatigueDrivingRecognition/model 目录下。

**步骤3**：  进入FatigueDrivingRecognition/model目录执行以下命令。
```
atc --model=./yolov4-tiny-customized.pb --framework=3 -output=./yolov4_detection --insert_op_conf=./aipp_yolov4.cfg --soc_version=Ascend310P3

atc --framework=5 --model=./pfld_106.onnx --output=pfld_106 --input_format=NCHW --insert_op_conf=./aipp_pfld_112_112.aippconfig  --input_shape="input_1:1,3,112,112" --log=debug --soc_version=Ascend310P3
```

## 4 编译与运行
**步骤1**：编译后处理插件so：在项目根目录下执行
```
bash build.sh #编译
chmod 440 ${SDK_INSTALL_PATH}/mxVision/lib/plugins/libmxpi_pfldpostprocess.so #修改so权限，${SDK_INSTALL_PATH}根据实际SDK安装路径修改
```

**步骤2**：拉起Live555服务：[Live555拉流教程](../../docs/参考资料/Live555离线视频转RTSP说明文档.md)

**步骤3**：配置pipeline：
根据实际的网络视频流，修改test_video.pipeline文件第9行：
```
#将rtspUrl的值修改为实际的rtsp网络视频流地址
"mxpi_rtspsrc0": {
    "factory": "mxpi_rtspsrc",
    "props": {
        "rtspUrl": "${264file_path}",
        "channelId": "0"
    },
    "next": "mxpi_videodecoder0"
},
```
根据实际的环境变量，修改test_video.pipeline文件第46行：
```
#将postProcessLibPath的值修改为libyolov3postprocess.so的绝对路径路径（在SDK安装路径下）
"mxpi_objectpostprocessor0": {
    "props": {
        "dataSource": "mxpi_tensorinfer0",
        "postProcessConfigPath": "model/yolov4.cfg",
        "labelPath": "model/coco.names",
        "postProcessLibPath": "${MX_SDK_HOME}/lib/modelpostprocessors/libyolov3postprocess.so"
    },
    "factory": "mxpi_objectpostprocessor",
    "next": "mxpi_distributor0"
},
```

**步骤4**：运行：
```
python3 test_video.py --online_flag True
```

**步骤5**：查看结果：
执行成功后终端会输出视频中是否存在疲劳驾驶，输出`Normal`为正常驾驶，输出`Fatigue!!!`为疲劳驾驶， 输出`Nobody is detected`为未检测到人。


## 5 常见问题

### 5.1 第一帧解码失败问题

**问题描述：** 运行测试代码后，可能会出现如下图所示的警告信息：

![Q1](images/Q1.png)

**解决方案：** live555推流工具导致，不影响测试。

### 5.2 数据集问题

**问题描述：** 运行测试代码测试部分视频文件时，可能会出现如下图所示的警告信息：

![Q2](images/Q2.png)

**解决方案：** 部分视频文件中有不止一个人，目标检测模型能检测出不止一个目标，而除了驾驶人员之外的目标较小，受mxpi_imagecrop插件对裁剪尺寸的限制，无法将小目标裁剪出来，因此在测试时要注意测试视频中只包含驾驶人员一个人。

### 5.3 每一帧解码失败问题

**问题描述：** 运行测试代码测试自己的视频时，出现每一帧都解码失败的警告。

![Q4](images/Q4.png)

**解决方案：** 测试的视频需要是yuv420编码的264文件，需要对测试的文件进行修改。

### 5.4 测试场景限制

**问题描述：** 部分场景测试时预测结果与预期不符。

**解决方案：** 由于模型训练与采用的疲劳度计算方法问题，本项目测试时具有一定限制条件：
（1）不适合嘴巴微张但未打哈欠且眼部被遮挡的场景
（2）不适合驾驶人员疲劳驾驶，双眼紧闭但未打哈欠的场景



