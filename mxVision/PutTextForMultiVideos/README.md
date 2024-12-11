# 多卡多路高性能贴字用例

## 1 介绍

### 1.1 简介
本开发样例用于演示多卡多路高性能贴字。本系统基于昇腾Atlas 300V、Atlas 300V Pro设备，主要步骤为视频拉流、解码、贴字、编码和保存视频。视频拉流通过强大的多媒体处理工具ffmpeg实现；视频解码、编码通过mxVision SDK的VideoDecoder、VideoEncoder类实现；贴字通过同级目录下的PutText参考设计实现。

本开发样例中包括两类常用分辨率：1080P分辨率（1920 * 1080）和CIF分辨率（352 * 288）。本样例要求rtsp流视频为H264格式，分辨率为1080P分辨率，帧率为25FPS。在完成贴字后，本样例会将贴字后的1080P分辨率视频帧缩放为CIF分辨率视频帧，一同进行编码和保存。

### 1.2 支持的产品
支持Atlas 300V和Atlas 300V Pro。

### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖

本项目除了依赖昇腾Driver、Firmware、CANN和MxVision及其要求的配套软件外，还需额外依赖以下软件：

| 软件名称   | 版本   |
|--------| ------ |
| ffmpeg | 3.4.11 |

注意：ffmpeg需要用户自行到相关网站下载源码进行编译安装。

## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：

```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
export FFMPEG_PATH=${ffmpeg-path}
export LD_LIBRARY_PATH=${ffmpeg-lib-path}:$LD_LIBRARY_PATH
# mxVision: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
# ffmpeg-path: ffmpeg安装路径，通常为/usr/local/ffmpeg
# ffmpeg-lib-path: ffmpeg的lib库安装路径，通常为/usr/local/ffmpeg/lib
```

##  4 编译与运行
步骤1： 下载PutText参考设计放至在项目根目录下

步骤2： 下载字库文件放至在项目根目录下


步骤3： 设置配置项

在setup.config文件中设置配置项，配置项含义如下表所示：

|    配置项字段     | 配置项含义        |
|:------------:|--------------|
|  deviceNum   | 指定执行业务占用的NPU数量      |
|  saveVideo   | 指定是否保存视频     |
| stream.ch{i} | 指定第i个rtsp流地址 |



注意：
1. deviceNum需为整数，取值范围为[1, NPU设备个数]，`npu-smi info` 命令可以查看NPU设备个数

2. saveVideor需为整数，取值范围为[0, 1]，0代表不保存贴字后视频，1代表保存贴字后视频。

3. stream.ch{i}用于指定第i个rtsp流地址。其中，i的取值范围为[0, 25 * NPU设备个数 -1]。

步骤4： 编译

步骤5： 运行

步骤6： 查看结果
