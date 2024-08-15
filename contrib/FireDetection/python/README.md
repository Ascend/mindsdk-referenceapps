# 基于mxBase的高速公路车辆火灾识别

## 1 介绍

高速公路车辆火灾识别基于 MindX Vision 开发，在 Atlas 300V、Atlas 300V Pro 上进行目标检测。项目主要流程为：通过av模块打开本地视频文件、模拟视频流，然后进行视频解码，解码结果经过模型推理进行火焰和烟雾检测，如果检测到烟雾和火灾则在日志中进行告警。解码后的视频图像会再次编码保存至指定位置。

### 1.1 支持的硬件形态
支持Atlas 300V和Atlas 300V Pro

### 1.2 支持的版本

  | MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- | 
  | 6.0.RC2 | 8.0.RC2   |  24.1.RC2  | 

### 1.3 软件方案介绍

基于MindX Vision的mxBase架构的高速公路车辆火灾识别业务流程为：经av库打开本地视频文件、模拟视频流——>将视频解码成图片——>将图像缩放至满足检测模型要求的大小——>将缩放后的图像输入模型进行车辆火灾识别，如果发生检测到火焰或者烟雾则在日志层面进行告警——>将解码后的视频图像编码保存至指定文件路径。

### 1.4 代码目录结构与说明

本项目目录如下图所示：

```
├── frame_analyzer.py  // 视频帧分析
├── infer_config.json  // 服务配置
├── utils.py  
├── main.py  
└── README.md
```
## 2 Python环境依赖
本项目除了依赖昇腾Driver、Firmware、CANN和MxVision及其要求的配套软件外，还需额外依赖以下python软件：

| 软件名称 | 版本   |
| -------- | ------ |
| av | 10.0.0 |
| numpy | 1.23.5 |
| python   | 3.9.2  |

## 3 模型下载和转换
### 3.1 下载模型相关文件
- **步骤1**  根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/FireDetection/models.zip)下载并解压得到firedetection.onnx文件和aipp_yolov5.cfg文件。

###  3.2 转换模型格式
- **步骤1** 设置环境变量 

       . /usr/local/Ascend/ascend-toolkit/set_env.sh # Ascend-cann-toolkit开发套件包默认安装路径，根据实际安装路径修改
- **步骤2** 将onnx格式模型转换为om格式模型

       atc --model=./firedetection.onnx --framework=5 --output=./firedetection --input_format=NCHW --input_shape="images:1,3,640,640"  --out_nodes="Transpose_217:0;Transpose_233:0;Transpose_249:0"  --enable_small_channel=1 --insert_op_conf=./aipp_yolov5.cfg --soc_version=Ascend310P3 --log=info

##  4 启动和停止高速公路火灾识别服务
### 4.1 启动高速公路火灾识别服务

- **步骤1** 设置环境变量 

       . /usr/local/Ascend/ascend-toolkit/set_env.sh # Ascend-cann-toolkit开发套件包默认安装路径，根据实际安装路径修改
       . ${MX_SDK_HOME}/mxVision/set_env.sh # ${MX_SDK_HOME}替换为用户的SDK安装路径

- **步骤2** 设置高速公路车辆火灾识别服务配置（修改infer_config.json文件） ，支持的配置项如下所示 ：


|       配置项字段       | 配置项含义           |
|:-----------------:|-----------------|
|    video_path     | 用于火灾识别的视频文件路径   |
|    model_path     | om模型的路径         |
|     device_id     | 运行服务时使用的NPU设备编号 |
| skip_frame_number | 指定两次推理的帧间隔数量    |
| video_saved_path  | 指定编码后视频保存的文件路径  |
|       width       | 用于火灾识别的视频文件的宽度  |
|      height       | 用于火灾识别的视频文件的高度  |


*device_id取值范围为[0, NPU设备个数-1]，`npu-smi info` 命令可以查看NPU设备个数；skip_frame_number需要大于等于1，建议根据实际业务需求设置，推荐设置为3；width和height的取值范围为[128, 4096]，请用户根据实际的视频帧数据进行适当设置，需大于或等于实际的视频帧数据高，否则会无解码输出，设置过大将会产生多余的内存资源开销。；video_path所指定的视频文件需为H264编码；video_saved_path所指定的文件每次服务启动时会被覆盖重写。

- **步骤3** 启动火灾检测服务。火灾检测结果在warning级别日志中体现；编码视频文件保存在配置文件指定的路径下。

      python3 main.py
### 4.2 停止高速公路火灾识别服务
- 停止服务有如下两种方式：

    1.视频文件分析完毕后可自动停止服务。 2.命令行输入Ctrl+C组合键可手动停止服务。
## 5 常见问题


- 问题描述：获取视频流失败。

  解决方案：检查av库的版本是否为10.0.0。
- 问题描述：获取视频流成功，但是执行完毕后无编码保存的文件。

  解决方案：检查配置文件中的width和height值是否大于等于真实视频宽、高。如果配置错误，可能会导致解码器无法正常工作，最终影响后续的视频分析和视频编码。