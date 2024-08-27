# 人体关键点检测
## 1. 介绍
### 1.1 简介
人体关键点检测插件基于 MindXSDK 开发，在昇腾芯片上进行人体关键点和骨架检测，将检测结果可视化并保存。输入一幅图像，可以检测得到图像中所有行人的关键点并连接成人体骨架。
人体关键点检测是指在输入图像上对指定的 18 类人体骨骼关键点位置进行检测，包括包括鼻子、左眼、右眼、左耳、右耳、左肩、右肩、左肘、右肘、左手腕、右手腕、左髋、右髋、左膝、右膝、左踝、右踝。然后将关键点正确配对组成相应的人体骨架，展示人体姿态，共 19 类人体骨架，如左肩和左肘两个关键点连接组成左上臂，右膝和右踝两个关键点连接组成右小腿等。
本方案采取OpenPose模型，将待检测图片输入模型进行推理，推理得到包含人体关键点信息和关键点之间关联度信息的两个特征图，首先从关键点特征图中提取得到所有候选人体关键点，然后结合关联度信息特征图将不同的关键点组合连接成为人体骨架，再将所有人体骨架连接组成不同的人体，最后将关键点和骨架信息标注在输入图像上，描绘人体姿态。本方案可以对遮挡人体、小人体、密集分布人体等进行检测，还适用于不同姿态（蹲坐、俯卧等）、不同方向（正面、侧面、背面等）以及模糊人体关键点检测等多种复杂场景。

本样例业务流程为：待检测图片通过 appsrc 插件输入，然后使用图像解码插件mxpi_imagedecoder对图片进行解码，再通过图像缩放插件mxpi_imageresize将图像缩放至满足检测模型要求的输入图像大小要求，缩放后的图像输入模型推理插件mxpi_tensorinfer得到检测结果，本项目开发的 OpenPose 人体关键点检测插件处理推理结果，从中提取关键点，确定关键点和关键点之间的连接关系，输出关键点连接形成的人体，最后通过序列化插件mxpi_dataserialize 和输出插件 appsink 获取人体关键点检测插件输出结果，并在外部进行人体姿态可视化描绘。本系统的各模块及功能描述如表1所示：

表1 系统方案各模块功能描述：

| 序号 | 子系统 | 功能描述     |
| ---- | ------ | ------------ |
| 1    | 图片输入    | 获取 jpg 格式输入图片 |
| 2    | 图片解码    | 解码图片 |
| 3    | 图片缩放    | 将输入图片放缩到模型指定输入的尺寸大小 |
| 4    | 模型推理    | 对输入张量进行推理 |
| 5    | 人体关键点检测    | 从模型推理结果检测人体关键点，并连接成人体骨架 |
| 6    | 序列化    | 将检测结果组装成json字符串 |
| 7    | 结果输出    | 将序列化结果输出|
| 8    | 结果可视化    | 将检测得到的关键点和人体骨架标注在输入图片上|

人体关键点检测插件的输入是模型推理插件输出的特征图，对于 OpenPose 模型，输出两个特征图，分别是关键点特征图 K 和关联度特征图 P，其中 K 的形状大小为 19 × w × h，P 的形状大小为 38 × w × h（w, h 表示特征图宽、高）， K中每个通道的二维特征图上每个位置的值表示该类关键点在该位置的置信度，共计 18 类关键点，关键点特征图的最后一个通道即第 19 个通道为背景点类。P 中每两个通道组成的三维特征图上的每个位置的值表示对应类别关键点在该位置处的向量坐标（x, y），通过计算两个不同类关键点组成的连接置信度将关键点连接成骨架，关键点之间组成的骨架共 19 类。

关键点插件从输出特征图检测得到人体关键点和骨架的整体流程为：
1. **将推理输出特征图缩放至原图尺寸大小。** 先将 K 和 P 放大 8 倍，因为 OpenPose 模型推理过程中会将输入缩小 8 倍得到特征图，然后去除 mxpi_imageresize 插件在缩放原图到指定尺寸时在图片右侧和下方添加的补边值，最后将特征图缩放到原图的尺寸大小。
2. **从关键点特征图检测得到每一类的候选关键点。** 首先将置信度小于一定阈值 T 的点的置信度设为 0，这些位置不会成为候选关键点；如果该点的置信度值大于其上、下、左、右四个相邻点的置信度值，则该点是该类关键点的一个候选关键点；对于每个候选关键点，去除其周围与其欧式距离小于一定阈值 TD 的其他候选关键点。上述过程如图1 所示。


<center>
    图1. 候选关键点选择示意图  </div>
    <img src="./images/KeypointNms.jpg">
    <br>
    <div style="color:orange;
    display: inline-block;
    color: #999;
    padding: 2px;">
</center>


3. **结合关联度特征图 P 将候选关键点配对形成候选骨架。** 对于每个骨架（kp1, kp2), 得到 kp1 的所有候选关键点集 S1={kp1_0, kp1_1, ……} 和 kp2 的所有候选关键点集 S2={kp2_0, kp2_1, ……}，将 S1 中的每个点 kp1_i和 S2 中的每个点 kp2_j 组合，计算每个点对是该骨架的置信度。计算方式为：在 kp1_i 和 kp2_j 两点连成的线段上等间距的生成 10 个点，每两个相邻点确定一个子段，通过这些子段计算该骨架的置信度并筛选得到候选骨架, 最后去除冲突的候选骨架，即两个骨架有相同的端点时，保留置信度高的骨架。

4. **将候选骨架组成人体。** 将有相同端点的骨架依次连接，最终组成一个或多个人体。

### 1.2 支持的产品

本项目基于mxVision SDK进行开发，以Atlas 500 A2为主要的硬件平台。


### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  |  CANN版本 | Driver/Firmware版本  |
|--------------- | ---------------------------------- | ----------|
| 5.0.0 | 7.0.0 | 23.0.0|
|6.0.RC2 | 8.0.RC2 | 24.1.RC2| 


### 1.4 三方依赖
环境依赖软件和版本如下表：

| 软件                | 版本         | 说明                          | 获取方式                                                     |
| ------------------- | ------------ | ----------------------------- | ------------------------------------------------------------ |                    
| pycocotools       | 2.0.8     | python COCO 评测工具            | pip3 install pycocotools|


### 1.5 代码目录结构说明

本工程名称为 OpenposeKeypointDetection，工程目录如下所示：
```
.
├── build.sh
├── images   # readme中使用的图片
│   ├── ATCSuccess.png
│   ├── COCOAnnotations.png
│   ├── KeypointNms.jpg
│   ├── OverallProcess.jpg
│   ├── PathError.png
│   └── PipelineError.png
├── plugins  # 后处理插件源码
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── MxpiOpenposePostProcess.cpp
│   └── MxpiOpenposePostProcess.h
├── proto    # 后处理插件protobuf定义
│   ├── build.sh
│   ├── CMakeLists.txt
│   └── mxpiOpenposeProto.proto
├── python
│   ├── evaluate.py   # 精度验证脚本
│   ├── main.py       # 推理脚本
│   ├── models        # 模型文件
│   │   ├── insert_op.cfg       # 模型转换配置文件
│   │   └── model_conversion.sh # 模型转换脚本
│   └── pipeline      # 
│       └── Openpose.pipeline   # pipline文件
└── README.md
```

## 2 设置环境变量
设置CANN及MindX SDK相关的环境变量

```shell
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # Ascend-cann-toolkit开发套件包默认安装路径，根据实际安装路径修改
. ${MX_SDK_HOME}/mxVision/set_env.sh   # ${MX_SDK_HOME}替换为用户的SDK安装路径
```


## 3. 准备模型

本项目中适用的模型是 OpenPose 模型，[原模型项目代码](https://github.com/Daniil-Osokin/lightweight-human-pose-estimation.pytorch)。此处提供pytorch 模型和onnx 模型[下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/OpenposeKeypointDetection/model.zip) 。然后使用模型转换工具 ATC 将 onnx 模型转换为 om 模型，模型转换工具相关介绍[参考链接](https://gitee.com/ascend/docs-openmind/blob/master/guide/mindx/sdk/tutorials/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99.md) 。

转换om模型步骤如下：
**步骤1**  从上述模型下载链接中下载onnx模型，将解压出来的simplified_560_openpose_pytorch.onnx放至 ``python/models`` 文件夹下。
**步骤2**  进入 ``python/models`` 文件夹下执行命令：
```
bash model_convertion.sh
```
执行该命令后会在当前文件夹下生成项目需要的模型文件 openpose_pytorch_560.om。执行后终端输出为：
```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4. 编译与运行

### 4.1 编译后处理插件

在项目根目录下执行命令：
```
bash build.sh
chmod 440 plugins/build/libmxpi_openposepostprocess.so
cp plugins/build/libmxpi_openposepostprocess.so ${SDK_INSTALL_PATH}/mxVision/lib/plugins/
```
注意需要将生成的so权限改为440。

### 4.2 运行
将一张包含人体的图片放在项目目录下，命名为 test.jpg。在该图片上进行检测，执行命令：
```
cd python
python3 main.py
```
### 4.3 查看结果

命令执行成功后在当前目录下生成检测结果文件 test_detect_result.jpg，查看结果文件验证检测结果。

## 5. 精度验证
### 5.1 获取数据集
执行下述命令下载 COCO keypoint VAL 2017 数据集与标注文件
```
wget http://images.cocodataset.org/zips/val2017.zip
wget http://images.cocodataset.org/annotations/annotations_trainval2017.zip
```
在 ``python`` 目录下创建 ``dataset`` 目录，将数据集压缩文件解压至 ``python/dataset`` 目录下确保下载完数据集和标注文件后的 python 目录结构为：
```
.
├── dataset
│   ├── annotations
│   │   ├── person_keypoints_val2017.json
│   │   └── ...
│   └── val2017
│       ├── 000000581615.jpg
│       ├── 000000581781.jpg
│       └── ...
├── evaluate.py
├── main.py
├── models
│   ├── convert_to_onnx.py
│   ├── insert_op.cfg
│   └── model_conversion.sh
└── pipeline
    └── Openpose.pipeline
```
### 5.2 执行验证
```
cd python
python3 evaluate.py
```

### 5.3 查看结果
命令执行结束后输出 COCO 格式的评测结果，并生成 val2017_keypoint_detect_result.json 检测结果文件。输出结果如下图所示：
<center>
    图2. 模型精度测试输出结果 </div>
    <img src="./images/EvaluateInfo.png">
    <br>
    <div style="color:orange;
    display: inline-block;
    color: #999;
    padding: 2px;">
</center>
其中圈出来的部分为模型在 COCO VAL 2017 数据集上，IOU 阈值为 0.50:0.05:0.95 时的精度值。

## 6 常见问题


### 6.1 模型参数配置问题

**问题描述：**

``python/pipeline/Openpose.pipeline`` 中模型输入尺寸相关参数需要和使用的 om 模型相对应，否则会报如下类型的错：

<center>
    图3. 模型输入尺寸和 pipeline 中参数设置不匹配报错 </div>
    <img src="./images/PipelineError.png">
    <br>
    <div style="color:orange;
    display: inline-block;
    color: #999;
    padding: 2px;">
</center>

**解决方案：**

确保 ``python/pipeline/Openpose.pipeline`` 中 mxpi_imageresize0 插件的 resizeWidth 和 resizeHeight 属性值是转换模型过程中设置的模型输入尺寸值；mxpi_openposepostprocess0 插件中的 inputWidth 和 inputHeight 属性值是转换模型过程中设置的模型输入尺寸值。


### 6.2 评测过程中的文件路径问题

**问题描述：**

精度评测过程中，将 COCO VAL 2017 数据集文件夹和标注文件夹放在正确位置，否则执行评测程序时找不到文件，报如下类型的错：

<center>
    图4. 文件路径报错 </div>
    <img src="./images/PathError.png">
    <br>
    <div style="color:orange;
    display: inline-block;
    color: #999;
    padding: 2px;">
</center>


**解决方案：**


下载完数据集和标注文件后，确保 ``python/dataset`` 目录结构为：
```
.
├── annotations
│   ├── person_keypoints_val2017.json
│   └── ...
└── val2017
    ├── 000000581615.jpg
    ├── 000000581781.jpg
    └── other-images
```