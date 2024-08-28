# SDK后处理开发教程

## 1 介绍

### 1.1 简介
本应用基于SDK提供的后处理框架，实现自定义resnet50后处理类和yolov3后处理类，并编译生成得到对应so文件。

### 1.2 支持的产品
本应用以昇腾 Atlas 300 卡为主要的硬件平台

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0 | 7.0.0   |  23.0.0  |


## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：

```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
# mxVision: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
```

##  3 编译
### 步骤1 编译

- 在项目根目录创建cmakeDir目录并进入该目录
- 执行cmake.. && make编译项目。

###  步骤2 查看结果

编译得到的so保存在项目根目录的lib目录下。其中，libsamplepostprocess.so用于restnet50的后处理；libyolov3postprocess.so用于yolov3的后处理。

## 4 常见问题

### 4.1 如何使用编译得到的后处理so

问题描述：如何使用编译得到的后处理so？

解决方案：使用方式请参考图像目标检测参考样例[链接]（https://www.hiascend.com/marketplace/mindx-sdk/case-studies/596c9426-439f-45cd-bd67-5265b41a9075)。
