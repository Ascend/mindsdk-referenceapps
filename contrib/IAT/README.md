# MindX SDK -- RGB图像的夜间增强参考设计

## 1、 介绍

### 1.1 简介
基于 MindX SDK 实现 IAT 模型的推理，在 LOL 数据集上达到 $PSNR\ge$23, $SSIM\ge 0.8$, 并把可视化结果保存到本地，达到预期的功能和精度要求。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称      | 版本             |
| ------------- | ---------------- |
| numpy         | 1.24.0           |
| opencv-python | 4.10.0.84       |
| timm       | 0.4.10           |
| torch       | 0.4.10           |


## 2、 设置环境变量

在编译运行项目前，需要设置环境变量：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```


## 3、 准备模型

**步骤1** 

本文提供已转换好的onnx模型：[IAT_lol-sim.onnx](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/IAT/IAT_lol-sim.onnx)
下载后放到项目目录的models文件夹

**步骤2** 

将模型转换为om模型，在models目录下，执行以下命令生成om模型
```
atc --framework=5 --model=./IAT_lol-sim.onnx --input_shape="input_1:1,3,400,600" --output=IAT_lol-sim --soc_version=Ascend310P3
```
执行完模型转换脚本后，会生成相应的IAT_lol-sim.om模型文件。 执行后终端输出为（模型转换时出现的warn日志可忽略）：

```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

## 4、 运行

**步骤1** 

将要推理的test.png图片放到本项目./data/文件夹下，执行以下命令:

```
python3 main.py
```

即可在./data/目录下得到推理后的结果result.png文件.

**步骤2** 

精度测试

下载LOLv1数据集，在[论文地址](https://daooshee.github.io/BMVC2018website/)Download Links章节下载LOL数据集。
将数据集解压后将其中的测试集目录(eval15)和文件放到本项目./data/文件夹下,如下图所示:

```
  ├── data		  
  	├──eval15  	# 精度测试数据集
  		├──high
  		├──low
```

切换到项目根目录下，将main.py中的主函数改为调用test_precision()，修改如下:

```
#142行修改为 test_precision()
```

再次运行代码
```
python3 main.py
```

即可得到精度测试结果,测试结果如下：

![模型计算量](images/精度测试.jpeg)
