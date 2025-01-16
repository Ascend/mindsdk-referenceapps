# passengerflowestimation客流量检测

## 1 介绍

### 1.1 简介
passengerflowestimation基于Vision SDK开发，在昇腾芯片上进行客流量统计，输入一段视频，最后可以得出在某一时间内的客流量。本项目适用于俯视角度较大，并且人流量不是非常密集的视频中人流量统计。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：
|Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

### 1.4 三方依赖

| 依赖软件 | 版本       | 说明                           | 使用教程                                                     |
| -------- | ---------- | ------------------------------ | ------------------------------------------------------------ |
| live555  | 1.10       | 实现视频转rstp进行推流         | [链接](https://gitee.com/ascend/mindsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) |

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：下载原始yolov4模型-[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/PassengerflowEstimation/ATC%20Yolov4%28FP16%29%20from%20Pytorch.zip)，并将解压后获取到的.onnx文件存放至本案例代码的PassengerflowEstimation/models 目录下。

**步骤2**： 进入PassengerflowEstimation/models目录执行以下命令
```
atc --model=./yolov4_dynamic_bs.onnx --framework=5 --output=yolov4 --input_format=NCHW --output_type=FP32 --soc_version=Ascend310P3 --input_shape="input:1,3,608,608" --log=info --insert_op_conf=./aipp_Passengerflowdetection.config 
```

**步骤3**： 转换opencvosd模型,执行以下命令
```
cd ${SDK_INSTALL_PATH}/mxVision/operators/opencvosd #根据实际SDK安装路径修改
bash generate_osd_om.sh
```

## 4 编译与运行
**步骤1**：配置pipeline

根据实际的网络视频流，修改passengerflowestimation.pipeline文件第9行：
```
#将rtspUrl的值修改为实际的rtsp网络视频流地址
"mxpi_rtspsrc0": {
    "factory": "mxpi_rtspsrc",
    "props": {
        "rtspUrl": "rtsp://xxx.xxx.xx.xxx:xxxx/xxxx.264",
        "channelId": "0"
    },
    "next": "queue0"
},
```
根据实际的环境变量，修改passengerflowestimation.pipeline文件第87行：
```
#将postProcessLibPath的值修改为libyolov3postprocess.so的绝对路径路径（在SDK安装路径下）
"mxpi_objectpostprocessor0": {
    "props": {
        "dataSource": "mxpi_tensorinfer0",
        "postProcessConfigPath": "./models/yolov4.cfg",
        "labelPath": "./models/yolov3.names",
        "postProcessLibPath": "${Vision SDK安装路径}/lib/modelpostprocessors/libyolov3postprocess.so"
    },
    "factory": "mxpi_objectpostprocessor",
    "next":  "mxpi_selectobject0"
},
```

**步骤2**：编译后处理插件so

在项目根目录下执行
```
bash build.sh #编译
chmod 440 ./plugins/mxpi_passengerflowestimation/build/libmxpi_passengerflowestimation.so #修改so权限
chmod 440 ./plugins/mxpi_selectobject/build/libmxpi_selectobject.so #修改so权限
cp ./plugins/mxpi_passengerflowestimation/build/libmxpi_passengerflowestimation.so ${SDK_INSTALL_PATH}/mxVision/lib/plugins #拷贝so到相应路径，${SDK_INSTALL_PATH}根据实际SDK安装路径修改
cp ./plugins/mxpi_selectobject/build/libmxpi_selectobject.so ${SDK_INSTALL_PATH}/mxVision/lib/plugins #拷贝so到相应路径，${SDK_INSTALL_PATH}根据实际SDK安装路径修改
```

**步骤3**：拉起Live555服务-[Live555拉流教程](../../docs/参考资料/Live555离线视频转RTSP说明文档.md)

**步骤4**：在根目录下运行
```
python3 main.py
```

**步骤5**：查看结果

生成的结果保存在result.h264文件里面（每次运行前请手动删除该文件）。