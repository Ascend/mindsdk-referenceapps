# 车牌识别
## 1 介绍
### 1.1 简介

本样例是基于mxBase开发的端到端推理的C++应用程序，使用车牌检测模型和车牌识别模型在昇腾芯片上对图像中的车牌进行检测，并对检测到的图像中的每一个车牌进行识别，最后将可视化结果保存为图片形式。

对于车牌检测模型，在绝大多数情况下都能将车牌正确框选出来，车牌检测准确率较高；但**受限于训练车牌识别模型的数据集**，车牌识别只能识别蓝底车牌，对于黄底车牌和绿底新能源车牌很难正确识别，而且模型对中文字符的识别准确率偏低，对于大角度车牌的识别准确率偏低，对分辨率较低的图片的识别准确率偏低。若用户需要高准确率的结果，可自行训练识别模型，参考本样例实现模型的推理及后处理开发。

本样例的主要处理流程为： Init > ReadImage > Resize > Detection_Inference > Detection_PostProcess > Crop_Resize > Recognition_Inference > Recognition_PostProcess > WriteResult > DeInit。

### 1.2 支持的产品

本项目以昇腾Atlas 300I为主要的硬件平台。

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 5.0.0 | 7.0.0   |  23.0.0  |
### 1.4 三方依赖
环境依赖软件和版本如下表：

| 软件                | 版本                                                         | 说明                                               |
| ------------------- | ------------------------------------------------------------ | -------------------------------------------------- |
| OpenCV              | 4.7.0                                                        | 用于结果可视化                                     |
| FreeType            | [2.10.0](https://download.savannah.gnu.org/releases/freetype/) | 用于在图片上写中文(opencv只支持在图片上写英文字符) |
###  1.5 代码目录结构与说明

本样例工程名称为CarPlateRecognition，工程目录如下图所示：

```
├── include #头文件目录
  ├── carplate_recognition.h 
  ├── carplate_recognition_postprocess.h
  ├── ssd_vgg_postprocess.h
  ├── initparam.h # 定义了包含程序所需参数的结构体
  ├── cvx_text.h
├── model #模型目录
├── src #源文件目录
  ├── main.cpp #主程序
  ├── carplate_recognition.cpp #车牌识别流程处理函数源文件
  ├── ssd_vgg_postprocess.cpp #车牌检测模型后处理源文件
  ├── carplate_recognition_postprocess.cpp #车牌识别模型后处理源文件
  ├── cvx_text.cpp #定义了使用FreeType库在图片上写中文的类
├── imgs #README图片目录
├── build.sh
├── CMakeLists.txt
├── README.md
├── simhei.ttf # 黑体字体文件
```

### 1.4 技术实现流程图

![技术流程图](https://gitee.com/zhong-wanfu/mindxsdk-referenceapps/raw/master/contrib/CarPlateRecognition/imgs/技术流程图.jpg))

## 2 设置环境变量


```bash
# 设置环境变量（请确认install_path路径是否正确）
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh
```

## 3 准备模型
**步骤1：** 获取[模型](暂定)，在项目目录创建model文件夹并解压到model目录下。
**步骤2：** 进入model目录，执行以下命令使用atc命令进行车牌检测与车牌识别模型转换
```bash
atc --model=./car_plate_detection/car_plate_detection.prototxt --weight=./car_plate_detection/car_plate_detection.caffemodel --framework=0 -output=./car_plate_detection/car_plate_detection --insert_op_conf=./car_plate_detection/aipp.cfg --soc_version=Ascend310
atc --model=./car_plate_recognition/car_plate_recognition.prototxt --weight=./car_plate_recognition/car_plate_recognition.caffemodel --framework=0 -output=./car_plate_recognition/car_plate_recognition --insert_op_conf=./car_plate_recognition/aipp.cfg --soc_version=Ascend310
```
## 4 编译与运行
**步骤1：** 获取[FreeType2.10.0](https://download.savannah.gnu.org/releases/freetype/)并安装:

```
STEP1:从上面的FreeType版本链接中获取安装包freetype-2.10.0.tar.gz，保存到服务器
STEP2:进入freetype的安装目录：cd /home/xxx/freetype-2.10.0 # 该路径需用户根据实际情况自行替换
STEP3:执行配置命令：./configure --without-zlib --prefix=path_to_install # path_to_install为用户想安装的路径
STEP4:执行编译命令：make
STEP5:执行安装命令：make install # 该步骤需要root权限，否则会提示安装失败
STEP6:设置环境变量：export FREETYPE_HOME=path_to_install # 编译时需要该环境变量
```
**步骤2：** 修改CMakeLists.txt文件：

第**10**行 `set(MX_SDK_HOME $ENV{MX_SDK_HOME})` 语句是设置MindX_SDK的安装路径，一般按第2章设置环境变量后环境中有该变量存在，若没有，则将$ENV{MX_SDK_HOME}替换为用户实际的MindX_SDK安装路径。

第**12**行 `set(FREETYPE_HOME $ENV{FREETYPE_HOME})` 语句是设置FreeType库的安装路径，若未设置FREETYPE_HOME环境变量，需将$ENV{FREETYPE_HOME}替换为用户实际的FreeType库安装路径。

第**39**行 freetype 语句是链接到FreeType库，该名称一般是不用修改的，若命名不同则看情况修改。

**步骤3** 执行shell脚本或linux命令对代码进行编译：

```shell
bash build.sh
```

**步骤4** **推理** 请自行准备**jpg/jpeg**格式图像保存在工程目录下，执行如下命令：

```shell
./bin/car_plate_recognition ./xxx.jpeg # 自行替换图片名称
```
## 5 常见问题
由于车牌识别模型的精度问题，识别结果误差较大时，建议使用蓝底、不包含中文字符、角度适中且分辨率高的图片做为推理的输入。