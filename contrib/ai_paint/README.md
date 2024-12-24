# CGAN Ai Painting

## 1 介绍
### 1.1 简介
  本开发样例基于Mind SDK实现了从结构化描述生成对应风景照片的功能。
  参考以下链接说明： <br/>
  参考设计来源 - https://www.hiascend.com/zh/developer/mindx-sdk/landscape?fromPage=1 <br/>
  相关代码 - https://gitee.com/ascend/samples/tree/master/cplusplus/contrib/AI_painting <br/>

### 1.2 支持的产品

本项目以昇腾Atlas 300I Pro, Atlas 300V Pro和Atlas 500 A2为主要的硬件平台。

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 5.0.0     | 7.0.0     |  23.0.0    |
| 6.0.RC2   | 8.0.RC2   |  24.1.RC2  |
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  |

### 1.4 代码目录结构说明
```
.
|-------- model
|--------   |---- AIPainting_v2.om         //转换后的OM模型
|--------   |---- AIPainting_v2.pb         //原始PB模型
|-------- pipeline
|           |---- ai_paint.pipeline        //流水线配置文件
|-------- python
|           |---- main.py                      //测试样例
|           |---- net_config.ini               //模型输入参数与说明
|-------- result                           //推理结果存放路径，由程序运行生成
|-------- README.md 
```

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh
```

## 3 准备模型
**步骤1** 获取原模型PB模型。

  - https://modelzoo-train-atc.obs.cn-north-4.myhuaweicloud.com/003_Atc_Models/AE/ATC%20Model/painting/AIPainting_v2.pb

**步骤2** 通过atc工具可转换为对应OM模型，转换命令

```
atc --output_type=FP32 --input_shape="objs:9;coarse_layout:1,256,256,17"  --input_format=NHWC --output="AIPainting_v2" --soc_version=${SOC_VERSION} --framework=3  --model="AIPainting_v2.pb"
```
*当使用昇腾Atlas 300I Pro、Atlas 300V Pro硬件平台时，SOC_VERSION为 Ascend310P3；当使用昇腾Atlas 500 A2硬件平台时，SOC_VERSION为 Ascend310B1。

将转换出来的om模型放入'样例所在目录/model'下
## 4 运行

**步骤1**  执行样例
进入python目录，修改net_config.ini文件中对应的网络参数，随后执行
```
python3 main.py
```
**步骤2**  查看结果
执行完毕后，默认输出的矢量图layoutMap.jpg和结果图像resultImg.jpg位于result目录下