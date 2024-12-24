# 视频伪装物体检测

## 1 介绍
### 1.1 简介

基于 VisionSDK 实现 SLT-Net 模型的推理。输入连续几帧伪装物体的视频序列，输出伪装物体掩膜 Mask 图。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro。


### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |


### 1.4 代码目录结构与说明

本sample工程名称为 VCOD_SLTNet，工程目录如下图所示：

```
──VCOD_SLTNet
    ├── inference.py   # 推理文件
    └── README.md
```

### 1.5 三方依赖

| 软件名称      | 版本     |
|-----------|--------|
| Python    | 3.9.2  |
| numpy     | 1.23.1 |
| imageio   | 2.27.0 | 
| Pillow    | 9.3.0  | 
| cv2       | 4.5.5  |
| timm      | 0.4.12 |
| tqdm      | 4.64.1 |
| mindspore | 2.0.0  |


## 2 设置环境变量

```bash
#设置CANN环境变量，ascend-toolkit-path为cann安装路径
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```


## 3. 准备模型

**步骤1:** 模型下载

下载 [models.zip 模型压缩包](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/sltnet/models.zip) ，在项目工程目录下解压获得 `sltnet.onnx` 模型文件

注意：
模型压缩包解压之后会获得"sltnet.om"，但是该模型不能直接使用，需要通过步骤2利用atc工具将onnx模型重新转换为om模型

**步骤2:** 模型转换

```
atc --framework=5 --model=sltnet.onnx --output=sltnet --input_shape="image:1,9,352,352" --soc_version=Ascend310P3 --log=error
```

**步骤3:** 查看结果：执行完模型转换后，若提示如下信息说明模型转换成功。

```
ATC run success, welcome to the next use.
```


## 4. 运行

**步骤1:** 数据下载

通过[数据集链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/sltnet/MoCA_Video.zip)下载 `MoCA_Video.zip` 数据集压缩包并解压；数据集文件目录如下所示：

```
--data
    └── TestDataset_per_sq           # 测试数据集
        ├── flower_crab_spider_1     # 不同场景
            ├── GT                   # Ground Truth
                ├── 00000.png
                ├── .....
            └── Imgs                 # 输入图片序列
                ├── 00000.jpg
                ├── .....
        ......

```

**步骤2:** 运行

使用如下命令，运行 `inference.py` 脚本：

```
python inference.py --datapath ${MoCA_Video数据集路径} --save_root ./results/ --om_path ./sltnet.om --testsize 352 --device_id 0
```

参数说明：

datapath：下载解压数据MoCA_Video以后，目录中 `TestDataset_per_sq` 的上一级目录。

save_root：结果保存路径。

om_path：om 模型路径。

testsize：图片 resize 的大小，当前固定为 352。

device_id：设备编号。


运行输出如下：

```
  0%|                                                                                                       | 0/713 [00:00<?, ?it/s]>  ./results/arctic_fox/Pred/00000.png
  0%|▏                                                                                              | 1/713 [00:00<10:31,  1.13it/s]>  ./results/arctic_fox/Pred/00005.png
  0%|▎                                                                                              | 2/713 [00:01<09:01,  1.31it/s]>  ./results/arctic_fox/Pred/00010.png
  0%|▍                                                                                              | 3/713 [00:02<08:30,  1.39it/s]>  ./results/arctic_fox/Pred/00015.png
  1%|▌                                                                                              | 4/713 [00:02<08:13,  1.44it/s]>  ./results/arctic_fox/Pred/00020.png
```

将展示剩余运行时间以及生成图片的路径。


**步骤3:** 查看结果

在步骤2中设置的结果保存路径下存放着伪装物体掩膜 Mask 图。