# 城市道路交通预测

## 1 介绍
### 1.1 简介

STGCN主要用于交通预测领域，是一种时空卷积网络，解决在交通领域的时间序列预测问题。在定义图上的问题，并用纯卷积结构建立模型，这使得使用更少的参数能带来更快的训练速度。本样例基于MindxSDK开发，是在STGCN模型的基础上对SZ-Taxi数据集进行训练转化，可以对未来一定时段内的交通速度进行预测。
论文原文：https://arxiv.org/abs/1709.04875

STGCN模型GitHub仓库：https://github.com/hazdzz/STGCN

SZ-Taxi数据集：https://github.com/lehaifeng/T-GCN/tree/master/data

SZ-Taxi数据集包含深圳市的出租车动向，包括道路邻接矩阵和道路交通速度信息。

软件方案介绍

基于MindX SDK的城市道路交通预测模型的推理流程为：

首先读取已有的交通速度数据集（csv格式）通过Python API转化为protobuf的格式传送给appsrc插件输入，然后输入模型推理插件mxpi_tensorinfer，最后通过输出插件mxpi_dataserialize和appsink进行输出。本系统的各模块及功能如表1.1所示：

表1.1 系统方案各子系统功能描述：

| 序号 | 子系统 | 功能描述     |
| ---- | ------ | ------------ |
| 1    | 数据输入 | 调用pythonAPI的SendProtobuf()函数和MindX SDK的appsrc输入数据|
| 2    | 模型推理 | 调用MindX SDK的mxpi_tensorinfer对输入张量进行推理 |
| 3    | 结果输出 | 调用MindX SDK的mxpi_dataserialize和appsink以及pythonAPI的GetProtobuf()函数输出结果 |

主程序流程

1、初始化流管理。
2、读取数据集。
3、向流发送数据，进行推理。
4、获取pipeline各插件输出结果。
5、销毁流。

### 1.2 支持的产品

本项目以昇腾Atlas300V pro、 Atlas300I pro为主要的硬件平台

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖
| 依赖软件  | 版本      |
| -------- | --------- |
| scipy    | 1.13.1    |
| numpy    | 1.24.0    |
| pandas   |   2.2.3 |
| google   | 3.0.0|
|protobuf  | 3.20.2|
|scikit-learn|1.5.2|

### 1.5 代码目录结构与说明

eg：本sample工程名称为STGCN，工程目录如下图所示：
```
├── data                # 数据目录
├── stgcn10.om          # 转化得到的om模型
├── pipeline
│   └── stgcn.pipeline
├── main.py             # 展示推理精度
├── predict.py          # 根据输入的数据集输出未来一定时段的交通速度
├── README.md
├── convert_om.sh       # onnx文件转化为om文件
└── results             # 预测结果存放
```

### 1.6 相关约束

模型的原始训练是基于SZ-Taxi数据集训练的，读取的图为深圳罗湖区156条主要道路的交通连接情况。因此对于针对罗湖区的自定义交通速度数据（大小为N×156，N>12），都能给出具有参考价值的未来一定时段的交通速度，从而有助于判断未来一段时间内道路的拥堵情况等。

## 2 设置环境变量


在编译运行项目前，需要设置环境变量：
```
#设置CANN环境变量（请确认install_path路径是否正确）
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh

#查看环境变量
env

```

## 3 准备模型

**步骤1** 模型下载
本项目提供训练好的onnx模型，下载链接如下：
```
https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/STGCN/stgcn10.onnx
```

**步骤2** onnx转化为om
根据实际路径修改convert_om.sh
```
bash convert_om.sh [model_path] stgcn10
参数说明：
model_path：onnx文件路径须自行输入。
stgcn10：生成的om模型文件名，转换脚本会在此基础上添加.om后缀。
```

## 4 运行

如果需要推理自定义的数据集(行数大于12行，列数为156列的csv文件)，运行predict.py，指令如下：
```
python predict.py [image_path] [result_dir]

参数说明：
image_path：验证集文件，如“data/sz_speed.csv”
result_dir：推理结果保存路径，如“results/”

例如： python predict.py data/sz_speed.csv results/
```
则会在results文件夹下生成代表预测的交通速度数据prediction.txt文件
这是通过已知数据集里过去时段的交通速度数据预测未来一定时间内的交通速度，无标准参考，所以只会输出代表预测的交通速度数据的prediction.txt文件，而没有MAE和RMSE等精度。
另外和main.py的运行指令相比少一个n_pred参数，因为已在代码中定义了确定数值，无需额外输入。

## 5 精度验证

### 5.1 数据集准备
SZ-Taxi数据集下载链接：https://github.com/lehaifeng/T-GCN/tree/master/data
将sz_speed.csv放置在工程目录/data下

### 5.2 运行main.py
运行main.py可以在sz_speed.csv的测试集上获得推理精度，指令如下：
```
python main.py [image_path] [result_dir] [n_pred]

参数说明：
image_path：验证集文件，如“data/sz_speed.csv”
result_dir：推理结果保存路径，如“results/”
n_pred：预测时段，如9

例如： python main.py data/sz_speed.csv results/ 9
注意：sz_speed.csv文件的第一行数据为异常数据，需要手动删除
```
最后sz_speed.csv测试集的推理预测的结果会保存在results/predictions.txt文件中，实际数据会保存在results/labels.txt文件中。
推理精度会直接显示在界面上。