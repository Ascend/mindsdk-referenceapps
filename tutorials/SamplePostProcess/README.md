# SDK后处理开发教程

## 1 介绍

### 1.1 简介
本应用基于SDK提供的后处理框架，实现自定义resnet50后处理类和yolov3后处理类，并编译生成得到对应so文件。

### 1.2 支持的产品
x86_64 Atlas 300I（型号3010）和arm Atlas 300I（型号3000）。

### 1.3 支持的版本

本样例配套的VisionSDK版本、CANN版本、Driver/Firmware版本如下所示：

| VisionSDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0 | 7.0.0   |  23.0.0  |


## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：

```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${VisionSDK-path}/set_env.sh
# VisionSDK-path: VisionSDK安装路径
# ascend-toolkit-path: CANN安装路径
```

##  3 编译
步骤1 编译

1. 在项目根目录创建cmakeDir目录并进入该目录。
2. 执行cmake.. && make编译项目。

步骤2 查看结果

编译得到的so保存在项目根目录的lib目录下。其中，libsamplepostprocess.so用于resnet50的后处理；libyolov3postprocess.so用于yolov3的后处理。

