# EfficientDet 目标检测
## 1. 介绍

### 1.1 简介
EfficientDet 目标检测后处理插件基于 mxVision 开发，对图片中的不同类目标进行检测，将检测得到的不同类的目标用不同颜色的矩形框标记。输入一幅图像，可以检测得到图像中大部分类别目标的位置。本方案使用在 COCO2017 数据集上训练得到的 EfficientDet 模型进行目标检测，数据集中共包含 90 个目标类，包括行人、自行车、公共汽车、手机、沙发、猫、狗等，可以对不同类别、不同角度、不同密集程度的目标进行检测。

### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。


### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称 | 版本   |
| -------- | ------ |
| webcolors| 1.11.1 |

### 1.5 代码目录结构与说明

本工程名称为 EfficientDet，工程目录如下所示：
```
.
├── build.sh
├── images
│   └── DetectionPipeline.png
├── postprocess
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── EfficientdetPostProcess.cpp
│   └── EfficientdetPostProcess.h
├── python
│   ├── main.py
│   ├── models
│   │   ├── aipp-configs
│   │   │   └── insert_op_d0.cfg
│   │   ├── coco.names
│   │   └── efficient-det.cfg
│   └── pipeline
│       └── EfficientDet-d0.pipeline
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

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/EfficientDet/models.zip)下载得到simplified-efficient-det-d0-mindxsdk-order.onnx文件，将该文件放入项目根目录的python/models目录下。

步骤2 转换模型格式

进入到项目根目录的python/models目录下，执行以下命令：
```
atc --model=./simplified-efficient-det-d0-mindxsdk-order.onnx --framework=5 --output=./efficient-det-d0-mindxsdk-order --soc_version=Ascend310P3 --input_shape="input:1, 3, 512, 512" --input_format=NCHW --output_type=FP32 --out_nodes='Concat_10954:0;Sigmoid_13291:0' --log=error --insert_op_conf=./aipp-configs/insert_op_d0.cfg
```
执行该命令后会在当前文件夹下生成项目需要的模型文件 efficient-det-d0-mindxsdk-order.om。



## 4. 编译与运行

**步骤1：编译**

在项目目录下执行bash build.sh命令。



**步骤2：运行**

将一张jpg图片放在项目目录根目录的python目录下，命名为 img.jpg。进入项目根目录下的python目录，执行命令如下：

执行命令：
```
python3 main.py
```

**步骤3：查看结果**

执行成功后在当前目录下生成检测结果文件 img_detect_result.jpg，查看结果文件验证检测结果。

