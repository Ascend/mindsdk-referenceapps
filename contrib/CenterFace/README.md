# 目标和关键点检测

## 1 介绍
### 1.1 简介

本样例基于mxVision开发，在昇腾芯片上对输入图片进行目标和关键点检测，将检测结果可视化并保存，支持多档次的动态分辨率输入。

目标检测指对输入图片输出目标检测框，关键点检测则指输出包括双眼，鼻尖和嘴巴两边在内的五个关键点。本方案模型推理采用CenterFace(一个轻量化的目标检测模型，同时实现了目标检测+关键点检测)，对模型的输出开发两个后处理插件——目标检测插件和关键点检测插件，分别对目标目标框和关键点信息进行了可视化处理。

基于mxVision的目标检测和关键点模型(动态分辨率)推理流程为：

待检测图片通过appsrc插件输入，然后使用图像解码mxpi_imagedecoder对图片进行解码，再通过图像缩放插件mxpi_imageresize将图形缩放至合适的分辨率档位，缩放后的图形输入模型推理插件mxpi_tensorinfer得到模型输出。本项目开发的模型后处理插件包括目标检测和关键点检测两部分；模型推理得到的结果分别送入两个后处理插件。目标检测插件用来得到目标目标框，关键点检测插件得到五个关键点。目标检测插件的结果可同图片mxpi_imagedecoder结果送入OSD可视化插件，和关键点检测插件通过appsink完成整个pipeline的流程，最后在外部使用opencv对目标和关键点进行可视化描绘并保存。本系统的各模块及功能如表1所示：

表1 系统方案各模块功能描述：

| 序号 | 子系统           | 功能描述                               |
| ---- | ---------------- | -------------------------------------- |
| 1    | 图片输入         | 获取jpg格式输入图片                    |
| 2    | 图片解码         | 解码图片为YUV420sp                     |
| 3    | 图片缩放         | 将输入图片缩放到合适的分辨率档位       |
| 4    | 模型推理         | 对输入张量进行推理                     |
| 5    | 目标检测后处理   | 对模型推理输出计算生成目标检测框       |
| 6    | 目标关键点后处理 | 对模型推理输出计算出目标关键点         |
| 7    | OSD              | 融合图片和目标检测后处理信息           |
| 8    | 结果可视化       | 将目标检测和关键点结果可视化保存为图片 |

本方案从人体方向，人体遮挡程度，人体个数，人体大小，图片清晰程度，灰度图片检测效果几个方面对模型进行了功能测试，在绝大部分情形下可以准确检测，存在以下两种异常情形：

1. 侧面目标且存在遮挡时会出现无法检测出目标的情况。

2. 图片尺寸与模型尺寸不匹配时，检测效果难以符合预期，请选择合适的分辨率以获取更好的检测效果。

### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。


### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 代码目录结构与说明

项目名称为CenterFace，项目目录如下图所示：

```
.
├── build.sh
├── C++
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── main.cpp
│   └── run.sh
├── model
│   ├── centerface_aipp.cfg
│   ├── centerface.cfg
│   ├── CenterFace.pipeline
│   └── person.names
├── plugins
│   ├── FaceDetectPostProcessor
│   │   ├── build.sh
│   │   ├── CMakeLists.txt
│   │   ├── FaceDetectPostProcessor.cpp
│   │   └── FaceDetectPostProcessor.h
│   └── KeyPointPostProcessor
│       ├── build.sh
│       ├── CenterfaceKeyPointPostProcessor.cpp
│       ├── CenterfaceKeyPointPostProcessor.h
│       └── CMakeLists.txt
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
步骤1 下载模型相关文件

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/CenterFaceWithDynamicResolution/centerface_offical.onnx)下载得到centerface_offical.onnx文件，将该文件放入项目根目录下的model目录。

步骤2 转换模型格式

进入到项目根目录的model目录下，执行以下命令：
```
atc --model=centerface_offical.onnx --output=centerface_offical --dynamic_image_size="768,1024;800,800;1024,768;864,1120;1120,864;960,1216;1216,960;1056,1312;1312,1056;1152,1408;1408,1152;1248,1504;1504,1248;1344,1600;1600,1344;1440,1696;1696,1440;1536,1792;1792,1536;1632,1888;1888,1632;1728,1984;1984,1728;1824,2080;2080,1824"   --soc_version=Ascend310P3 --input_shape="input.1:1,3,-1,-1" --input_format=NCHW --framework=5 --insert_op_conf=centerface_aipp.cfg
```
执行该命令后会在当前文件夹下生成项目需要的模型文件 centerface_offical.om。


## 4 编译与运行

**步骤1：** 编译

进入mxVision安装目录的`operators/opencvosd`目录下执行以下命令：

```
bash generate_osd_om.sh
```

进入项目根目录，执行以下命令：
  ```bash
  bash build.sh
  ```

**步骤2：** 运行  

进入项目根目录的C++目录下，执行以下命令：

  ```bash
  ./Main ${jpg图片路径}  # ${jpg图片路径}为待检测图片的真实路径
  ```

**步骤3：** 查看结果  

检测后的可视化结果图片保存在项目根目录的C++/result目录下，打开图片查看检测结果。