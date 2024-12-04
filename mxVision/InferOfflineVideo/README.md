

# 离线视频推理

## 1 介绍

### 1.1 简介

离线视频推理项目基于mxVision SDK开发的参考用例，用于在视频流中检测出目标。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 依赖软件 | 版本       | 说明                           | 使用教程                                                     |
| -------- | ---------- | ------------------------------ | ------------------------------------------------------------ |
| live555  | 1.10       | 实现视频转rstp进行推流         | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) |
| ffmpeg   | 4.2.1 | 实现mp4格式视频转为264格式视频 | [链接](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/pc%E7%AB%AFffmpeg%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md#https://ffmpeg.org/download.html) |

**注意：**

第三方库默认全部安装到/usr/local/下面，全部安装完成后，请设置环境变量
```bash
export PATH=/usr/local/ffmpeg/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/ffmpeg/lib:$LD_LIBRARY_PATH
```

### 1.5 代码目录结构说明

```
.
├── main.cpp
├── pipeline
│   └── regular.pipeline
├── models
│   └── yolov3
|         ├── aipp_yolov3_416_416.aippconfig
│         ├── yolov3_tf_bs1_fp16.cfg
│         └── coco.names
├── test                            # 需用户手动创建文件夹
├── run.sh
└── README.md
```

## 2 设置环境变量

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh       # sdk安装路径，根据实际安装路径修改
```

## 3 准备模型

**步骤1：** 在ModelZoo上下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2：** 将获取到的YOLOv3模型文件内的`.pb`文件存放至`InferOfflineVideo/models/yolov3/`下。
 
**步骤3：** 模型转换
在文件夹 `InferOfflineVideo/models/yolov3/` 下，执行模型转换命令

```bash
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
```

执行完模型转换脚本后，会生成相应的`.om`模型文件。执行后终端输出为：

```bash
ATC start working now, please wait for a moment.

ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4 编译与运行

**步骤1：** 准备测试视频。视频流格式为264，放入 `/InferOfflineVideo/test/` 文件夹下，并修改命名为 `input.264`。

**步骤2：** 在 `/InferOfflineVideo/test/` 文件夹下拉起Live555服务。[Live555拉流教程](../../docs/参考资料/Live555离线视频转RTSP说明文档.md)

**步骤3：** 修改`pipeline/regular.pipeline`文件：

①：将文件中第8行的 “rtspUrl” 字段值替换为可用的 rtsp 流源地址（目前只支持264格式的rtsp流，例："rtsp://xxx.xxx.xxx.xxx:xxx/input.264", 其中xxx.xxx.xxx.xxx:xxx为ip和端口号，端口号需同Live555服务的起流端口号一致）；

②：将所有 “deviceId” 字段值替换为实际使用的device的id值，即文件的第4、18、29、41行，可用的 device id 值可以使用命令：`npu-smi info` 查看

**步骤4：** 修改日志打印级别。打开文件 `${MX_SDK_HOME}/config/logging.conf` ，依次修改第17行、第22行的字段值为 0 ，如下所示：

```
global_level = 0
console_level = 0
```

**步骤5：** 运行。在样例根目录下执行命令 `bash run.sh`

**步骤6：** 查看结果。正常启动后，控制台会输出检测到各类目标的对应信息。手动执行 `ctrl + C` 结束程序