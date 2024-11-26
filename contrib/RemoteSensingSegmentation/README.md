# 遥感影像地块分割

## 1 介绍
### 1.1 简介
本开发样例基于MindX SDK实现了对遥感影像地图进行的语义分割能力，并以可视化的形式返回输出。

本样例使用DANet和Deeplabv3+，其中两模型均使用了pytorch官方提供的resnet101预训练模型作为backbone,
使用SGDR对模型进行训练,选择多个局部最优点的结果进行集成。


### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用pip3 install * 安装以下依赖。

| 软件名称                   | 版本        |
|------------------------|-----------|
| numpy                  | 1.24.0    |
| opencv-python-headless | 4.10.0.84 |
| Pillow                 | 9.4.0     |


### 1.5 代码目录结构说明

本代码仓名称为RemoteSensingSegmentation，工程目录如下图所示：

```
|--RemoteSensingSegmentation
|-------- config
|           |---- configure.cfg                     // 模型转换配置文件
|-------- models                                    // 模型存放文件目录(需要用户创建)
|-------- test_set                                  // 测试集图像目录(需要用户自行创建)
|           |---- *.jpg                             // 15张jpg格式的测试集遥感图片(需要用户下载)
|-------- pipeline
|           |---- segmentation.pipeline             // 遥感影像地块分割的pipeline文件
|-------- result                                    // 语义分割结果存放处
|           |---- final                             // 对比结果图存放目录,对比结果图（左为输入原图 右为结果图）
|           |---- temp_result                       // 单一结果图存放目录,仅有单一结果图
|-------- util
|           |---- model_conversion.sh               // 模型转换脚本 *.onxx -> *.om
|           |---- transform_model_util.py           // 模型转换工具 *.pth -> *.onxx
|           |---- visual_utils.py                   // 语义分割可视化工具
|-------- main.py                                   // 遥感影像地块分割检测样例
|-------- README.md                                 // ReadMe 
```


### 1.6 相关约束

输入的遥感影像地图仅支持大小为256*256的jpg文件。


## 2. 设置环境变量
```bash
#设置CANN环境变量
. ${install_path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```

## 3. 准备模型

**步骤1** 通过[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/RemoteSensingSegmentation/models.zip)下载模型文件包`models.zip`，并放在项目根目录`RemoteSensingSegmentation/`下。

**步骤2** 通过`unzip`解压模型包，可在项目根目录`RemoteSensingSegmentation/`下找到文件夹`models`，
文件夹内应该有文件`DANet.onnx`与`Deeplabv3.onnx`。

**步骤3** 转换模型

在`RemoteSensingSegmentation/util`目录下运行模型转换脚本：

1. 如不是可执行脚本，先将其转换`chmod +x model_conversion.sh`
2. 转换格式：`dos2unix model_conversion.sh`
3. 执行脚本`./model_conversion.sh`

执行成功后终端输出为：
```bash
ATC start working now, please wait for a moment.
....
ATC run success, welcome to the next use.

ATC start working now, please wait for a moment.
...
ATC run success, welcome to the next use.
```
并且在`RemoteSensingSegmentation/models/`下可以找到文件`DANet.om`与`Deeplabv3.om`。

## 4 运行

**步骤1** 准备数据集

请下载 [测试集图片](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/RemoteSensingSegmentation/data.zip)，
并放在项目根目录`RemoteSensingSegmentation/`下解压：
```bash
unzip data.zip
```
解压后能在根目录下找到文件夹`test_set`，内有15张符合输入格式要求的jpg遥感地图图片文件。

**步骤2** 在工程目录`RemoteSensingSegmentation/`下执行：
```bash
python3 main.py ${测试图片路径} ${是否开启对比图输出} ${输出结果路径}
e.g.: python3 main.py test_set/test_1.jpg True result/final/result.jpg
```
**步骤3** 查看结果

如果开启了对比图输出，运行完毕后, 
带有原图的对比图结果保存在目录`RemoteSensingSegmentation/result/final/`下，
单一结果图保存在目录`RemoteSensingSegmentation/result/temp_result/`下。

若没有开启对比图输出，运行完毕后, 只有单一结果图保存在目录`RemoteSensingSegmentation/result/temp_result/`下。
