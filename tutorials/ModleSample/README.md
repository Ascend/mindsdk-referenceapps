## MxVision快速入门--Model接口基本使用教程

## 1、 介绍

### 1.1 简介
Model类，作为模型的抽象，持有模型推理的资源，并主要开放推理接口。

本文主要使用C++和python接口的方式，根据传入的模型文件构造Model，然后调用相关接口输出模型信息。使用到的接口主要有：
- C++：
```
Model::GetInputFormat(); // 获得模型输入的数据组织形式(NHWC 或者 NCHW)。
Model::GetInputTensorNum(); // 获得模型的输入个数。
Model::GetOutputTensorNum(); // 获得模型的输出个数。
Model::GetInputTensorShape(uint32_t index = 0); // 获得模型的输入个数。
Model::GetOutputTensorShape(uint32_t index = 0); // 获得模型输出的对应Tensor的数据shape信息。
Model::Infer(std::vector<Tensor>& inputTensors, std::vector<Tensor>& outputTensors, AscendStream &stream = AscendStream::DefaultStream()); // 推理接口
```

- python：
```
input_shape(index: int) # 获得模型输入的对应Tensor的数据shape信息
output_shape(index: int) # 获得模型输出的对应Tensor的数据shape信息。
input_dtype(index: int) # 获得模型输入的对应Tensor的数据类型信息。
infer(tensorList: List) # 通过输入Tensor列表进行模型推理
```
- python部分还使用了numpy相关接口实现了Tensor与numpy数组之间的生成和转换。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称      | 版本             |
| ------------- | ---------------- |
| numpy         | 2.0.2           |

### 1.5 三方依赖

本项目工程目录如下图所示：
```angular2html
|-------- C++
|           |---- main.cpp
|           |---- CMakeLists.txt     
|           |---- run.sh 
|-------- python
|           |---- main.py
|-------- model
|-------- README.md
```  

## 2、 设置环境变量

在编译运行项目前，需要设置环境变量：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```

## 3、 准备模型

**步骤1**：模型文件下载

本项目意在为开发者介绍使用mxVision软件包中Model相关的C++、python接口使用样例。使用的模型为[RGB图像的夜间增强参考设计](https://gitee.com/ascend/mindxsdk-referenceapps/tree/master/contrib/IAT)中用到的模型。
原始pth模型源码[地址](https://github.com/cuiziteng/illumination-adaptive-transformer)
本文提供已从pth模型转换好的onnx模型直接使用：[IAT_lol-sim.onnx](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/IAT/IAT_lol-sim.onnx)
下载后放到项目根目录的model文件夹下。

**步骤2**：模型转换

将模型转换为om模型，在model文件夹下，执行以下命令生成om模型：
```
atc --framework=5 --model=./IAT_lol-sim.onnx --input_shape="input_1:1,3,400,600" --output=IAT_lol-sim --soc_version=Ascend310P3
```
执行完模型转换脚本后，会生成相应的IAT_lol-sim.om模型文件。 执行后终端输出为（模型转换时出现的warn日志可忽略）：

```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

## 4、 编译与运行

### 4.1 C++样例运行

**步骤1**：进入`C++`文件夹，执行以下命令：
```
bash run.sh
```

**步骤2**：查看结果
命令执行成功后可在屏幕看到模型信息输出
```
Input format: NCHW
model input tensor num: 1
model output tensor num: 1
inputShape: 1 3 400 600
ouputShape: 1 3 400 600 
```

### 4.2 python样例运行

**步骤1**：进入`python`文件夹，执行以下命令：
```
python3 main.py
```

**步骤2**：查看结果
命令执行成功后可在屏幕看到模型信息输出
```
input num: 1
output num: 1
input Tensor shape list: [1, 3, 400, 600]
output Tensor shape list: [1, 3, 400, 600]
Input dtype: dtype.float32
output numpy array shape (1, 3, 400, 600)
```





