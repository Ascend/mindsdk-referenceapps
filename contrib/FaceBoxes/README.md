# FaceBoxes

## 1 介绍

### 1.1 简介
本开发项目基于VisionSDK，用Faceboxes模型实现目标检测。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的VisionSDK版本、CANN版本、Driver/Firmware版本如下所示：
| VisionSDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖
第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用pip3 install 安装以下依赖。
|软件名称    | 版本        |
|-----------|-----------|
| opencv-python   | 4.10.0.84 |

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：下载faceboxes模型-[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/Faceboxes/model.zip)，解压后将获取到的.onnx文件存放至本案例代码的FaceBoxes/models 目录下。

**步骤2**：进入FaceBoxes/models 目录下执行以下命令
```
atc --framework=5 --model=faceboxes-b0_bs1.onnx --output=faceboxes-b0_bs1 --input_format=NCHW --input_shape="image:1,3,1024,1024" --log=debug --soc_version=Ascend310P3 --insert_op_conf=./FaceBoxes.aippconfig
```

## 4 编译与运行
**步骤1**：编译后处理插件so，在FaceBoxes/plugin/FaceBoxesPostProcess/目录下执行
```
bash build.sh
```

**步骤2**：配置pipeline：
根据实际的SDK安装路径，修改Faceboxes.pipeline文件第38行：
```
#将postProcessLibPath的值修改为libfaceboxespostprocess.so的绝对路径路径（在SDK安装路径下）
"mxpi_objectpostprocessor0": {
    "props": {
        "dataSource": "mxpi_tensorinfer0",
        "postProcessConfigPath": "./models/faceboxes-b0_bs1.cfg",
        "postProcessLibPath": "${SDK安装路径}/mxVision/lib/modelpostprocessors/libfaceboxespostprocess.so"
},
```

**步骤3:** 将输入图片命名为test.jpg放到项目根目录下

**步骤4:** 在项目根目录下运行
```
python3 main.py
```

**步骤5:** 查看结果

执行成功后会在当前目录下生成结果图片result.jpg。