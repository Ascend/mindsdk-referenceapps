# 基于Vision SDK的AdaBins单目深度估计

## 1 介绍

### 1.1 简介
本案例是基于AdaBins室内模型的单目深度估计，输出为对应输入图像的深度图（灰度图形式）。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：
| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：下载模型-[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/MonocularDepthEstimation/AdaBins_nyu.onnx)，将获取到的.onnx文件存放至本案例代码的MonocularDepthEstimation/model 目录下。

**步骤2**：进入MonocularDepthEstimation/model目录执行以下命令
```
atc --model=./AdaBins_nyu.onnx --framework=5 --output=./AdaBins_nyu --soc_version=Ascend310P3 --insert_op_conf=./aipp_adabins_640_480.aippconfig --log=error
```

## 4 运行
**步骤1**：准备输入图片

将输入图片命名为test.jpg放入项目根目录下

**步骤2**：运行
```
python3 main.py
```
**步骤3**：查看结果

在当前目录生成result.jpg