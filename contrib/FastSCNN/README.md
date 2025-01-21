# FastSCNN语义分割参考设计

## 1 介绍
### 1.1 简介

   使用fastscnn模型，在Vision SDK环境下实现语义分割功能
   由用户设置测试图片，传入到pipeline中先后实现前处理，模型推理，后处理等功能，最终输出结果图片实现可视化

    Fast-SCNN 是一个面向实时的语义分割网络。 在双分支的结构基础上，大量使用了深度可分离卷积和逆残差模块，并且使用特征融合构造金字塔池化模块来融合上下文信息。
   
   软件方案介绍

   项目主要由主函数，测试集，模型，测试图片组成。
   主函数中构建业务流steam读取图片，通过pipeline在sdk环境下先后实现图像解码，图像缩放，模型推理的功能，
   最后从流中取出相应的输出数据进行涂色保存结果并测试精度。

   表1.1 系统方案中各模块功能：

   | 序号 | 模块          | 功能描述                                                     |
   | ---- | ------------- | ------------------------------------------------------------ |
   | 1    | appsrc        | 向Stream中发送数据，appsrc将数据发给下游元件                 |
   | 2    | imagedecoder  | 用于图像解码，当前只支持JPG/JPEG/BMP格式                     |
   | 3    | imageresize   | 对解码后的YUV格式的图像进行指定宽高的缩放，暂时只支持YUV格式的图像 |
   | 4    | tensorinfer   | 对输入的张量进行推理                                         |
   | 5    | dataserialize | 将stream结果组装成json字符串输出                             |
   | 6    | appsink       | 从stream中获取数据                                           |
   | 7    | color         | 通过分辨出的不同类别进行上色                                 |
   | 8    | evaluation    | 模型精度评估，输出Model MIoU和 Model MPA                     |

   技术实现流程图

   FastSCNN语义分割模型的后处理的输入是mxpi_tensor0推理结束后通过appsink0输出的tensor数据，尺寸为[1*19*1024*2048]，将张量数据通过pred取出推测的结果值，argmax函数确定每个像素点概率最大的类型。每一类的rgb数值存在于cityscapepallete数组中，查找每个像素点的类型进行上色，最后将像素点组成的图片保存成mask.png。

   实现流程图如下图所示：

   ![流程](./流程.png)

   ![pipeline](./pipeline.png)


### 1.2 支持的产品

本项目以昇腾Atlas300V pro、 Atlas300I pro为主要的硬件平台

### 1.3 支持的版本

本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：
| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

推荐系统为ubantu 18.04，环境依赖软件和版本如下表：

| 软件名称 | 版本   |
| -------- | ------ |
| cv2      | 4.5.3  |
| numpy    | 1.21.1 |

### 1.5 代码目录结构与说明

本工程名称为FastSCNN，工程目录如下图所示：

```
├── main.py  //运行工程项目的主函数
├── evaluate.py   //评测精度函数
├── label.py      //分类label函数
├── text.pipeline      //pipeline
├── model   //存放模型文件
|   ├──aipp_FastSCnn.aippconfig     //预处理配置文件
├── 流程.png          //流程图
├── pipeline.png          //pipeline流程图
└──README.md          
```


## 2 设置环境变量


在编译运行项目前，需要设置环境变量：
```
#设置CANN环境变量（请确认install_path路径是否正确）
. ${ascend-toolkit-path}/set_env.sh

#设置Vision SDK 环境变量，SDK-path为Vision SDK 安装路径
. ${SDK-path}/set_env.sh

#查看环境变量
env
```

## 3 准备模型

本项目使用的模型是FastSCNN模型，相关模型下载链接如下：
[models](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/FastScnn/models.zip)

1. 下载上述models压缩包，获取fast_scnn_bs1.onnx模型文件放置FastSCNN/model目录下。


2. 进入FastSCNN/model文件夹下执行命令：

   ```
   atc --framework=5 --model=fast_scnn_bs1.onnx --output=fast_scnn_bs1  --output_type=FP16 --input_format=NCHW --insert_op_conf=./aipp_FastSCnn.aippconfig --input_shape="image:1,3,1024,2048"  --log=debug --soc_version=Ascend310P1
   ```

3. 执行该命令会在当前目录下生成项目需要的模型文件fast_scnn_bs1.om。执行后终端输出为：

   ```
   ATC start working now, please wait for a moment.
   ATC run success, welcome to the next use.
   ```

   表示命令执行成功。

## 4 运行

**步骤 1**  将任意一张jpg格式的图片存到当前目录下(/FastSCNN)，命名为test.jpg。

**步骤 2**   按照模型转换获取om模型，放置在FastSCNN/models路径下。修改text.pipeline中的第32行，将 mxpi_tensorinfer0 插件 modelPath 属性值中的 om 模型名改成实际使用的 om 模型名；修改text.pipeline中的第23、24行, 将 mxpi_imageresize0 插件中的 resizeWidth 和 resizeHeight 属性改成转换模型过程中设置的模型输入尺寸值(原尺寸为2048*1024)。
```
   "props": {
              "dataSource": "mxpi_imageresize0",
              "modelPath": "../FastScnn_python/models/fast255.om"
          },
   "props": {
              "dataSource": "mxpi_imagedecoder0",
              "resizeHeight": "1024",
              "resizeWidth": "2048"
          },
```
**步骤 3**  在命令行输入 如下代码运行整个工程：

```
python3 main.py
```

**步骤 4** 图片检测。运行结束输出mask.png实现语义分割功能（通过不同颜色区分不同事物）。

## 5 测试精度：

**步骤 1** 安装数据集用以测试精度。数据集cityscapes需要下载到当前目录，下载路径为：https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/FastScnn/dataset.zip
将标注文件解压至FastSCNN/目录下。确保下载完数据集和标注文件后的目录结构为如下：

```
├── main.py  //运行工程项目的主函数
├── evaluate.py   //评测精度函数
├── label.py      //分类label函数
├── text.pipeline      //pipeline
├── model   //存放模型文件
|   ├──best_model.pth     //权重文件
|   ├──aipp_FastSCnn.aippconfig     //预处理配置文件
|   └──fast_scnn_bs1.om         //生成的om文件
├── 流程.png          //流程图
├── pipeline.png          //pipeline流程图
├──cityscapes             //数据集
|  ├── gtFine
|   |   ├──test
|   |   ├──train
|   |   └──val
|   |
|   └── leftImg8bit
|       ├──test
|       ├──train
|       └──val
└──README.md
```

**步骤 2** 进入数据集的某个文件夹作为测试集（此处以cityscapes/leftImg8bit/val/frankfurt/为例），进入frankfurt文件夹，需要用户将png格式转成jpg格式保存在当前目录下。

```
cd cityscapes/leftImg8bit/val/frankfurt/
```

**步骤 3** 进入标签集gtFine相应的文件夹下。在当前目录上传label.py并运行，用以挑选后缀为labelIds的文件。

```
cd ${用户路径}/FastSCNN/cityscapes/gtFine/val/frankfurt/
cp ${用户路径}/FastSCNN/label.py .
python3 label.py
```

**步骤 4** 运行结束会在当前目录下新生成四个文件夹，将labelIds.png命名的文件夹重命名为Label。这里可以重新点击一下文件排序，确保leftImg8bit的frankfurt中的文件和gtFine下frankfurt/label中的文件排序一致，一一对应。

**步骤 5** 回到工程目录下

```
cd ${用户路径}/FastSCNN
```
修改evaluate.py 91行、100行的代码
```
filepath = "./cityscapes/leftImg8bit/val/frankfurt/"



with open(image_path, 'rb') as f:
            label_path = "./cityscapes/gtFine/val/frankfurt/Label/" + filename.split('_')[0] + '_' + filename.split('_')[1] \
            + '_' + filename.split('_')[2] + "_gtFine_labelIds.png"
```

**步骤 6** 运行

运行结束会在显示屏输出测试精度（mIoU，PA）。
```
python3 evaluate.py
```

