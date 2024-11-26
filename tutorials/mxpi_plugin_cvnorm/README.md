


# MxVision快速入门——开发opencv的均一化插件

## 1 介绍

### 1.1 简介

opencv的均一化插件开发样例基于c++代码，生成SDK插件，以用于自定义插件后处理开发。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本

| MxVision版本 | CANN版本  | Driver/Firmware版本 |
|------------|---------|-------------------|
| 6.0.RC2    | 8.0.RC2 | 24.1.RC2          |
| 6.0.RC3    | 8.0.RC3 | 24.1.RC3          |


## 2 设置环境变量

```
# MindX SDK环境变量:
.${SDK-path}/set_env.sh

# CANN环境变量:
.${ascend-toolkit-path}/set_env.sh

# 环境变量介绍
SDK-path:SDK mxVision安装路径
ascend-toolkit-path:CANN安装路径
```

## 3 编译与运行

**步骤1：** 在项目根目录下创建build文件夹，使用cmake命令进行编译，生成插件*.so文件：

```
# 创建build目录
mkdir build
cd build
# cmake编译
cmake ..
make
```
**步骤2：** 查看结果：执行成功后会在`mindxsdk-referenceapps/lib/plugins/`下生成插件*.so文件。