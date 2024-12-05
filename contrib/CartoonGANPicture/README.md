# 图像卡通风格迁移

## 1 介绍

### 1.1 简介

本开发项目基于mxBase，在昇腾平台上，开发端到端的图像卡通风格迁移参考设计，实现图像卡通化功能。

图像卡通风格迁移项目实现：输入图片，通过调用mxBase提供的接口，使用DVPP进行图像解码，解码后获取图像数据，然后经过图像缩放，满足模型的输入要求；将缩放后的图像数据输入cartoonization模型进行推理，模型输出经过后处理后，得到生成的卡通化的图像，将其可视化，得到最后的卡通图像。

技术实现流程图如下：

![image-20210929114019494](image.png)

表1.1系统方案中各模块功能：

| 序号 | 子系统       | 功能描述                                     |
| ---- | ------------ | -------------------------------------------- |
| 1    | 设备初始化   | 芯片与模型参数初始化                         |
| 2    | 图片输入     | 读取文件夹中的图片路径                       |
| 3    | 图像解码     | 调用DvppJpegDecode()函数完成图像解码         |
| 4    | 图像缩放     | 调用VpcResize()接口完成图像缩放              |
| 5    | 模型推理     | 调用ModelInferenceProcessor 接口完成模型推理 |
| 6    | 后处理       | 获取模型推理输出张量BaseTensor，进行后处理   |
| 7    | 保存结果     | 将处理后得到的卡通化图像可视化保存至文件夹中 |
| 8    | 设备去初始化 | 推理卡设备去初始化。                         |

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro。

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 代码目录结构与说明

工程目录如下图所示：

data文件及目录下的images、model文件夹需要用户在项目运行前手动创建。

```
|-----CartoonGANPicture
|     |---CartoonGANPicture.cpp
|     |---CartoonGANPicture.h
|-----data        // 需用户自己创建
|     |---images  // 推理图片存放路径，需用户自己创建
|     |---model   // 模型存放路径，需用户自己创建
|     |---output  // 推理结果存放路径，由程序运行生成
|-----build.sh    // 编译脚本
|-----CMakeLists.txt
|-----image.png   // 技术实现流程图
|-----main.cpp
|-----README.md
```

### 1.5 相关约束

- 适用场景：本项目支持通用场景下的jpg图片卡通化。为了保证卡通化效果，建议使用图像线条简单，细节较少的图片进行推理。
- Dvpp图片解码接口只支持图片格式为jpg、jpeg，并且对图片分辨率在[32，8192]范围内的图片的解码，图片格式不支持或分辨率不符合约束的图片无法成功进行推理。

## 2 设置环境变量

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh       # sdk安装路径，根据实际安装路径修改
```

## 3 模型转换

**步骤1：** 模型下载。将下载好的模型和配置文件解压后放入`data/model/`文件夹下。[模型及配置文件下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/CartoonGANPicture/model.zip)

**步骤2：** 模型转换。进入`data/model/`文件夹，运行如下模型转换命令实现模型转换：

```
atc --output_type=FP32 --input_shape="train_real_A:1,256,256,3"  --input_format=NHWC --output="cartoonization" --soc_version=Ascend310P3 --insert_op_conf=insert_op.cfg --framework=3 --model="cartoonization.pb" --precision_mode=allow_fp32_to_fp16
```

若终端输出：
```
ATC start working now, please wait for a moment.

ATC run success, welcome to the next use.
```

表示命令执行成功。

## 4 编译与运行

**步骤1：** 进入项目主目录，执行如下命令编译程序：

```
bash build.sh
```

**步骤2：** 将需要执行推理的图片放置在`data/images/`文件夹下，在项目主目录下执行如下命令完成推理：

```
./CartoonGAN_picture ./data/images
```

**步骤3：** 查看结果。推理完成后的图片存放在生成的`data/output`文件夹下。

## 5 常见问题

### 5.1 图片解码失败

**问题描述：**

Dvpp图片解码接口只支持图片格式为jpg、jpeg，并且对图片分辨率在[32，8192]范围内的图片的解码，图片格式不支持或分辨率不符合约束的图片无法成功进行推理。

**解决方案：**

使用规格约束内的图片进行推理。