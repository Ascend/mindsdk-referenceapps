# FFmpeg-Ascend-Plugin

## 介绍

mxVison ascend 硬件平台内置了视频相关的硬件加速解码器，
为了提升用户的易用性，mxVision提供了FFmepg-Plugin解决方案。

该样例的处理流程为：
```
准备芯片及环境 -> 安装CANN版本包 -> 下载开源FFmpeg代码 -> 拉取FFmpeg-Plugin代码 -> 应用patch -> 编译 -> 执行
```

## 支持的产品
Atlas 300I Pro, Atlas 300V Pro和Atlas A500 A2

### 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 5.0.0 | 7.0.0   |  23.0.0  |
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  |

## 支持的功能
|功能|mpeg4|h264/h265|多路|
|:----:|:----:|:----:|:----:|
|硬件解码|√|√|√|
|硬件编码|√|√|√|
|硬件转码|√|√|√|
|硬件缩放|√|√|√|

## 安装 CANN
[详情请参考CANN用户指南](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/80RC3alpha001/softwareinst/instg/instg_0001.html)

## 下载开源FFmpeg代码
[FFmpeg-n4.4.4 Source code](https://github.com/FFmpeg/FFmpeg/releases/tag/n4.4.4)

zip包解压
```shell
unzip FFmpeg-n4.4.4.zip
```
tar.gz包解压
```shell
tar -zxvf FFmpeg-n4.4.4.tar.gz
```

## FFmpeg-Plugin目录结构

FFmpeg-Plugin 目录主要文件：
```text
|-- ascend_ffmpeg.patch
|
|-- README.md (FFmpeg-Plugin 使用手册)
```

## 应用patch
```shell
cd FFmpeg-n4.4.4
patch -p1 -f < {FFmpeg-Plugin-Dir}/AscendFFmpegPlugin/ascend_ffmpeg.patch
```

## 重新编译

### 设置环境变量：
* `ASCEND_HOME`     Ascend 安装的路径，一般为 `/usr/local/Ascend`
* 执行命令
    ```bash
    export ASCEND_HOME=/usr/local/Ascend
    ```

### 编译
* `FFMPEG_LIB_PATH` FFmpeg 编译安装的 lib 文件路径（一般为 FFmpeg 安装目录下的 lib 目录， 安装目录由安装时的 --prefix 编译选项来指定）。
* `LD_LIBRARY_PATH` 指定 ffmpeg 程序运行时依赖的动态库查找路径。
* 编译选项说明
  ```text
    prefix : FFmpeg 及相关组件安装目录
    enable-shared : FFmpeg 允许生成 so 文件
    extra-cflags : 添加第三方头文件
    extra-ldflags : 指定第三方库位置
    extra-libs : 添加第三方 so 文件
    enable-ascend : 允许使用 ascend 进行硬件加速
  ```
* 编译命令
在 /FFmpeg-n4.4.4 文件夹下执行以下命令
  ```bash
  ./configure \
      --prefix=./ascend \
      --enable-shared \
      --extra-cflags="-I${ASCEND_HOME}/ascend-toolkit/latest/acllib/include" \
      --extra-ldflags="-L${ASCEND_HOME}/ascend-toolkit/latest/acllib/lib64" \
      --extra-libs="-lacl_dvpp_mpi -lascendcl" \
      --enable-ascend \
      && make -j && make install
  ```

### 添加FFmpeg环境变量
FFMPEG_LIB_PATH: {your_dir}/FFmpeg-n4.4.4/ascend/lib

示例: /home为FFmpeg-n4.4.4所在目录
```shell
export FFMPEG_LIB_PATH=/home/FFmpeg-n4.4.4/ascend/lib
```

```shell
export LD_LIBRARY_PATH=${FFMPEG_LIB_PATH}:$LD_LIBRARY_PATH
```

## 运行
当前目录或者 FFmpeg 安装目录(ascend/bin)下均会生成 `ffmpeg` 可执行文件，均可以使用。
相关指令参数：

* `-hwaccel`    -   指定采用 ascend 来进行硬件加速, 用来做硬件相关初始化工作。

解码相关参数(注意：解码相关参数需要在 `-i` 参数前设置)：
* `-c:v`        -   指定解码器为 h264_ascend (解码 h265 格式可以使用 h265_ascend)。
* `-device_id`  -   指定硬件设备 id 为 0。取值范围取决于芯片个数，默认为 0。 `npu-smi info` 命令可以查看芯片个数
* `-channel_id` -   指定解码通道 id [0-255], 默认为0, 若是指定的通道已被占用, 则自动寻找并申请新的通道。
* `-resize`     -   指定缩放大小, 输入格式为: {width}x{height}。宽高:[128x128-4096x4096], 宽高相乘不能超过 4096*2304（此为h264的约束）。宽要与 16 对齐，高要与 2 对齐。 
* `-i`          -   指定输入文件（支持h264和h265及rtsp视频流, 其他视频格式不做保证）。

编码相关参数(注意：编码相关参数需要在 `-i` 参数后设置)：
* `-c:v`        -   指定编码器为 h264_ascend (编码成 h265 格式可以使用 h265_ascend)。
* `-device_id`  -   指定硬件设备 id 为 0。取值范围取决于芯片个数，默认为 0。 `npu-smi info` 命令可以查看芯片个数。
* `-channel_id` -   指定编码通道 id [0-127], 默认为 0, 若是指定的通道已被占用, 则自动寻找并申请新的通道。
* `-profile`    -   指定视频编码的画质级别（0: baseline, 1: main, 2: high, 默认为 1。 H265 编码器只支持 main）。
* `-rc_mode`    -   指定视频编码器的速率控制模式（0: CBR, 1: VBR, 默认为 0）。
* `-gop`        -   指定关键帧间隔, [1, 65536], 默认为 30。
* `-frame_rate` -   指定帧率, [1, 240], 默认为25。
* `-max_bit_rate` - 限制码流的最大比特率, [2， 614400], 默认为 20000。
* `-movement_scene` - 指定视频场景（0：静态场景（监控视频等）， 1：动态场景（直播，游戏等））, 默认为 1。

```bash
./ffmpeg -hwaccel ascend -c:v h264_ascend -i test.264 -c:v h264_ascend out.264
```

```bash
./ffmpeg -hwaccel ascend -c:v h264_ascend -device_id 0 -channel_id 0 -resize 1024x1000 -i test.264 -c:v h264_ascend -device_id 0 -channel_id 0 -profile 2 -rc_mode 0 -gop 30 -frame_rate 25 -max_bit_rate 20000 out.264
```

```bash
./ffmpeg -hwaccel ascend -c:v h264_ascend -i test.264 out.yuv
./ffmpeg -hwaccel ascend -s 1920x1080 -pix_fmt nv12 -i out.yuv -c:v h264_ascend out.264
```