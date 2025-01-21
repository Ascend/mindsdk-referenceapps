# 黑白图像上色

## 1 介绍

### 1.1 简介

在智能手机越来越普及的今天，拍摄一张色彩鲜艳、清晰的照片轻而易举。但是老照片没有如此“幸运”，大多为黑白。借助人工智能，可以一定程度上帮助老照片还原原来色彩。

本项目是黑白图像上色应用，旨在华为Atlas300推理芯片上实现输入黑白图像，自动对黑白图像进行上色，还原彩色图像。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：

| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用pip3 install 安装以下依赖。
|软件名称    | 版本        |
|-----------|-----------|
| numpy     | 1.24.0    |
| opencv-python   | 4.9.0.80 |
### 1.5 代码目录结构说明
```
.
├── data         //需要手动创建
├── model        //需要手动创建
│   ├── colorization.caffemodel
│   └── colorization.prototxt
├── pipeline
│   └── colorization.pipeline
├── README.md
├── scripts
│   ├── atc_run.sh
└── src
    └── main.py
```

## 2 设置环境变量

```bash
#设置CANN环境变量，ascend-toolkit-path为cann安装路径
. ${ascend-toolkit-path}/set_env.sh

#设置Vision SDK 环境变量，SDK-path为Vision SDK 安装路径
. ${SDK-path}/set_env.sh
```

## 3 准备模型

**步骤1:** 获取face_mask_detection的原始模型

本工程原模型是caffee模型，需要使用atc工具转换为om模型，模型和所需权重文件已上传，在项目根目录下使用以下命令下载并解压

```
mkdir model
cd model
wget https://mindx.sdk.obs.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/Colorization/model.zip
unzip model.zip
```

**步骤2:** 模型转换

下载并解压完毕后，在项目根目录下进入scripts目录执行模型转换脚本

```
cd scripts
bash atc_run.sh
```
执行完模型转换后，若提示如下信息说明模型转换成功。

```
ATC run success, welcome to the next use.
``` 
## 4 运行

**步骤1:** 获取测试图片

在项目根目录下执行：

```
mkdir data
cd data
wget https://c7xcode.obs.cn-north-4.myhuaweicloud.com/models/colorization_picture-python/dog.png
```

**步骤2:** 修改pipeline文件

根据使用的设备id，修改项目根目录下pipeline/colorization.pipeline中第四行的deviceId：
```
"deviceId": "0"                # 根据实际使用的设备id修改
```
**步骤3:** 执行程序
```
cd src
python3 main.py
```
**步骤4:** 查看结果

输出结果保存在src/out_dog.png，下载至本地查看图片上色是否合理


