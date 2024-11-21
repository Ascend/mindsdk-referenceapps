# MindXSDK 人像分割与背景替换

## 1 介绍

### 1.1 简介
本开发样例基于MindX SDK实现了端到端的人像分割与背景替换（Portrait Segmentation and Background Replacement, PSBR）。PSBR的主要功能是使用Portrait模型对输入图片中的人像进行分割，然后与背景图像融合，实现背景替换。输入为带有简单背景的单人jpg图片和一张没有人像的背景jpg图片，输出为人像背景替换后的jpg图片。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖
| 软件名称 | 版本     |
| -------- |--------|
| opencv_python   | 3.4.0 |

### 1.5 代码目录结构说明
本工程名称为PortraitSegmentation，工程目录如下图所示：
```
├── models
|   ├──  portrait.pb                 // 人像分割pb模型
|   ├──  insert_op.cfg               // 模型转换配置文件
|   └──  portrait.om                 // 人像分割om模型
├── pipline
|   └──  segment.pipeline            // 人像分割模型pipeline配置文件
├── main.py                             
└── README.md   
```

### 1.6 相关约束
为了达到良好的背景替换效果，输入的人像jpg图片构图应尽可能简单，仅包含单个人像及其相应的背景，其中人像应与其他物体有一定的间隔并显示出完整的轮廓。

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：  下载Portrait原始模型：[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/PortraitSegmentation/model.zip)，并将获取到的Portrait模型pb文件存放至本案例代码的PortraitSegmentation/models 目录下。

**步骤2**：  进入PortraitSegmentation/models目录执行以下命令。
```
atc --model=portrait.pb  --input_shape="Inputs/x_input:1,224,224,3"  --framework=3  --output=portrait --insert_op_conf=insert_op.cfg --soc_version=Ascend310P3
```

**步骤3**： 执行命令后，终端提示如下信息说明模型转换成功，会在output参数指定的路径下生成portrait.om模型文件。  
```
ATC run success, welcome to the next use.
```

## 4 运行
**步骤1**：配置pipeline
根据所需场景，修改segment.pipeline文件第32行：
```
#配置mxpi_tensorinfer插件的模型加载路径： modelPath
"mxpi_tensorinfer0": {
    "props": {
        "dataSource": "mxpi_imageresize0",
        "modelPath": "models/portrait.om"
    },
    "factory": "mxpi_tensorinfer",
    "next": "appsink0"
},
```

**步骤2**：准备输入图片
在工程根目录下新建data文件夹：
```
mkdir data
```
在data文件夹下存放对应jpg格式的人像和背景测试图片，并分别命名为portrait.jpg以及background.jpg。

**步骤3**：新建result文件夹
在工程根目录下新建result文件夹：
```
mkdir result
```
用于存放结果图片。

**步骤4**：在工程根目录下执行
```
python3 main.py data/background.jpg data/portrait.jpg
```

**步骤5**：查看结果
在result目录中查看背景替换结果图片。