# Vision SDK快速入门——mxBaseV2视频编解码接口使用

## 1 介绍

### 1.1 简介
本样例属于Vision SDK快速入门样例，用于向用户介绍mxBaseV2系列视频编解码接口的基本使用。本系统以昇腾Atlas 300V，Atlas 300I pro和 Atlas300V pro为主要的硬件平台。

本样例以本地视频拉流、解码、编码、编码结果保存为例子，着重介绍解码接口VideoDecoder和编码接口VideoEncoder的实例化和功能接口（Decode接口、Encode接口）使用。

建议用户按照README跑通示例代码后，通过阅读示例源码的方式，更深入的理解mxBaseV2系列视频编解码接口基本使用。

### 1.2 支持的产品
本项目以昇腾Atlas 300V，Atlas 300I pro和 Atlas300V pro为主要的硬件平台。

### 1.3 支持的版本

| Vision SDK版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 
| 6.0.0   | 8.0.0   |  24.1.0  |

### 1.4 三方依赖

本项目除了依赖昇腾Driver、Firmware、CANN和Vision SDK及其要求的配套软件外，还需额外依赖以下软件：

| 软件名称   | 版本   |
|--------| ------ |
| av | 10.0.0 |
| ffmpeg | 3.4.11 |

注意：ffmpeg需要用户自行到相关网站下载源码进行编译安装。

## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：

```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${Vision SDK-path}/set_env.sh
export FFMPEG_PATH=${ffmpeg-path}
export LD_LIBRARY_PATH=${ffmpeg-lib-path}:$LD_LIBRARY_PATH
# Vision SDK-path: Vision SDK安装路径
# ascend-toolkit-path: CANN安装路径
# ffmpeg-path: ffmpeg安装路径，通常为/usr/local/ffmpeg
# ffmpeg-lib-path: ffmpeg的lib库安装路径，通常为/usr/local/ffmpeg/lib
```

##  3 编译与运行
### 3.1 C++样例运行
**步骤1：准备视频** 

准备一个H264格式的视频文件，并放至在本项目路径下。

**步骤2：修改main.cpp文件，指定VideoDecoder和VideoEncoder的基本初始化参数**  


第**332**行到第**354**行展示了VideoDecoder和VideoEncoder的主要配置项，用户可以结合Vision SDK官方文档根据需要调整。本样例中仅指定必要配置项，如下所示：

第**333**行 `"std::string filePath = "${filePath}"`中的${filePath}替换为步骤2中视频文件实际的路径。

第**334**行 `"int width = ${width}"`中的${width}替换为步骤2中视频帧实际的宽。

第**335**行 `"int height = ${height}"`中的${height}替换为步骤2中视频帧实际的高。

第**350**行 `"vEncodeConfig.srcRate = ${fps}"`中的${fps}替换为步骤2中视频实际的帧率。

第**352**行 `"vEncodeConfig.displayRate = ${fps}"`中的${fps}替换为步骤2中视频实际的帧率。


**步骤3：编译**

进入项目根目录的C++目录下，执行以下命令:
```
bash build.sh
```

**步骤4：运行**

进入项目根目录的C++目录下，执行以下命令:
```
./main
```

**步骤5：查看结果**

保存后的视频文件（命令为output.264）会在同级目录下，打开该文件即可查看编码结果。



### 3.2 Python样例运行


**步骤1：准备视频**

准备一个H264格式的视频文件，并放至在本项目路径下。


**步骤2：修改main.py文件，指定VideoDecoder和VideoEncoder的基本初始化参数**

第**149**行到第**175**行展示了VideoDecoder和VideoEncoder的主要配置项，用户可以结合Vision SDK官方文档根据需要调整。本样例中仅指定必要配置项，如下所示：

第**150**行 `"file_path = "${file_path}”"`中的${file_path}替换为步骤1中视频文件实际的路径。

第**151**行 `"width = ${width}"`中的${width}替换为步骤1中视频帧实际的宽。

第**152**行 `"height = ${height}"`中的${height}替换为步骤1中视频帧实际的高。

第**170**行 `"venc_conf.srcRate = ${fps}"`中的${fps}替换为步骤1中视频实际的帧率。

第**172**行 `"venc_conf.srcRate = ${fps}"`中的${fps}替换为步骤1中视频实际的帧率。


**步骤3：运行**

进入项目根目录的Python目录下，执行以下命令:
```
python3 main.py
```

**步骤4：查看结果**

保存后的视频文件（命令为output.264）会在同级目录下，打开该文件即可查看编码结果。

_注意：为提高Python示例代码易读性，Python示例代码的线程模型与C++示例代码保持一致。在实际业务中，为提高性能，Python代码的线程模型应适度精简。_

