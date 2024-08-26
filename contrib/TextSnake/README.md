# TextSnake 弯曲形状文字检测

## 1 介绍

### 1.1 简介

TextSnake 弯曲形状文字检测基于 MindX SDK 开发，对图片中的任意弯曲形状文字进行检测，将检测得到的不同类的目标用曲线框标记。本方案使用在人工合成数据集SynthText上训练一个epoch，然后在其他数据集上finetune得到的TextSnake_bs1模型检测，数据集中共包含各种各样的弯曲形状文字，可以对各种角度，各种环境下的弯曲形状文字进行检测。
本项目流程为用python代码实现对图像的预处理过程，然后将处理好的图片通过 appsrc 插件输入到业务流程中。整体业务流程为：待检测图片通过 appsrc 插件输入，然后使用图像解码插件 mxpi_imagedecoder 对图片进行解码，解码后的图像输入模型推理插件 mxpi_tensorinfer 得到推理结果。最后通过输出插件 appsink 获取检测结果，并在外部进行后处理和可视化，将检测结果标记到原图上，本系统的各模块及功能描述下表所示：

| 序号 | 子系统 | 功能描述     |
| ---- | ------ | ------------ |
| 1    | 图片输入    | 	获取 jpg 格式输入图片 |
| 2    | 	检测前处理    | 更改输入图片尺寸并进行归一化 |
| 3    | 		模型推理    | 对输入张量进行推理 |
| 4    | 	结果输出    | 获取检测结果 |
| 5    | 	检测后处理    | 根据检测结果计算检测框位置和形状 |
| 6    | 		结果可视化    | 	将检测结果标注在输入图片上 |


### 1.2 支持的产品

本项目以昇腾Atlas 500 A2为主要的硬件平台

### 1.3 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 5.0.0 | 7.0.0   |  23.0.0  |
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  |

### 1.4 三方依赖

| 软件名称 | 版本     |
| -------- |--------|
| numpy   | 1.25.2 |
| scikit_image   | 0.24.0 |
| scipy   | 1.13.1 |
| easydict   | 1.13   |
| shapely | 2.0.6  |

### 1.5 代码目录结构与说明

本工程名称为TextSnake，工程目录如下图所示：

```
├── main.py  //运行工程项目的主函数
├── evaluate.py   //精度计算
├── t.pipeline      //pipeline
├── sdk.png      //流程图
├── pipeline.png      //pipeline流程图
├── 精度1.png
├── 精度1.png
└──README.md          
```

### 1.6 技术实现流程图

实现流程图如下图所示：

![流程](./sdk.png)


pipeline流程如下图所示：

![pipeline](./pipeline.png)


## 2 设置环境变量

在编译运行项目前，需要执行一下命令设置环境变量：

```bash
export PYTHONPATH=${MX_SDK_HOME}/python/:$PYTHONPATH
export install_path=${install_path}
. ${install_path}/set_env.sh
. ${MX_SDK_HOME}/set_env.sh
```
注：**${MX_SDK_HOME}** 替换为用户自己的MindX_SDK安装路径（例如："/home/xxx/MindX_SDK/mxVision"）；

**${install_path}** 替换为开发套件包所在路径（例如：/usr/local/Ascend/ascend-toolkit/latest）。


## 3 准备模型

本项目使用的模型是TextSnake模型。

本项目提供已从pytorch模型转换好的onnx 模型，需要进一步转换为om模型
pth 权重文件和 onnx 文件的下载链接
https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/TextSnake/ATC%20TextSnake%28FP16%29%20from%20Pytorch%20-%20Ascend310.zip

该压缩文件中已存在om文件，需删除后重新进行模型转换
具体步骤如下

**步骤1** 下载上述模型压缩包，获取 TextSnake.onnx 模型文件放置 TextSnake/model 目录下。

**步骤2** 进入TextSnake/model文件夹下执行命令

```
atc --model=TextSnake.onnx --framework=5 --output=TextSnake_bs1 --input_format=NCHW --input_shape="image:1,3,512,512" --log=info --soc_version=Ascend310B1
 ```

**步骤3** 执行该命令会在当前目录下生成项目需要的模型文件TextSnake_bs1.om。执行后终端输出为

 ```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

表示命令执行成功。



## 4 运行

**步骤 1**  将任意一张jpg格式的图片存到当前目录下（./TextSnake），命名为test.jpg。如果 pipeline 文件（或测试图片）不在当前目录下（./TestSnake），需要修改 main.py 的pipeline（或测试图片）路径指向到所在目录。此外，需要从
https://github.com/princewang1994/TextSnake.pytorch/tree/b4ee996d5a4d214ed825350d6b307dd1c31faa07
下载util文件夹至当前目录（./TextSnake），并对其中的detection.py和misc.py文件做如下修改(以下行数均为原代码行数)。

1.detection.py文件中第12行的init函数
```
def __init__(self, model, tr_thresh=0.4, tcl_thresh=0.6):
    self.model = model
    self.tr_thresh = tr_thresh


    self.tcl_thresh = tcl_thresh

    # evaluation mode
    model.eval()
```
修改为：
```
def __init__(self, tr_thresh=0.4, tcl_thresh=0.6):
    self.tr_thresh = tr_thresh
    self.tcl_thresh = tcl_thresh
```
2.detection.py文件中第38行
```
in_poly = cv2.pointPolygonTest(cont, (xmean, i), False)
```
修改为：
```
in_poly = cv2.pointPolygonTest(cont, (int(xmean), int(i)), False)
```
3.detection.py文件中第56行
```
if cv2.pointPolygonTest(cont, (test_pt[0], test_pt[1]), False) > 0:
```
修改为：
```
if cv2.pointPolygonTest(cont, (int(test_pt[0]), int(test_pt[1])), False) > 0:
```
4.detection.py文件中第67行
```
return cv2.pointPolygonTest(cont, (x, y), False) > 0
```
修改为：
```
return cv2.pointPolygonTest(cont, (int(x), int(y)), False) > 0
```
5.detection.py文件中314至316行：
```
if len(conts) > 1:
    conts.sort(key=lambda x: cv2.contourArea(x), reverse=True)
elif not conts:
```
修改为：
```
if len(conts) > 1:
    conts = list(conts)
    conts.sort(key=lambda x: cv2.contourArea(x), reverse=True)
    conts = tuple(conts)
elif not conts:
```
6.因numpy版本兼容性问题，需根据情况将misc.py中第45行
```
canvas = canvas[1:h + 1, 1:w + 1].astype(np.bool)
```
修改为
```
canvas = canvas[1:h + 1, 1:w + 1].astype(np.bool_)
```

**步骤 2**  按照模型转换获取om模型，放置在 TextSnake/model 路径下。若未从 pytorch 模型自行转换模型，使用的是上述链接提供的 onnx 模型，则无需修改相关文件，否则修改 main.py 中pipeline的相关配置，将 mxpi_tensorinfer0 插件 modelPath 属性值中的 om 模型名改成实际使用的 om 模型名。

**步骤 3**  在命令行输入 如下命令运行整个工程

```
python3 main.py
```
注意：运行过程中可能会出现告警，不影响执行结果

**步骤 4** 图片检测。运行结束输出result.jpg。


## 5  精度验证

**步骤 1** 安装数据集用以测试精度。数据集 TotalText和GroundTruth文件 需要自行下载:[下载地址](https://drive.google.com/file/d/1bC68CzsSVTusZVvOkk7imSZSbgD1MqK2/view?usp=sharing),
groundTruth的[下载地址](https://drive.google.com/file/d/19quCaJGePvTc3yPZ7MAGNijjKfy77-ke/view?usp=sharing)。

将下载好的数据集和groundTruth文件调整成以下路径的形式(需手动创建相关文件夹)
测试图片位于total-text/Images/Test
Groundtruth位于Groundtruth/Polygon/Test
拷贝两个目录下的所有文件至对应目录
```
├── main.py  //运行工程项目的主函数
├── evaluate.py   //精度计算
├── t.pipeline      //pipeline
├── model   //存放模型文件
├── test.jpg          //测试图像
├── result.jpg          //输出结果
├── sdk.png          //流程图
├── pipeline.png          //pipeline流程图
├── data
    ├── total-text
        ├── gt
            ├── Test
                ├── poly_gt_img1.mat //测试集groundtruth
                ...
        ├── img1.jpg     //测试集图片
        ...              
└──README.md           
```

**步骤 2** 除先前下载的util文件夹之外，还需要从以下网址中下载Deteval.py与polygon_wrapper.py文件，放入util文件夹中。
https://github.com/princewang1994/TextSnake.pytorch/tree/b4ee996d5a4d214ed825350d6b307dd1c31faa07/dataset/total_text/Evaluation_Protocol/Python_scripts

**步骤 3**  在命令行输入 如下命令运行精度测试
```
python3 evaluate.py
```
注意：运行过程中会出现告警，不影响执行结果
得到精度测试的结果：

![精度测试结果1](./精度1.png)

![精度测试结果2](./精度2.png)

与pytorch实现版本的精度结果相对比，其精度相差在1%以下，精度达标。

## 6 常见问题
本案例中的TextSnake模型适用于图像中弯曲形状文字的检测。
本模型在以下几种情况下检测弯曲形状文字的效果良好：含有目标数量少、目标面积占比图像较大、各目标边界清晰。
在以下情况检测弯曲形状文字效果不太好：图片中的弯曲形状文字数目较多且大小较小，此时会出现缺漏的情况。