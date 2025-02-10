# YOLOv3目标检测样例

## 1 介绍
### 1.1 简介
本开发样例基于Vision SDK实现了对本地图片进行YOLOv3目标检测，生成可视化结果。


### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：

| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |
| 6.0.0   | 8.0.0   |  24.1.0  |

### 1.4 三方依赖

第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用pip3 install * 安装以下依赖。

| 软件名称                   | 版本        |
|------------------------|-----------|
| numpy                  | 1.22.4    |
| opencv-python | 4.10.0.84 |


## 2. 设置环境变量

```bash
#设置CANN环境变量，cann_install_path为CANN安装路径
. ${cann_install_path}/set_env.sh

#设置Vision SDK 环境变量，sdk_install_path为Vision SDK 安装路径
. ${sdk_install_path}/set_env.sh
```
## 3. 准备模型

**步骤1** 下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2** 将获取到的YOLOv3模型文件内的`.pb`文件存放至`ImageDetectionSample/python/models/`下。
 
**步骤3** 使用ATC执行模型转换
在文件夹 `ImageDetectionSample/python/models/` 目录下执行以下命令
```bash
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
```
执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4 运行

**步骤1：** 准备一张待检测图片，放到`ImageDetectionSample/python`目录下命名为`test.jpg`。

**步骤2：** 运行, 进入`ImageDetectionSample/python`目录，执行
```
python3 main.py
```
**步骤3：** 查看结果，目标检测结果保存在当前目录的`result.jpg`中。
