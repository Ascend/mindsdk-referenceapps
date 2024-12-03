# RCF模型边缘检测

## 1 介绍
### 1.1 简介
本开发样例是基于mxBase开发的端到端推理的C++应用程序，可进行图像边缘提取，并把可视化结果保存到本地。 其中包含Rcf模型的后处理模块开发。 

主要处理流程为： 

Init > ReadImage >Resize > Inference >PostProcess >DeInit

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖
无

### 1.5 代码目录结构说明
本工程名称为EdgeDetectionPicture，工程目录如下图所示：

```
.
├── model
│   ├── aipp.cfg // 模型转换aipp配置文件
├── rcfDetection
│   ├── RcfDetection.cpp
│   └── RcfDetection.h
├──  rcfPostProcess
│   ├── rcfPostProcess.cpp
│   └── rcfPostProcess.h
├── build.sh
├── main.cpp
├── README.md
├── CMakeLists.txt
└── License
```

## 2 设置环境变量

```bash
#设置CANN环境变量
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```
## 3 准备模型

**步骤1** 通过[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/EdgeDetectionPicture/model.zip)下载RCF模型文件包。

**步骤2** 将获取到的RCF模型文件内的`rcf.prototxt`文件和`rcf_bsds.caffemodel`文件放在`EdgeDetectionPicture/model/`下。

**步骤3** 在`EdgeDetectionPicture/model/`下执行模型转换命令：
```bash
atc --model=rcf.prototxt --weight=./rcf_bsds.caffemodel --framework=0 --output=rcf --soc_version=Ascend310P3 --insert_op_conf=./aipp.cfg  --input_format=NCHW --output_type=FP32
```
执行完模型转换脚本后，若提示如下信息说明模型转换成功，可以在`EdgeDetectionPicture/model/`下找到名为`rcf.om`模型文件。

```
ATC run success, welcome to the next use.
```  


## 4 编译与运行

**步骤1** 在`EdgeDetectionPicture/`下执行如下编译命令：
```bash
bash build.sh
```

**步骤2** 进行图像边缘检测

1. 在`EdgeDetectionPicture/`下创建文件夹`data`。
2. 请自行准备jpg格式的测试图像，保存在`data/`文件夹内(例如 `data/**.jpg`)
3. 在`EdgeDetectionPicture/`下执行如下命令来进行边缘检测：
```bash
./edge_detection_picture ./data
```
**步骤3** 查看结果

生成的边缘检测图像会以原测试图像名称保存在`EdgeDetectionPicture/result/`文件夹内。 （如`result/**.jpg`）
