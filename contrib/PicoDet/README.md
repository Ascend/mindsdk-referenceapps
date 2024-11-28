# PP-PicoDet目标检测

## 1 介绍
### 1.1 简介
本案例基于mxVision，在昇腾平台上，使用PicoDet模型开发端到端目标检测的参考设计，并把可视化结果保存到本地，达到功能要求。本样例适用于通用场景的jpg/jpeg图片目标检测。

基于mxVision的目标检测业务流程为：待检测图片通过 appsrc 插件输入，然后使用图像解码插件 mxpi_imagedecoder 对图片进行解码，再通过图像缩放插件 mxpi_imageresize 将图像缩放至满足检测模型要求的输入图像大小要求，缩放后的图像输入模型推理插件 mxpi_tensorinfer 得到推理结果，推理结果输入 mxpi_objectpostprocessor 插件进行后处理，得到输入图片中所有的目标框位置和对应的置信度。最后通过输出插件 appsink 获取检测结果，并在外部进行可视化，将检测结果标记到原图上，本系统的各模块及功能描述如表1所示：

表1 系统方案各模块功能描述：

| 序号 | 子系统         | 功能描述                                                     |
| ---- | -------------- | ------------------------------------------------------------ |
| 1    | 图片输入       | 获取 jpg 格式输入图片                                        |
| 2    | 图片解码       | 解码图片                                                     |
| 3    | 图片缩放       | 将输入图片放缩到模型指定输入的尺寸大小                       |
| 4    | 模型推理       | 对输入张量进行推理                                           |
| 5    | 目标检测后处理 | 从模型推理结果计算检测框的位置和置信度，并保留置信度大于指定阈值的检测框作为检测结果 |
| 6    | 结果输出       | 获取检测结果                                                 |
| 7    | 结果可视化     | 将检测结果标注在输入图片上                                   |

### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。

### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 


### 1.4 代码目录结构与说明

本工程名称为 PicoDet，工程目录如下所示：

```
├── build.sh
├── colorlist.txt
├── images
│   ├── sdk流程图.png
│   └── 精度结果.png
├── main.py
├── models
│   ├── picodet.aippconfig
│   └── picodet.cfg
├── picodet.pipeline
├── PicodetPostProcess
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── PicodetPostProcess.cpp
│   └── PicodetPostProcess.h
└── README.md
```

## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：


```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
# mxVision-path: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
```

## 3 准备模型
**步骤1** 下载模型相关文件

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/Picodet/picodet_s_320_coco.onnx)下载得到picodet_s_320_coco.onnx文件，将该文件放入项目根目录下的models目录。

**步骤2** 转换模型格式

进入到项目根目录下的models目录，执行以下命令：
```
atc --model=picodet_s_320_coco.onnx --output=picodet --output_type=FP32 --soc_version=Ascend310P3 --input_shape="image:1,3,320,320"  --insert_op_conf=picodet.aippconfig --input_format=NCHW --framework=5
```
执行该命令后会在当前文件夹下生成项目需要的模型文件 picodet.om。


## 4 编译与运行
**步骤1**  编译后处理插件，在项目根目录下执行如下命令

```
bash build.sh
```

**步骤2**  下载标签文件coco.names

下载文件[coco2014.names](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/contrib/Collision/model/coco.names)，将下载的标签文件放入models目录中并修改文件名为**coco.names**

**步骤3**  在项目根目录执行以下指令创建输入、输出目录

```
mkdir input
mkdir output
```
创建成功后，将一张待检测的jpg/jpeg图片放入项目根目录下的input目录

**步骤4**  执行推理

```
python3 main.py ./input ./output
```

**步骤5** 查看结果

检测的同名可视化结果图像将保存在项目根目录下的output目录，打开图片查看即可观察结果。

