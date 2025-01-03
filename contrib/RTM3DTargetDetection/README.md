# 3D目标检测

## 1 介绍

### 1.1 简介

3D目标检测样例基于Vision SDK进行开发，实现对图像进行三维目标检测的功能。本次使用的3D目标检测模型在图片中只能识别三类目标：'Car'，'Pedestrian'，'Cyclist'，因此使用场景一般限定于公路道路场景中。输入图片大小推荐在1280*416左右，对于'Pedestrian'，'Cyclist'检测效果不太理想，识别率不高。

### 1.2 支持的产品

Atlas 300I

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：
| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0 | 7.0.0   |  23.0.0  | 

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型

**步骤1：** 下载3D目标检测的模型文件：[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/RTM3DTargetDetection/model.zip)，解压后将om文件放到RTM3DTargetDetection/models目录下。

## 4 编译与运行

**步骤1：** 编译后处理插件：在项目根目录下执行命令
```
bash build.sh #编译后处理插件
chmod 440 ./plugins/plugin/librtm3dpostprocess.so #修改so权限
```

**步骤2：** 准备输入图片：将图片命名为test.jpg放到项目根目录下

**步骤3：** 运行：在项目根目录下执行命令
```
python3 main.py --input-image test.jpg
```

**步骤4：** 查看结果：
运行成功后回显会显示检测的相关信息，并在当前目录生成heatmap.jpg