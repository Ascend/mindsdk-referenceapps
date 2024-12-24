# MxBase人群密度估计

## 1 介绍
### 1.1 简介
本开发样例是基于VisionSDK开发的端到端推理的C++应用程序，可进行人群计数目标检测，并把可视化结果保存到本地。
该Sample的主要处理流程为： Init > ReadImage >Resize > Inference >PostProcess >DeInit

技术实现流程图：

![image-20210813154111508](image-20210813154111508.png)

### 1.2 支持的产品

本项目支持昇腾Atlas 500 A2。

### 1.3 支持的版本
本样例配套的VisionSDK版本、CANN版本、Driver/Firmware版本如下所示：

| VisionSDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- |---------| -------------- |
| 5.0.0   |7.0.0 |  23.0.0  |
| 6.0.RC3   | 8.0.RC3 |  24.1.RC3  |

### 1.4 三方依赖
无

## 2 设置环境变量

```bash
#设置CANN环境变量（请确认install_path路径是否正确）
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```
## 3 准备模型

**步骤1：** 下载模型文件包`model.zip`：

[模型及配置文件下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/CrowdCounting/model.zip)

**步骤2：** 解压zip：
```bash
unzip model.zip
```
**步骤3：** 转移解压后文件夹内的`count_person.caffe.caffemodel`与`count_person.caffe.prototxt`到`CrowdCounting/model`目录下。

**步骤4：** 使用ATC模型转换工具进行模型转换，参考如下指令:
```bash
atc --input_shape="blob1:1,3,800,1408" --weight="count_person.caffe.caffemodel" --input_format=NCHW --output="count_person.caffe" --soc_version=Ascend310B1 --insert_op_conf=insert_op.cfg --framework=0 --model="count_person.caffe.prototxt" 
```
- 执行完模型转换脚本后，若提示如下信息说明模型转换成功，并可以在该路径下找到名为`count_person.caffe.om`模型文件。

```
ATC run success, welcome to the next use.
```  

## 4 编译与运行

**步骤1：** cd到`CrowdCounting`目录下，执行如下编译命令： 
```bash
bash build.sh
```
**步骤2：** 准备推理图片

支持JPG格式，任意图像分辨率。将推理图片`xxx.jpg`放入`CrowdCounting`目录下，执行：
```bash
./crowd_counting  ./xxx.jpg
```
**步骤2：** 查看结果

结果以`result.jpg`的形式保存在`CrowdCounting`目录下。图片标注了识别到的人，左上角为识别到的人群数量。

