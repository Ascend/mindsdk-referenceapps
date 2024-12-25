# PraNet医学分割

## 1 介绍

### 1.1 简介

PraNet是一种针对息肉分割任务需求设计的，名为并行反向注意力的深度神经网络。
基于并行反向注意力的息肉分割网络（PraNet），利用并行的部分解码器（PPD）在高级层中聚合特征作为初始引导区域，
再使用反向注意模块（RA）挖掘边界线索。

本项目基于MindSDK框架实现了PraNet模型的推理。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的VisionSDK版本、CANN版本、Driver/Firmware版本如下所示：
| VisionSDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖

第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用pip3 install * 安装以下依赖。

|软件名称    | 版本     |
|-----------|----------|
| numpy    | 1.24.0   |
| tqdm   | 4.66.5    |
| imageio  | 2.36.0   |

### 1.5 相关约束

在医疗图像处理领域，PraNet针对息肉识别需求而设计。Pranet网络能够对息肉图片进行语义分割，功能正常，且精度达标。但是在以下情况下，分割效果不够理想：
- 当息肉相比整张图片面积很小时，分割效果不够理想，边缘会比较模糊。
- 当息肉大面具处于整张图片的边缘时，有一定概率分割失败，效果较差。

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型

**步骤1：** 下载PraNet原始模型-[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/PranetSegementation/ATC%20PraNet%28FP16%29%20from%20Pytorch%20-%20Ascend310.zip)，并将获取到的PraNet-19.onnx文件存放至本案例代码的PraNetSegmentation/model目录下。

**步骤2：** 进入PraNetSegmentation/model目录执行以下命令
```
atc --model=PraNet-19.onnx --output=./PraNet-19_bs1 --framework=5 --input_shape="actual_input_1:1,3,352,352" --soc_version=Ascend310P3 --input_format=NCHW --output_type=FP32 --insert_op_conf=./pranet.aippconfig
```
## 4 编译与运行

**步骤1：** 编译后处理插件so

进入PraNetSegmentation/plugin/postprocess/目录，执行命令
```
bash build.sh
```

**步骤2：** 准备输入图片路径

输入图片命名为test.jpg放入根目录。

**步骤3：** 运行

在根目录下执行

```
python3 main.py
```

**步骤4：** 查看结果

在infer_result目录可以查看图片结果。
