# 手势关键点检测

## 1 介绍

### 1.1 简介
手势关键点检测样例基于MxVision开发，实现人手检测以及手势关键点检测，将检测结果可视化并保存。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 代码目录结构与说明

本工程名称为 GestureKeypointDetection，工程目录如下所示：
```
.
├── main.py
├── detection.pipeline
├── model
│   ├── hand
│   │   ├── coco.names
│   │   ├── aipp.cfg
│   │   └── hand.cfg
│   └── keypoint
│       └── insert_op.cfg
└── README.md
```

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：下载yolo模型：[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/GestureKeypointDetection/yolov3_hand.onnx)，将获取到的onnx文件存放至本案例代码的GestureKeypointDetection/model/hand 目录下。

**步骤2**：下载resnet模型：[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/GestureKeypointDetection/resnet_50_size-256.onnx)，将获取到的onnx文件存放至本案例代码的GestureKeypointDetection/model/keypoint 目录下。

**步骤3**：进入GestureKeypointDetection/model/hand目录执行以下命令：
```
atc --model=yolov3_hand.onnx --framework=5 --output=hand --input_format=NCHW --output_type=FP32 --soc_version=Ascend310P3 --input_shape="input.1:1,3,416,416" --insert_op_conf=./aipp.cfg --log=info
```

**步骤4**：进入GestureKeypointDetection/model/keypoint目录执行以下命令：
```
atc --model=./resnet_50_size-256.onnx --framework=5 --output=hand_keypoint --soc_version=Ascend310P3 --input_shape="input:1, 3, 256, 256" --input_format=NCHW --insert_op_conf=./insert_op.cfg
```

## 4 运行
**步骤1**： 配置pipeline：
根据实际的环境变量，修改detection.pipeline文件第43行：
```
#将postProcessLibPath的值修改为libyolov3postprocess.so的绝对路径路径（在SDK安装路径下）
"mxpi_objectpostprocessor0": {
    "props": {
        "dataSource": "mxpi_tensorinfer0",
        "postProcessConfigPath": "./model/hand/hand.cfg",
        "labelPath": "./model/hand/coco.names",
        "postProcessLibPath": "{$MX_SDK_HOME}/lib/modelpostprocessors/libyolov3postprocess.so"
    },
    "factory": "mxpi_objectpostprocessor",
    "next": "mxpi_imagecrop0"
},
```

**步骤2**：准备输入图片：将关于人手手势的输入图片命名为test.jpg并放在项目根目录下。

**步骤3**：在项目根目录下执行：
```
python3 main.py test.jpg
```

**步骤4**：查看结果：执行成功后终端会打印相关检测信息，并在当前目录下生成检测结果图片result_test.jpg。

