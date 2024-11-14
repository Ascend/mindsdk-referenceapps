# YOLOv3目标检测样例

## 1 介绍
### 1.1 简介
本开发样例基于MindX SDK实现了对本地图片进行YOLOv3目标检测，生成可视化结果。


### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

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
将${SDK安装路径}替换为自己的SDK安装路径

```
export MX_SDK_HOME=${SDK安装路径}

export LD_LIBRARY_PATH=${MX_SDK_HOME}/lib:${MX_SDK_HOME}/opensource/lib:${MX_SDK_HOME}/opensource/lib64
```

```bash
# 设置CANN环境变量（请确认install_path路径是否正确）
# Set environment PATH (Please confirm that the install_path is correct).

export install_path=/usr/local/Ascend/ascend-toolkit/latest
export PATH=/usr/local/python3.9.2/bin:${install_path}/atc/ccec_compiler/bin:${install_path}/atc/bin:$PATH
export PYTHONPATH=${install_path}/atc/python/site-packages:${install_path}/atc/python/site-packages/auto_tune.egg/auto_tune:${install_path}/atc/python/site-packages/schedule_search.egg
export LD_LIBRARY_PATH=${install_path}/atc/lib64:$LD_LIBRARY_PATH
export ASCEND_OPP_PATH=${install_path}/opp

#设置CANN环境变量
. ${install_path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```

```
# 执行如下命令，打开.bashrc文件
vi .bashrc
# 在.bashrc文件中添加以下环境变量
MX_SDK_HOME=${SDK安装路径}

LD_LIBRARY_PATH=${MX_SDK_HOME}/lib:${MX_SDK_HOME}/opensource/lib:${MX_SDK_HOME}/opensource/lib64:/usr/local/Ascend/ascend-toolkit/latest/acllib/lib64:/usr/local/Ascend/driver/lib64/

GST_PLUGIN_SCANNER=${MX_SDK_HOME}/opensource/libexec/gstreamer-1.0/gst-plugin-scanner

GST_PLUGIN_PATH=${MX_SDK_HOME}/opensource/lib/gstreamer-1.0:${MX_SDK_HOME}/lib/plugins

# 保存退出.bashrc文件
# 执行如下命令使环境变量生效
source ~/.bashrc

#查看环境变量
env
```
## 3. 准备模型

**步骤1** 在ModelZoo上下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2** 将获取到的YOLOv3模型文件内的.pb文件存放至`ImageDetectionSample/python/models/`下。

**步骤3** 模型转换
在文件夹 `ImageDetectionSample/python/models/` 下，执行模型转换脚本model_conversion.sh
```
bash model_conversion.sh
```
执行完模型转换脚本后，会生成相应的.om模型文件。执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4 编译与运行
**步骤1：** 转移样例：

将样例目录从 `mindxsdk-referenceapps/tutorials/ImageDetectionSample/python` 文件夹下 移动到 `${SDK安装路径}/samples/mxVision/python/`路径下。
```bash
cp mindxsdk-referenceapps/tutorials/ImageDetectionSample/python ${SDK安装路径}/samples/mxVision/python
```
移动后的项目路径为：`${SDK安装路径}/samples/mxVision/python/python`。


**步骤2：** 修改main.py：


将main.py 文件中 mxpi_objectpostprocessor0插件中的postProcessLibPath路径中的${SDK安装路径} 替换为自己的SDK安装路径

**步骤3：** 准备测试图片：

准备一张待检测图片，放到项目目录`${SDK安装路径}/samples/mxVision/python/python`下命名为test.jpg
**步骤4：** 运行:

命令行输入：

```
python3 main.py
```
运行结果将以`result.jpg`的形式保存在项目目录下。结果图片有画框，框的左上角显示推理结果和对应的confidence。
