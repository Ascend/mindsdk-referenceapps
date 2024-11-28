
# 基于mxBase的驾驶员状态识别
## 1 介绍
### 1.1 简介
本开发样例是基于mxBase开发的端到端推理的应用程序，可在昇腾芯片上识别视频中的驾驶员状态，然后送给分类模型进行推理，再由模型后处理得到驾驶员的状态识别结果。 其中包含Rcf模型的后处理模块开发。 主要处理流程为：  输入视频>视频解码  >图像前处理 >分类模型推理 >分类模型后处理 >驾驶员状态

推荐适用场景：在拍摄光线充足的情况下，拍摄角度可体现驾驶员身体上半身侧向图像(拍摄角度为副驾驶上方)，图像上驾驶员身体大部分居于图像区域内，且占比不小于50%、无大面积遮挡，支持的分辨率最佳为640*480。 本项目可识别输出为10种驾驶状态，分别为安全驾驶、右手打字、 右手打电话、 左手打字、 左手打电话、 调收音机、 喝饮料、 拿后面的东西、 整理头发和化妆、和其他乘客说话。

### 1.2 支持的产品

本项目以昇腾Atlas 300I pro和 Atlas300V pro为主要的硬件平台。


### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 


## 2 设置环境变量

在执行后续步骤前，需要设置环境变量：


```bash
# 执行环境变量脚本使环境变量生效
. ${ascend-toolkit-path}/set_env.sh
. ${mxVision-path}/set_env.sh
# mxVision-path: mxVision安装路径
# ascend-toolkit-path: CANN安装路径
```
## 3 准备模型
**步骤1** 下载模型相关文件

根据[链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/DriverStatusRecognition/model.zip)下载得到resnet50-90-dirver_detection-air.air文件，将该文件放入convert目录。

**步骤2** 转换模型格式

进入到convert目录，执行以下命令：
```
atc --model=./resnet50-90-dirver_detection-air.air --soc_version=Ascend310P3 \
    --framework=1 --output=./resnet50-dirver_detection-air-915-yuv \
    --input_format=NCHW --input_shape="x:1,3,224,224" --enable_small_channel=1 \
    --log=error  --insert_op_conf=yuv_aipp.config 
```
执行该命令后会在当前文件夹下生成项目需要的模型文件 resnet50-dirver_detection-air-915-yuv.om。
## 4 编译与运行

**步骤1**  启动rtsp服务

按照 [教程](https://gitee.com/ascend/mindxsdk-referenceapps/blob/master/docs/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/Live555%E7%A6%BB%E7%BA%BF%E8%A7%86%E9%A2%91%E8%BD%ACRTSP%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md) 自行准备数据 并启动rtsp服务

**步骤2** 修改pipeline/dirver-detection.pipeline配置文件

第**8**行 `"rtspUrl": "rtsp://xxx.xxx.xxx.xxx:xxxx/test1.264"`中的rtsp://xxx.xxx.xxx.xxx:xxxx/test1.264替换为可用的 rtsp 流地址。

第**50**行 `"postProcessLibPath": "${mxVision-path}/lib/modelpostprocessors/libresnet50postprocess.so"`中的${mxVision-path}替换为实际的mxVision安装路径。

**步骤3** 进行驾驶员状态识别

进入项目根目录。执行以下指令：

```
python3 main.py ${告警间隔}
```
${告警间隔}表示告警的间隔时间（单位为秒）。如，若需要每30s输出告警信息，则命令为`python3 main.py 30`。

**步骤4** 查看结果

用户可在标准输出中查看驾驶员状态识别告警结果。

其中，frame_total的数值代表告警间隔期间的总帧数，st_frame的数值表示告警间隔期间识别为安全驾驶的帧数，thr的数值表示告警间隔期间识别为安全驾驶的帧数占总帧数的比例。当thr在[0, 0.2)区间时，会输出”安全驾驶占比小于阈值，严重警告“；当thr在[0.2, 0.8)区间时，会输出”安全驾驶占比小于警告值，注意“。

**步骤5**  停止服务

命令行输入Ctrl+C组合键可手动停止服务。
