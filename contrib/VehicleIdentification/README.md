# 车型识别

## 1、 介绍

### 1.1 简介
在本系统中，目的是基于MindX SDK，在昇腾平台上，开发端到端车型识别的参考设计，实现对图像中的车辆进行车型识别的功能，并把可视化结果保存到本地，达到功能要求。

样例输入：带有车辆的jpg图片。

样例输出：框出并标有车辆车型与置信度的jpg图片。

项目适用于光照条件较好，车辆重叠程度低，车辆轮廓明显，且图片较清晰的测试图片

**注**：由于GoogLeNet_cars模型限制，仅支持识别在`./models/vehicle/car.names`文件中的 **431** 种车辆。且由于此模型为2015年训练，在识别2015年之后外观有较大变化的车辆时误差较大。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称 | 版本   |
| -------- | ------ |
|numpy|1.24.0|
|opencv-python|4.9.0.80|

### 1.5 代码目录结构与说明

本工程名称为VehicleIdentification，工程目录如下图所示：
```
├── models
│   ├── googlenet
│   │   ├── car.names
│   │   ├── googlenet.om
│   │   ├── updatemodel.py				# caffemodel旧版本升级新版本
│   │   ├── insert_op.cfg				# googlenet aipp转换配置
│   │   └── vehiclepostprocess.cfg		# googlenet后处理配置
│   ├── yolo
│   │   ├── aipp_yolov3_416_416.aippconfig
│   │   ├── coco.names
│   │   ├── yolov3_tf_bs1_fp16.cfg		# yolov3后处理配置
│   │   └── yolov3_tf_bs1_fp16.om
├── pipeline
│   └── identification.pipeline         # pipeline文件
├── vehiclePostProcess			        # 车型识别后处理库
│   ├── CMakeLists.txt
│   ├── VehiclePostProcess.cpp
│   └── VehiclePostProcess.h
├── input
│   ├── xxx.jpg							# 待检测文件
│   └── yyy.jpg
├── result
│   ├── xxx_result.jpg					# 运行程序后生成的结果图片
│   └── yyy_result.jpg
├── main.py
└── build.sh 							# 编译车型识别后处理插件脚本
```


## 2、 设置环境变量

在编译运行项目前，需要设置环境变量：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```

## 3、 准备模型

### 3.1 模型获取

**步骤1** 

1.在ModelZoo上下载YOLOv3模型。[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ActionRecognition/ATC%20YOLOv3%28FP16%29%20from%20TensorFlow%20-%20Ascend310.zip)

2.下载googlenet模型文件。[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/VehicleIdentification/models.zip)


### 3.2 模型转换

**步骤1** yolo模型转换

将在3.1节获取到的yolo模型压缩包解压，得到的文件夹TOLOv3_for_ACL中的模型pb文件yolov3_tf.pb存放至`./models/yolo/`。
在`./models/yolo`目录下执行以下命令

```bash
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"

# 说明：out_nodes制定了输出节点的顺序，需要与模型后处理适配。
```
执行完模型转换脚本后，会生成相应的.om模型文件。 执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

**步骤2** googlenet模型转换

将在3.1节获取到的models.zip压缩包解压，得到的after-modify.caffemodel模型文件存放至`./models/googlenet`。
在`./models/googlenet`目录下执行以下命令

```bash
atc --framework=0 --model=./deploy.prototxt --weight=./after-modify.caffemodel --input_shape="data:1,3,224,224" --input_format=NCHW --insert_op_conf=./insert_op.cfg --output=./googlenet --output_type=FP32 --soc_version=Ascend310P3
```

执行完模型转换脚本后，会生成相应的.om模型文件。 执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```


## 4、 编译与运行

示例步骤如下：

**步骤1** 

后处理插件库编译：在本项目目录`./VehicleIdentification`下执行
```bash
bash build.sh
```

编译成功后，生成的`libvehiclepostprocess.so`后处理库文件位于`./lib`目录下。执行后终端输出为：

```bash
[ 50%] Building CXX object CMakeFiles/vehiclepostprocess.dir/VehiclePostProcess.cpp.o
[100%] Linking CXX shared library {项目路径}/lib/libvehiclepostprocess.so
[100%] Built target vehiclepostprocess
```

**步骤2**

修改so文件权限：

```bash
chmod 640 ./lib/libvehiclepostprocess.so
```

**步骤3** 

自行选择一张或多张jpg文件，放入新建`./input`目录下，再执行
```bash
python3 main.py
```

**步骤4** 查看结果 
执行后会在终端按顺序输出车辆的车型信息和置信度

生成的结果图片中添加方框框出车辆，在方框左上角标出车型信息和置信度，按 **{原名}_result.jpg** 的命名规则存储在`./result`目录下，查看结果文件验证检测结果。
