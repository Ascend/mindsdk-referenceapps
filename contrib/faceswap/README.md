## 基于MindX SDK的faceswap应用开发

## 1、 介绍

### 1.1 简介
faceswap应用基于VisionSDK开发，在昇腾芯片上进行目标检测，脸部关键点推理以及目标替换，将替换结果可视化并保存。  

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称      | 版本             |
| ------------- | ---------------- |
| numpy         | 1.19.5           |
| opencv-python | 4.10.0.84       |
| Pillow       | 9.3.0           |

### 1.5 三方依赖

本Sample工程名称为faceswap，工程目录如下图所示：
```angular2html
|-------- data                                 // 输入存放文件夹（需手动创建）
|-------- models
|           |---- yolov4.cfg                   // yolov4后处理配置文件（用于目标检测）
|           |---- coco.names                   // yolov4模型所有可识别类
|           |---- yolov4_detection.om          // yolov4离线推理模型
|           |---- V3ONNX.cfg                   // 脸部特征点检测模型转换配置文件（用于检测脸部特征点）
|           |---- V3ONNXX.om                   // 脸部特征点检测离线模型
|-------- pipline
|           |---- faceswap.pipeline            // 目标替换流水线配置文件
|-------- result                               // 存放结果文件（需手动创建）
|-------- faceswap_main.py                              
|-------- faceswap_post.py                     // 后处理模块
|-------- README.md
```  

### 1.6 相关约束

- 在目标检测阶段，由于yolov4_detection.om模型的coco.names标签集中同时存在people，face两类标签。当对输入图片的检测结果为people时，无法进行后续的换脸操作，故输入图片应尽可能体现脸部特征，建议输入图片为类似于证件照的半身人像。否则，当输入为全身人像时候，图片标签为people，无法进行后续换脸操作；  
- 在特征点检测阶段，由于特征点检测模型限制，输入目标应尽可能采用脸部清晰，轮廓完整的正面图像，即应尽可能输入2D目标图像，且脸部应尽可能避免眼镜等一类装饰物。若图片中存在3D特征，如输入侧脸时，可能会由于脸部特征点检测存在偏差导致换脸效果不佳；  
- 针对MindSDK固有插件的输入限制，输入目标图片的宽高均应限制在[32, 8192]区间内，否则会导致图片入流失败。当输入图片尺寸不符合要求时，系统会提示相应的错误信息。

## 2、 设置环境变量

在编译运行项目前，需要设置环境变量：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```

## 3、 准备模型

**步骤1**：模型文件下载

- 目标检测采用提供的离线模型`yolov4_detection.om`进行推理。

  [模型下载链接](https://mindx.sdk.obs.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/faceswap/yolov4_detection.om) 。

  下载后，将`yolov4_detection.om`模型存放在工程`/model`目录下。

- 下载脸部特征点检测onnx模型

  [模型下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/faceswap/v3.onnx)。

  下载后，将`v3.onnx`模型存放在工程`/model`目录下。

**步骤2**：模型转换

在项目的`model`文件夹下执行以下命令：
```
atc --model=v3.onnx --framework=5 --output=V3ONNXX --soc_version=Ascend310P3 --insert_op_conf=V3ONNX.cfg --out_nodes="Gemm_169:0"
```

执行完模型转换脚本后，会生成相应的`V3ONNXX.om`模型文件。执行命令后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

## 4、 运行

**步骤1**：准备两张需要的测试图片  

在项目根目录下执行以下命令新建`data`文件夹。
```
mkdir data
```
将准备好的测试图片放在`data`文件夹下并分别命名为`face1.jpg`，`face2.jpg`。

**步骤2**：创建输出文件夹

在项目根目录下执行以下命令新建`result`文件夹，用于存放推理结果。
```
mkdir result
```

**步骤3**：执行程序

在项目根目录下，执行以下命令运行样例。
```
python3 faceswap_main.py data/face1.jpg data/face2.jpg
```

**步骤4**：查看结果

执行完成后，可在`result`目录中查看目标替换结果`face_swap_result.jpg`。




