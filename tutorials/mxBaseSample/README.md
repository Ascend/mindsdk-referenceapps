# 基于MxBaseV1接口的yoloV3目标检测

## 1 介绍
### 1.1 简介

开发样例是基于mxBase开发的端到端推理的C++应用程序，通过 yolov3 进行目标检测，并把可视化结果保存到本地。其中包含yolov3的后处理模块开发。

该Sample的主要处理流程为：

Init > ReadImage >Resize > Inference >PostProcess >DeInit

### 1.2 支持的产品

本项目支持昇腾Atlas 500 A2。

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- |---------| -------------- |
| 5.0.0   |7.0.0 |  23.0.0  |
| 6.0.RC3   | 8.0.RC3 |  24.1.RC3  |

### 1.4 三方依赖
无


## 2 设置环境变量

```bash
#设置CANN环境变量（请确认install_path路径是否正确）
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```



## 3 准备模型

**步骤1：** 通过[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ActionRecognition/ATC%20YOLOv3%28FP16%29%20from%20TensorFlow%20-%20Ascend310.zip)下载YOLOv3模型。


**步骤2：** 将获取到的YOLOv3模型的pb文件放在`mxBaseSample/model/`下。

**步骤3** 执行模型转换命令

```bash
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310B1 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
```
- 执行完模型转换脚本后，若提示如下信息说明模型转换成功，并可以在`mxBaseSample/model/`下找到名为`yolov3_tf_bs1_fp16.om`模型文件。

```
ATC run success, welcome to the next use.
```  

## 4 编译与运行
**步骤1:** 在`mxBaseSample/`下执行如下编译命令：
```bash
bash build.sh
```
**步骤2：** 将jpg格式的推理图片命名为`test.jpg`， 并放入`mxBaseSample/`目录下，执行：
```bash
./mxBase_sample ./test.jpg
```
**步骤3：** 查看结果

结果以`result.jpg`的形式保存在`mxBaseSample/`目录下。
