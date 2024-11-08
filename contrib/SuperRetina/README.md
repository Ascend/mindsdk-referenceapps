# 基于深度学习的图像配准

## 1 介绍

### 1.1 简介

基于深度学习的图像配准基于 MindXSDK 开发，在晟腾芯片上进行图像配准。输入两幅图片，可以匹配两幅图像中的特征点。
图像配准的业务流程为：将输入的两幅图片进行归一化等预处理操作后，输入到模型中进行推理，对输出的关键点，进行极大值抑制去除相近的关键点，再进一步去除靠近边界的关键点，最后利用knn聚类算法得到可能性最大的关键点。本系统的各模块及功能描述如下：

| 序号 | 子系统   | 功能描述                   |
| ---- | -------- | -------------------------- |
| 1    | 图像输入 | 读取图像                   |
| 2    | 预处理   | 对图像进行预处理           |
| 3    | 模型推理 | 对输入进行推理并输出结果   |
| 4    | 后处理   | 从模型推理结果中解出关键点 |


### 1.2 支持的产品
本项目以昇腾Atlas 500 A2为主要的硬件平台。

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 5.0.0 | 7.0.0   |  23.0.0  |
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  |

### 1.4 三方依赖

| 软件名称    | 版本    | 
|---------|-------| 
| numpy   | 1.23.0 |
| scipy   | 1.13.1 |
| pytorch | 1.7.0 |
| tqdm    | 4.64.1 |


### 1.5 代码目录结构说明
```txt
.
│  README.mdn
│  onnx2om.sh
│
└─python
    │  main.py
    │  requirements.txt
    │  predictor.py
    │  resize.py
    │
    ├─config
    │  test.yaml
```


## 2 设置环境变量
```bash
export PYTHONPATH=${MX_SDK_HOME}/python/:$PYTHONPATH
export install_path=${install_path}
. ${install_path}/set_env.sh
. ${MX_SDK_HOME}/set_env.sh
```

注：
**${MX_SDK_HOME}** 替换为用户自己的MindX_SDK安装路径（例如："/home/xxx/MindX_SDK/mxVision"）；

**${install_path}** 替换为CANN开发套件包所在路径（例如：/usr/local/Ascend/ascend-toolkit/latest）。


## 3 准备模型

模型转换使用的是ATC工具，具体使用教程可参考[《ATC工具使用指南》](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/80RC2alpha003/devaids/auxiliarydevtool/atlasatc_16_0001.html)。

**步骤1** 获取.onnx模型
本文提供已完成转换的onnx模型供开发者使用：https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/SuperRetina/models.zip

**步骤2** **onnx转om** 将步骤2中转换获得的onnx模型存放至**服务器端**的SuperRetina/目录下，执行如下命令：
```bash
bash onnx2om.sh ./SuperRetina.onnx ./SuperRetina
```


## 4 运行

**步骤1**  在./python目录下创建./samples文件夹，下载需要配准的图像上传到文件夹中。（注意：图像宽高需根据模型调整，若不对本文提供的模型做改变，需限制为768*768）。

**步骤2**  按照第 2 小节 环境依赖 中的步骤设置环境变量。

**步骤3**  按照第 3 小节 模型转换 中的步骤获得 om 模型文件,在./python目录下创建./model文件夹，将om文件移动到model文件夹中。

**步骤4**  在./python目录下运行predictor.py，首先按需求修改路径：

```bash
    f1 = './data/samples/query.jpg'   # image path
    f2 = './data/samples/refer.jpg'   # image path
    merged = align_image_pair(f1, f2, model, show=True)
```

执行如下命令：

```bash
python predictor.py
```
输出两幅图像，分别命名为match_result.jpg和result.jpg。



## 5 精度验证

**步骤1**  在./python目录下创建./data文件夹，下载[FIRE数据集]( https://projects.ics.forth.gr/cvrl/fire/FIRE.7z)，解压后将./FIRE文件夹，放到./data文件夹。

**步骤2**  在./python目录下执行resize脚本，将数据集图片缩放到模型的输入的大小，同时也对groudTruth做了缩放。缩放后的图片位于./data/FIRE/Images/resized文件夹下。

**步骤3**  按照第 2 小节 环境依赖 中的步骤设置环境变量。

**步骤4**  按照第 3 小节 模型转换 中的步骤获得 om 模型文件,在./python目录下创建./model文件夹,将om文件移动到model文件夹中。

**步骤5**  在./python目录下运行main.py函数，执行如下命令：

```bash
python main.py 
```

结果输出到终端，结果如下所示：

```bash
100%|██████████| 133/133 [1:37:18<00:00, 43.90s/it]
----------------------------------------
Failed:0.00%, Inaccurate:0.00%, Acceptable:100.00%
----------------------------------------
S: 0.999, P: 0.894, A: 0.960, mAUC: 0.951
```