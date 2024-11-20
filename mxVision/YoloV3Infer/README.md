# 基于C++ V2接口的yoloV3推理

## 1 介绍
### 1.1 简介
本开发样例基于MindX SDK实现了基于C++ V2接口的yoloV3推理样例，主要支持以下功能：

1. 图片读取解码：本样例支持JPG及PNG格式图片，使用图像处理单元进行解码。
2. 图片缩放/保存：使用图像处理单元相关接口进行图片的缩放，并输出一份缩放后的副本保存。
3. 模型推理：使用yoloV3网络识别输入图片中对应的目标，并打印输出大小。
4. 模型后处理：使用SDK中的模型后处理插件对推理结果进行计算，并输出相关结果，

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖
无


### 1.5 代码目录结构说明

本代码仓名称为YoloV3Infer，工程目录如下图所示：

```
|-- YOLOV3CPPV2
|   |-- CMakeLists.txt
|   |-- main.cpp
|   |-- README.md
|   |-- run.sh
|   |-- test.jpg    #测试使用的图片，需要用户自备
|   |-- model
|   |   |-- yolov3_tf_bs1_fp16.cfg
|   |   |-- aipp_yolov3_416_416.aippconfig
|   |   |-- yolov3_tf_bs1_fp16.OM       #OM模型需要按照手册下载并转换
|   |   |-- yolov3.names

```
## 2. 设置环境变量
```bash
#设置CANN环境变量
. ${install_path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```


## 3. 准备模型

**步骤1** 在ModelZoo上下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2** 将获取到的YOLOv3模型文件内的`.pb`文件存放至`YoloV3Infer/model/`下。

**步骤3** 模型转换

在`./model/`目录下执行以下命令

```bash
# 执行，转换YOLOv3模型
# Execute, transform YOLOv3 model. 310P
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
# 说明：out_nodes制定了输出节点的顺序，需要与模型后处理适配。
```

执行完模型转换脚本后，会生成相应的`.om`模型文件。 执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。


## 4 编译与运行

**步骤1：** 准备测试图片，在根目录下放置待测试图片，修改命名为`test.jpg`

**步骤2：** 执行运行脚本：

> `bash run.sh`

**步骤3：** 查看运行结果 

执行完毕后，以测试图片作为参数运行的结果会保存为`result.jpg`和`resized_yolov3_416.jpg`。 

## 5 常见问题
如果执行`bash run.sh`报错如下：
```
run.sh: line 2: $'\r': command not found
run.sh: line 3: cd: $'.\r\r': No such file or directory
run.sh: line 4: $'\r': command not found
run.sh: line 8: $'\r': command not found
run.sh: line 10: $'\r': command not found
```
则是文件格式需要转换，执行以下命令转换`run.sh`格式：
```
dos2unix run.sh
```