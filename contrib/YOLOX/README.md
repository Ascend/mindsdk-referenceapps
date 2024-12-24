# YOLOX 目标检测
## 1 介绍

### 1.1 简介
YOLOX 目标检测后处理插件基于 VisionSDK 开发，对图片中的不同类目标进行检测，将检测得到的不同类的目标用不同颜色的矩形框标记。输入一幅图像，可以检测得到图像中大部分类别目标的位置。本方案使用在 COCO2017 数据集上训练得到的 YOLOX-Nano 模型进行目标检测，数据集中共包含 80 个目标类，包括行人、自行车、公共汽车、手机、沙发、猫、狗等，可以对不同类别、不同角度、不同密集程度的目标进行检测。

整体业务流程为：待检测图片通过 appsrc 插件输入，然后使用图像解码插件 mxpi_imagedecoder 对图片进行解码，再通过图像缩放插件 mxpi_imageresize 将图像缩放至满足检测模型要求的输入图像大小要求，缩放后的图像输入模型推理插件 mxpi_tensorinfer 得到推理结果，推理结果输入 mxpi_objectpostprocessor 插件进行后处理，得到输入图片中所有的目标框位置和对应的置信度。最后通过输出插件 appsink 获取检测结果，并在外部进行可视化，将检测结果标记到原图上，本系统的各模块及功能描述如表1所示：

表1.1 系统方案各模块功能描述：

| 序号 | 子系统 | 功能描述     |
| ---- | ------ | ------------ |
| 1    | 图片输入    | 获取 jpg 格式输入图片 |
| 2    | 图片解码    | 解码图片 |
| 3    | 图片缩放    | 将输入图片放缩到模型指定输入的尺寸大小 |
| 4    | 模型推理    | 对输入张量进行推理 |
| 5    | 目标检测后处理    | 从模型推理结果计算检测框的位置和置信度，并保留置信度大于指定阈值的检测框作为检测结果 |
| 6    | 结果输出    | 获取检测结果|
| 7    | 结果可视化    | 将检测结果标注在输入图片上|

YOLOX 的后处理插件接收模型推理插件输出的特征图，该特征图为三张不同分辨率的特征图拼接而成，形状大小为1 x n x 85,其中 n 为三张网络模型输出特征图的像素点数总和，85 为 80 （数据集分类数）+ 4 （目标框回归坐标点）+ 1 （正类置信度）。本项目方案的技术流程图如下：

<center>
    <img src="./images/pipeline_pre.png">
    <br>
</center>


### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro


### 1.3 支持的版本

本样例配套的VisionSDK版本、CANN版本、Driver/Firmware版本如下所示：

| VisionSDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖 

| 软件名称   | 版本       |
|--------|----------|
| webcolors | 24.8.0   |

### 1.5 代码目录结构说明

本工程名称为 YOLOX，工程目录如下所示：
```
.
├── build.sh
├── images
│   ├── MindXSDKValueError.png
│   ├── permissionerror.png
│   ├── pipeline_pre.png
│   └── warning.png
├── postprocess
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── YoloxPostProcess.cpp
│   └── YoloxPostProcess.h
├── python
│   ├── Main
│   │   ├── eval_pre_post.py
│   │   ├── pre_post.py
│   │   ├── visualize.py
│   │   └── preprocess.py
│   ├── models
│   │   ├── aipp-configs
│   │   │   └── yolox_bgr.cfg
│   │   ├── conversion-scripts              # 需用户手动创建文件夹，并将下载的onnx模型存放在该文件夹下
│   │   ├── yolox_eval.cfg
│   │   └── coco.names                      # 需要下载，下载链接在下方 
│   ├── test_img                            # 需用户手动创建文件夹
│   │   └── test.jpg                        # 需要用户自行添加测试数据
│   └── pipeline
│       └── pre_post.pipeline
└── README.md
```

注：coco.names文件源于[链接](../Collision/model/coco.names)的coco.names文件，将这个文件下载后，放到python/models目录下。

### 1.6 相关约束

经过测试，该项目适用于一般的自然图像，对含单个清晰目标的图像、灰度图像、模糊图像以及高分辨率的图像均有较好的检测效果，而用于含大量小目标的图像、光照不佳的图像和存在大量遮挡的图像时，有轻微的漏检现象。

## 2 设置环境变量

MindSDK 环境变量:

```
. ${SDK-path}/set_env.sh    # SDK-path: mxVision SDK 安装路径
```

CANN 环境变量：

```
. ${ascend-toolkit-path}/set_env.sh     # ascend-toolkit-path: CANN 安装路径。
```

## 3 准备模型

本项目中采用的模型是 YOLOX 模型，参考实现代码：https://github.com/Megvii-BaseDetection/YOLOX ， 选用的模型是该 pytorch 项目中提供的模型 yolox-Nano.onnx，模型下载链接：https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/YOLOX/yolox_nano.onnx 。 本项目使用模型转换工具 ATC 将 onnx 模型转换为 om 模型。

**步骤1：** 从上述项目链接中下载 onnx 模型 yolox_nano.onnx 至 ``python/models/conversion-scripts`` 文件夹下。


**步骤2：** 将该模型转换为om模型，具体操作为： ``python/models/conversion-scripts`` 文件夹下, 执行atc指令如下：

```
atc --model=yolox_nano.onnx --framework=5 --output=./yolox_pre_post --output_type=FP32 --soc_version=Ascend310P3 --input_shape="images:1, 3, 416, 416" --insert_op_conf=../aipp-configs/yolox_bgr.cfg
```
注: --soc_version 需填写当前芯片类型，可通过`npu-smi info`查询

若终端输出：
```
ATC start working now, please wait for a moment.

ATC run success, welcome to the next use.
```

表示命令执行成功。

## 4 编译与运行

**步骤1：** 在项目根目录执行命令：
 
```
bash build.sh  
chmod 640 postprocess/build/libYoloxPostProcess.so
cp postprocess/build/libYoloxPostProcess.so ${MX_SDK_HOME}/lib/modelpostprocessors/
```   

**步骤2：** 修改``python/pipeline/pre_post.pipeline``文件中的第47行 postProcessLibPath 为 libYoloxPostProcess.so 所在路径。

**步骤3：** 放入待测图片。将一张图片放在路径``python/test_img``下，命名为 test.jpg。

**步骤4：** 图片检测。在项目路径``python/Main``下运行命令：

```
python3 pre_post.py
```

**步骤5：** 查看结果。命令执行成功后在目录``python/test_img``下生成检测结果文件 pre_post_bgr.jpg，查看结果文件验证检测结果。

## 5 常见问题

### 5.1 未修改 pipeline 文件中的 ${MX_SDK_HOME} 值为具体值

**问题描述：**

运行demo前需要正确导入环境变量，否则会报错，如下图所示：
<center>
    <img src="./images/MindXSDKValueError.png">
    <br>
</center>

**解决方案：**

检查第四章生成的so路径，确保so路径在pipeline中配置正确。
### 5.2 后处理插件权限问题

**问题描述：**

运行检测 demo 和评测时都需要将生成的YOLOX后处理动态链接库的权限修改，否则将会报权限错误，如下图所示：
<center>
    <img src="./images/permissionerror.png">
    <br>
</center>

**解决方案：**

在YOLOX后处理的动态链接库的路径下运行命令：

```
chmod 640 libYoloxPostProcess.so
```

### 5.3 模型转换时会警告缺slice算子

**问题描述：**

YOLOX在图像输入到模型前会进行slice操作，而ATC工具缺少这样的算子，因此会报出如图所示的警告：

<center>
    <img src="./images/warning.png">
    <br>
</center>

**解决方案：**

常规的做法是修改slice算子，具体操作可参考[安全帽检测](https://gitee.com/booyan/mindxsdk-referenceapps/tree/master/contrib/HelmetIdentification)的开源项目。

由于在本项目下是否修改算子并不影响检测结果，因此默认不做处理。

### 5.4 protobuf报错

**问题描述：**

执行第4节**步骤4**时，运行命令报错
```
TypeError: Descriptors cannot be created directly.
If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
```

**解决方案：**

更新protobuf，命令为：`pip install 'protobuf~=3.19.0'`

### 5.5 模型加载错误

**问题描述：**

执行第4节**步骤4**时，运行命令报错`Failed to load offfline model data from file.`

**解决方案：**

1、执行模型转换时，要将--soc_version 修改为项目支持的硬件soc名

2、检查pipeline中的模型路径是否正确，修改为正确路径