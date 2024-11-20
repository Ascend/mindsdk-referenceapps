# YOLOv3目标检测样例

## 1 介绍
### 1.1 简介
本开发样例基于MindX SDK实现了对本地图片进行YOLOv3目标检测，生成可视化结果。


### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用pip3 install * 安装以下依赖。

| 软件名称                   | 版本        |
|------------------------|-----------|
| numpy                  | 1.22.4    |
| opencv-python-headless | 4.10.0.84 |


## 2. 设置环境变量

```bash
#设置CANN环境变量
. ${install_path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```
## 3. 准备模型

**步骤1** 在ModelZoo上下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2** 将获取到的YOLOv3模型文件内的`.pb`文件存放至`ImageDetectionSample/python/models/`下。
 
**步骤3** 模型转换
在文件夹 `ImageDetectionSample/python/models/` 下，执行模型转换脚本model_conversion.sh
```
bash model_conversion.sh
```
执行完模型转换脚本后，会生成相应的`.om`模型文件。执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。

**步骤4** 准备标签文件coco.names

通过命令查找到文件`coco.names`路径：
```bash
find / -name coco.names
```
在`ImageDetectionSample/python/models/` 下， 复制文件`coco.names`：
```bash
cp ${刚刚获取的路径}  ./
```

## 4 运行
**步骤1：** 转移样例：

将样例目录从 `mindxsdk-referenceapps/tutorials/ImageDetectionSample/python` 文件夹下 移动到 `${SDK安装路径}/samples/mxVision/python/`路径下。
```bash
cp -r mindxsdk-referenceapps/tutorials/ImageDetectionSample/python ${SDK安装路径}/samples/mxVision/python
```
移动后的项目路径为：`${SDK安装路径}/samples/mxVision/python/python`。


**步骤2：** 修改main.py：


将main.py 文件中 第78行 mxpi_objectpostprocessor0插件中的postProcessLibPath路径中的${SDK安装路径} 替换为自己的SDK安装路径：
```bash
78  "postProcessLibPath": "${SDK安装路径}/lib/modelpostprocessors/libyolov3postprocess.so"
```
**步骤3：** 准备测试图片：

准备一张待检测图片，放到项目目录`${SDK安装路径}/samples/mxVision/python/python`下命名为test.jpg


**步骤4：** 运行:

命令行输入：

```
python3 main.py
```
运行结果将以`result.jpg`的形式保存在项目目录下。
