# 行人重识别

## 1 介绍
### 1.1 简介
本开发样例基于MindX SDK实现了端到端的行人重识别（Person Re-identification, ReID），支持检索给定照片中的行人ID。

其主要流程为：    
1. 首先，程序入口分别接收查询图片和行人底库所在的文件路径。    
2. 其次，利用目标检测模型YOLOv3检测查询图片中的行人，检测结果经过抠图与调整大小，再利用ReID模型提取图片中每个行人的特征向量。    
3. 之后，将行人底库图片调整大小，利用ReID模型提取相应的特征向量。    
4. 最后进行行人检索。 将查询图片中行人的特征向量与底库中的特征向量比对，为每个查询图片中的行人检索最有可能的ID，通过识别框和文字信息进行可视化标记。

参考链接：
> 特定行人检索：[Person Search Demo](https://github.com/songwsx/person_search_demo)  

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro。

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用`pip3 install * `安装以下依赖：

|软件名称    | 版本        |
|-----------|-----------|
| numpy     | 1.24.0    |
| opencv-python   | 4.10.0.84 |
| pillow   | 11.0.0    |

### 1.5 代码目录结构说明
本工程名称为ReID，工程目录如下图所示：


```
ReID
|---- data
|   |---- gallerySet                    // 查询场景图片文件夹
|   |---- querySet                      // 行人底库图片文件夹
|   |---- ownDataset					// 行人底库原图形文件夹 
|   |---- cropOwnDataset				// 行人底库结果文件夹 
|---- models                            // 目标检测、ReID模型与配置文件夹
|   |   |---- yolov3.cfg
|   |   |---- coco.names
|   |   |---- ReID_pth2onnx.cfg
|---- pipeline                          // 流水线配置文件夹
|   |   |---- ReID.pipeline
|---- result                            // 结果保存文件夹                              
|---- main.py       
|---- makeYourOwnDataset.py
|---- README.md   
```  

## 2 设置环境变量

```bash
#设置CANN环境变量
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```

## 3 准备模型
行人重识别先采用了yolov3模型将图片中的行人检测出来，然后利用ReID模型获取行人的特征向量。 由于yolov3模型和ReID模型分别是基于Pytorch和Tensorflow的深度模型，我们需要借助ATC工具分别将其转换成对应的.om模型。

### 3.1 获取yolov3模型

**步骤1：** 获取yolov3的原始模型（.pb文件）和相应的配置文件（.cfg文件）。

&ensp;&ensp;&ensp;&ensp;&ensp; [原始模型下载链接](https://c7xcode.obs.myhuaweicloud.com/models/YOLOV3_coco_detection_picture_with_postprocess_op/yolov3_tensorflow_1.5.pb)
&ensp;&ensp;&ensp;&ensp;&ensp; [配置文件下载链接](https://c7xcode.obs.myhuaweicloud.com/models/YOLOV3_coco_detection_picture_with_postprocess_op/aipp_nv12.cfg)  

**步骤2：** 将获取到的yolov3模型.pb文件和.cfg文件存放至`ReID/models/`目录下。

**步骤3：** 模型转换。

在`ReID/models/`目录下，执行以下命令使用ATC将.pb文件转成为.om文件：
```bash
atc --model=yolov3_tensorflow_1.5.pb --framework=3 --output=yolov3 --output_type=FP32 --soc_version=Ascend310P3 --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0" --log=info --insert_op_conf=aipp_nv12.cfg
```
执行完模型转换脚本后，若提示如下信息说明模型转换成功，可以在`ReID/models/`下找到名为`yolov3.om`模型文件。

```
ATC run success, welcome to the next use.
```  

### 3.2 获取ReID模型

**步骤1：** 获取模型文件ReID.onnx。


通过[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ReIDv2/ReID.onnx)获取模型文件`ReID.onnx`，并放在`ReID/models/`路径下。


**步骤2：** 使用ATC将.onnx文件转成为.om文件。

在`ReID/models/`路径下执行：

```bash
atc --framework=5 --model=ReID.onnx --output=ReID --input_format=NCHW --input_shape="image:1,3,256,128" --insert_op_conf=ReID_onnx2om.cfg --log=debug --soc_version=Ascend310P3
```
执行完模型转换脚本后，若提示如下信息说明模型转换成功，可以在`ReID/models/`路径下找到名为`ReID.om`模型文件。
```
ATC run success, welcome to the next use.
```  





## 4 运行

**步骤1：** 准备行人底库数据集。


通过[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ReID/ReID%E7%9B%B8%E5%85%B3%E6%96%87%E4%BB%B6.rar)下载压缩包`ReID相关文件`。 在压缩包`ReID相关文件`中有`文件夹Market1501数据集`，该文件夹内有压缩文件`Market-1501-v15.09.15.zip`。

请解压`Market-1501-v15.09.15.zip`，在`Market-1501-v15.09.15\Market1501\gt_bbox`中选择想要查询的行人图片，将图片放在`ReID/data/querySet`中。
> 推荐每次查询1人，使用2-6张图片作为底库，效果较好；  
> 如需要查询多人，请保证待查询行人之间的着装风格差异较大，否则会较容易出现误报；
> 该项目需要为每张图片提取行人ID，行人图片的命名格式为： 
> '0001(行人ID)_c1(相机ID)s1(录像序列ID)_000151(视频帧ID)_00(检测框ID).jpg'。

**步骤2：** 准备场景图片数据集。

在上一步骤的压缩包`ReID相关文件`中有`场景图片`，该文件夹内有压缩文件`search_samples.rar`。
请解压`search_samples.rar`，然后将获取的图片放在`ReID/data/gallerySet`中。
> gallery下的图片必须是1920*1080大小的jpg。


**步骤3：** 配置pipeline。

在`ReID/pipeline/`路径下，修改文件`ReID.pipeline`第39行：

将`${SDK安装路径}`改为绝对路径。
```bash
34        "mxpi_objectpostprocessor0": {
35           "props": {
36                    "dataSource": "mxpi_tensorinfer0",
37                    "postProcessConfigPath": "models/yolov3.cfg",
38                    "labelPath": "models/coco.names",
39                    "postProcessLibPath": "${SDK安装路径}/lib/modelpostprocessors/libyolov3postprocess.so"
40                },
41                "factory": "mxpi_objectpostprocessor",
42                "next": "mxpi_imagecrop0"
43        },
```

**步骤4：** 执行命令。

在`ReID/`路径下，执行以下命令：
```bash
python3 main.py --queryFilePath='data/querySet' --galleryFilePath='data/gallerySet' --matchThreshold=0.3
```
matchThreshold是行人重定位的阈值，默认值是0.3，可根据行人底库的数量进行调整。 请注意这个阈值单位是距离单位，并不是比例阈值。 对market1501数据集，建议的范围是0.2~0.4之间。


**步骤5：** 查看结果。

可在`ReID/result/`路径下查看结果，结果以`.jpg`的形式可视化保存。


## 5 常见问题

### 5.1 检测目标过小

**问题描述：** 在运行main.py时出现“Vpc cropping failed”，或者“The image height zoom ratio is out of range [1/32, 16]”。  

**解决方案：** 这里的错误是因为yolov3模型检测到的目标过小，抠图后放大的比例超过系统给定的阈值[1/32, 16]，更新“项目所在目录/models/yolov3.cfg”文件，将OBJECTNESS_THRESH适度调大可解决该问题。
