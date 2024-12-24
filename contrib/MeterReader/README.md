# 工业指针型表计读数项-MeterReader

## 1 介绍
### 1.1 简介

在电力能源厂区需要定期监测表计读数，以保证设备正常运行及厂区安全。但厂区分布分散，人工巡检耗时长，无法实时监测表计，且部分工作环境危险导致人工巡检无法触达。针对上述问题，希望通过摄像头拍照后利用计算机智能读数的方式高效地完成此任务。

在本系统中，目的是基于VisionSDK，在华为云昇腾平台上，开发端到端工业指针型表计读数的参考设计，实现对传统机械式指针表计的检测与自动读数功能，达到功能要求。



实现方案：

本系统识别的流程是：先将输入的图像送入流中解码和缩放大小，使用YOLOv5目标检测模型去检测图片中的表盘，结束流。将目标框裁剪下来，再送入流中解码和缩放大小，用DeepLabv3语义分割模型去得到工业表中的指针和刻度，对语义分割模型预测的结果进行读数后处理，找到指针指向的刻度，根据刻度的间隔和刻度根数计算表盘的读数。

表1.1 系统方案中各模块功能：

| 序号 | 子系统 | 功能描述 |
| :------------ | :---------- | :---------- |
| 1    | 图像输入 | 调用VisionSDK的appsrc输入图片|
| 2    | 图像解码 | 调用VisionSDK的mxpi_imagedecoder输入图片|
| 3    | 图像放缩 | 调用VisionSDK的mxpi_imageresize，放缩到1024*576大小 |
| 4    | 工业表检测 | 调用VisionSDK的mxpi_tensorinfer，使用YOLOv5的检测模型，检测出图片中车辆|
| 5    | 保存工业表的图像 | 将YOLOv5检测到的工业表结果保存图片|
| 6    | 图像输入| 调用VisionSDK的appsrc输入检测到的工业表 |
| 7    | 图像解码 | 调用VisionSDK的mxpi_imagedecoder输入图片|
| 8    | 图像放缩 | 调用VisionSDK的mxpi_imageresize，放缩到512*512大小 
| 9    | 指针刻度检测 | 调用VisionSDK的mxpi_tensorinfer，使用DeepLabv3语义分割模型，检测图像中的指针与刻度|
| 10    | 模型后处理 | 调用VisionSDK的mxpi_semanticsegpostprocessor，得到语义分割的结果|
| 11    | 读数后处理 | 开发mxpi_process3插件，读出工业表的数字|

技术实现流图：

<ol>
  <center>
      <img src="./images/README_img/YOLOv5_pipeline.png">
      <br>
      <div style="color:orange;
      display: inline-block;
      color: #999;
      padding: 2px;">图1. YOLOv5的pipeline流程图 </div>
  </center>

  <center>
        <img src="./images/README_img/DeepLabv3_pipeline.png">
        <br>
        <div style="color:orange;
        display: inline-block;
        color: #999;
        padding: 2px;">图2. DeepLabv3的pipeline流程图 </div>
  </center>
</ol>


注意事项：
* 本系统中只使用了两种类型的表盘数据参与训练和测试。我们通过预测的刻度根数来判断表盘类型，第一种表盘的刻度根数为50，第二种表盘的刻度根数为32。因此，目前系统只能实现这两种针表计的检测和自动读数功能。

* 本系统要求拍摄图片角度正常，尽可能清晰。如果拍摄图片角度不正常，导致图片模糊，则很难正确读出表数。

* 本系统采用opencv进行图片处理，要求输入文件均为opencv可处理文件。
### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro。

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖
环境依赖软件和版本如下表：

|   软件名称     |    版本     |
| :-----------: |:---------:|
|    Python     |   3.9.2   |
|     numpy     |  1.24.0   |
| opencv-python | 4.10.0.84 |

### 1.5 代码目录结构与说明
本工程名称为工业指针型表计读数，工程目录如下图所示：
```
├── build.sh
├── README.md
├── images
    ├── README_img
        ├── DeepLabv3_pipeline.png
        ├── get_map1.png
        ├── get_map2.png
        ├── get_map3.png
        ├── YOLOv5_pipeline.png        
├── infer
    ├── det.py
    ├── main.py 
    ├── seg.py     
├── models
    ├── deeplabv3
        ├── seg_aipp.cfg            #deeplabv3的onnx模型转换成om模型的配置文件
    ├── yolov5
        ├── det_aipp.cfg           #yolov5的onnx模型转换成om模型的配置文件   
├── pipeline                        #pipeline文件
    ├── deeplabv3
        ├── deeplabv3.cfg
        ├── deeplabv3.names
        ├── seg.pipeline
    ├── yolov5
        ├── det.pipeline   
├── plugins                         #开发读数处理插件代码
    ├── process3
        ├── build.sh
        ├── CMakeLists.txt
        ├── Myplugin.cpp
        ├── Myplugin.h
        ├── postprocess.cpp
        ├── postprocess.h
```


## 2 设置环境变量
```bash
#设置CANN环境变量，ascend-toolkit-path为cann安装路径
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```


## 3 准备模型

### 3.1 模型转换

* YOLOV5模型转换

**步骤1:** 模型下载

下载[onnx模型压缩包](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/MeterReader/models.zip)并解压

将压缩包中的"det.onnx"模型拷贝至"\${MeterReader代码根目录}/models/yolov5"目录下。  

**步骤2:** 执行命令

进入"\${MeterReader代码根目录}/models/yolov5"目录，执行以下命令将"det.onnx"模型转换成"det.om"模型:
```bash
atc --model=det.onnx --framework=5 --output=det  --insert_op_conf=det_aipp.cfg --soc_version=Ascend310P3 
```

**步骤3:** 查看结果

出现以下语句表示命令执行成功，会在当前目录中得到"det.om"模型文件。
  ```
  ATC start working now, please wait for a moment.
  ATC run success, welcome to the next use.
  ```





* DeepLabv3模型转换

**步骤1:** 模型下载

将压缩包中的"seg.onnx"模型拷贝至"\${MeterReader代码根目录}/models/deeplabv3"目录下：

  注：DeepLabv3模型提供了两种转换方式:

  * 若下载[onnx模型压缩包](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/MeterReader/models.zip)，则执行上述步骤后，只需完成DeepLabv3模型转换的步骤四；

  * 若下载[pdmodel模型压缩包](https://bj.bcebos.com/paddlex/examples2/meter_reader//meter_seg_model.tar.gz)，则参考并完成DeepLabv3模型转换的所有后续步骤；



**步骤2:** 安装paddle2onnx

使用以下命令安装paddle2onnx依赖，[paddle2onnx安装参考链接](https://github.com/PaddlePaddle/Paddle2ONNX/blob/develop/docs/zh/compile.md)：
```bash
pip3 install paddle2onnx
```


**步骤3:** paddle模型转onnx模型

确保已下载[pdmodel模型压缩包](https://bj.bcebos.com/paddlex/examples2/meter_reader//meter_seg_model.tar.gz)，将目录"meter_seg_model"中的文件解压至"${MeterReader代码根目录}/models/deeplabv3"目录下，进入"deeplabv3"目录，使用以下命令将"pdmodel"模型转换成"onnx"模型,[paddle2onnx模型转换参考链接](https://github.com/PaddlePaddle/Paddle2ONNX/)：
  ```bash
  cd ${MeterReader代码根目录}/models/deeplabv3
  paddle2onnx --model_dir meter_seg_model \
              --model_filename model.pdmodel \
              --params_filename model.pdiparams \
              --save_file seg.onnx \
              --enable_dev_version True
  ```

**步骤4:** onnx模型转om模型

进入"\${MeterReader代码根目录}/models/deeplabv3"目录，执行以下命令将"seg.onnx"模型转换成"seg.om"模型。
  ```bash
  cd ${MeterReader代码根目录}/models/deeplabv3
  atc --model=seg.onnx --framework=5  --output=seg --insert_op_conf=seg_aipp.cfg  --input_shape="image:1,3,512,512"  --input_format=NCHW --soc_version=Ascend310P3
  ```

**步骤5:** 查看结果

出现以下语句表示命令执行成功，会在当前目录中得到seg.om模型文件。
  ```
  ATC start working now, please wait for a moment.
  ATC run success, welcome to the next use.
  ```


## 4 编译与运行

**步骤1:** 编译插件

在项目目录下执行如下命令：
```bash
cd ${MeterReader代码根目录}/plugins/process3
. build.sh
```

**步骤2:** 修改pipeline文件中的参数地址
* 修改"${MeterReader代码根目录}/pipeline/yolov5/det.pipeline"第40行处文件的绝对路径，将pipeline中所需要用到的模型路径改为存放模型的绝对路径地址：
  ```python
  40 "modelPath":"${MeterReader代码根目录}/models/yolov5/det.om"
  ```

* 修改"${MeterReader代码根目录}/pipeline/deeplabv3/seg.pipeline"第30、38、39行处文件的绝对路径，将pipeline中所需要用到的模型路径、配置文件地址改为绝对路径地址：
  ```python
  30 "modelPath":"${MeterReader代码根目录}/models/deeplabv3/seg.om"
  38 "postProcessConfigPath":"${MeterReader代码根目录}/pipeline/deeplabv3/deeplabv3.cfg",
  39 "labelPath":"${MeterReader代码根目录}/pipeline/deeplabv3/deeplabv3.names",
  ```

**步骤3:** 运行

输入带有预测表盘的jpg图片，在指定输出目录下输出得到带有预测表盘计数的png图片。
```bash
cd ${MeterReader代码根目录}/infer
python3 main.py --ifile ${输入图片路径} --odir ${输出图片目录}
```

**步骤4:** 查看结果

执行结束后，可在命令行内得到yolo模型输出的表盘文件路径，以及通过后续模型得到的预测表盘度数。可在设定的输出图片目录中查看带有预测表盘计数的图片结果。最后展示的结果图片上用矩形框框出了图片中的表计并且标出了预测的表盘读数。