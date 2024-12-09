# 多线程使用流程编排（C++）

## 1 介绍

### 1.1 简介
本开发样例演示如何用多线程使用MxVision流程编排能力来实现简单的目标检测功能。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：下载yolov3模型-[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ActionRecognition/ATC%20YOLOv3%28FP16%29%20from%20TensorFlow%20-%20Ascend310.zip)，解压后将获取到yolov3_tf.pb文件存放至${SDK_INSTALL_PATH}/mxVision/samples/mxVision/models/yolov3目录，并进入该目录。

**步骤2**：执行以下命令
```
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
```

**步骤3**：在MultiThread项目根目录下使用`mkdir models`创建目录，执行以下拷贝命令
```
cp -r ${SDK_INSTALL_PATH}/mxVision/samples/mxVision/models/yolov3 ./models
```

## 4 编译与运行
**步骤1**：配置pipeline

根据实际的SDK安装路径，修改EasyStream.pipeline文件第35、81、127行：
```
"modelPath": "../models/yolov3/yolov3_tf_bs1_fp16.om",
"postProcessConfigPath": "../models/yolov3/yolov3_tf_bs1_fp16.cfg",
"labelPath": "../models/yolov3/yolov3.names",
"postProcessLibPath": "${SDK安装路径}/mxVision/lib/libMpYOLOv3PostProcessor.so"
```

**步骤2**：将输入图片命名为test.jpg放到MultiThread项目根目录

**步骤3**：编译后处理插件，在项目根目录下执行
```
bash build.sh
```

**步骤4**：运行
```
./build/mxVisionMultiThread
```

**步骤5**：查看结果

运行成功后，会在屏幕上出现多线程目标检测的相关结果。