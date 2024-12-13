# 通用文字识别（中英文）

## 1 介绍

### 1.1 简介

通用文字识别样例基于mxVision SDK进行开发，主要支持以下功能：

1. 图片读取解码：本样例支持JPG及PNG格式图片，采用OpenCV进行解码、缩放等预处理。
2. 文本检测：在输入图片中检测出文本框，本样例选用基于DBNet的文本检测模型，能达到快速精准检测。
3. 投射变换：将识别的四边形文本框，进行投射变换得到矩形的文本小图。
4. 竖排文字旋转：根据文本框的高宽比，大于阈值（默认为1.5），将文本框旋转90°，从竖排文本转换为横排文本。
5. 文本方向检测：识别文本小图上文本的方向--[0°，180°]，如果为180°，则将文本小图进行180°旋转，本样例选用Mobilenet为方向识别模型。
6. 文字识别：识别文本小图上中英文，本样例采用CRNN模型进行文字识别，能够识别中英文.

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro。

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称                   | 版本      |
|------------------------|---------|
| python                 | 3.9.2   |
| paddlepaddle（静态图）      | 大于1.8.0 |
| paddlepaddle（动态图）      | 大于2.0.0 |
| onnx                   | 大于1.7.0 |

### 1.4 代码目录结构说明

```
|-- mxVision
|   |-- GeneralTextRecognition
|   |   |-- C++
|   |   |   |-- CMakeLists.txt
|   |   |   |-- mainMultiThread.cpp
|   |   |   |-- run.sh
|   |   |-- License.md
|   |   |-- README.md
|   |   |-- THIRD PARTY OPEN SOURCE SOFTWARE NOTICE.md
|   |   |-- data
|   |   |   |-- OCR.pipeline
|   |   |   |-- OCR_multi3.pipeline
|   |   |   |-- config
|   |   |   |   |-- cls
|   |   |   |   |   |-- cls.cfg
|   |   |   |   |   |-- ic15.names
|   |   |   |   |-- det
|   |   |   |   |   |-- det.cfg
|   |   |   |   |-- rec
|   |   |   |       |-- rec_cfg.txt
|   |   |   |-- model
|   |   |       |-- cls_aipp.cfg
|   |   |       |-- det_aipp.cfg
|   |   |       |-- rec_aipp.cfg
|   |   |-- main_ocr.py
|   |   |-- src
|   |       |-- Clipper
|   |       |   |-- CMakeLists.txt
|   |       |-- DBPostProcess
|   |       |   |-- CMakeLists.txt
|   |       |   |-- DBPostProcess.cpp
|   |       |   |-- DBPostProcess.h
```

### 1.5 相关约束

本项目支持通用文字识别，支持图片格式为jpg、jpeg、png。

## 2 设置环境变量

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh       # sdk安装路径，根据实际安装路径修改
```

## 3 准备模型

**步骤1：** 模型下载。

本样例采用[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)的release/2.1分支作为基准，预训练模型请下载"PP-OCR 2.0 series model list（Update on Dec 15）"->"Chinese and English general OCR model (143.4M)" 对应的三个推理模型：
1. Detection model: [DBNet](https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_server_v2.0_det_infer.tar)
2. Direction classifier model: [Mobilenet](https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar)
3. Recognition model: [CRNN](https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_server_v2.0_rec_infer.tar)

**步骤2：** 将下载的3个模型tar包移动至<Project_Root>/data/model目录下。其中，Project_Root为样例代码根目录。

**步骤3：** 执行<Project_Root>/data/model下的run.sh脚本，等待片刻。
```bash
bash run.sh
```

## 4 编译与运行
**步骤1：** 编译clipper动态库。

在[Clipper网站](https://sourceforge.net/projects/polyclipping/files/)下载`clipper_ver6.4.2.zip`压缩包，解压后将路径cpp下的 `clipper.hpp、clipper.cpp` 到<Project_Root>/src/Clipper目录下。依次执行如下命令：
```bash
mkdir build
cd build
cmake ..
make -j
make install
```

**步骤2：** 编译后处理动态库DBPostProcess。

进入到<Project_Root>/src/DBPostProcess路径目录下。依次执行如下命令：
```bash
mkdir build
cd build
cmake ..
make -j
make install
```

**步骤3：** 权限设置。

DB后处理目前支持两种缩放方式：拉伸缩放`Resizer_Stretch`、 等比例缩放`Resizer_KeepAspectRatio_Fit`。 因此，需要确保编译生成的libclipper.so和libDBPostProcess.so文件权限不高于640, 如果文件权限不满足要求, 
进入到<Project_Root>/lib目录, 执行如下命令修改文件权限：
```bash
chmod 640 libclipper.so libDBPostProcess.so
```

**步骤4：** 准备字典数据。
下载文字识别模型的[字典](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.1/ppocr/utils/ppocr_keys_v1.txt), 由于样例使用的CRNN模型，对应的字典从1开始，0代表为空，请在下载的字典首行添加一行"blank"，并将修改后的字典保存到<Project_Root>/data/config/rec目录，文件命名为ppocr_keys_v1.txt, 修改示例如下：
```bash
blank
'
疗
绚
诚
娇
.
.
.
```

**步骤5：** 修改配置根目录下的配置文件。

将所有`deviceId`字段值替换为实际使用的device的id值，可用的`deviceId`值可以使用如下命令查看：
```bash
npu-smi info
```
文本检测使用的DBNet后处理由步骤2编译得到，默认生成到"<Project_Root>/lib/libDBpostprocess.so", 如有修改，请修改<Project_Root>/data/OCR.pipeline和OCR_multi3.pipeline的对应配置，将`<project_Root>`标识符更改为实际的路径，示例如下：
```bash
"mxpi_textobjectpostprocessor0": {
      "props": {
        "postProcessConfigPath": "<Project_Root>/data/config/det/det.cfg",
        "postProcessLibPath": "<Project_Root>/lib/libDBpostprocess.so"
       },
      "factory": "mxpi_textobjectpostprocessor",
      "next": "mxpi_warpperspective0"
},
```
最后，请将pipline下的所有**Project_Root**路径更换为实际的项目路径，例如/root/GeneralTextRecognition/data/config/rec/rec_cfg.txt，/root/GeneralTextRecognition为实际项目路径。

**步骤6：** 准备测试图片，在根目录下创建input_data目录，并将包含中英文的JPG或PNG图片拷贝到input_data目录下

**步骤7：** 运行多线程高性能c++样例

多线程高性能c++样例输入与输出解耦，多线程发送与读取数据。运行前确保<Project_Root>/data/OCR_multi3.pipeline已完成修改，而后进入到<Project_Root>/C++目录，执行如下命令：
```bash
bash run.sh
```

## 5 运行

提供简易python运行样例，请参考第4小结中步骤1至步骤6完成配置准备，进入到<Project_Root>/python目录，执行如下命令：
```bash
python3 main_ocr.py
```
