# 文档版面分析

## 1 介绍
在本系统中，目的是基于MindX Vision，在昇腾平台上，开发端到端文档版面分析的参考设计，实现对图像中的文档识别的功能，并把可视化结果保存到本地。

样例输入：包含文档版面的jpg图片或者png图片。

样例输出：框出版面内容并标有版面类型与置信度的jpg或者png图片。

### 1.1 支持的硬件形态

支持昇腾500 A2 推理产品

### 1.2 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本 |
  | --------- | ------------------ | -------------- | 
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  | 
| 5.0.0     | 7.0.0     |  23.0.0    |



### 1.3 软件方案介绍

本方案中，通过将onnx格式的文档版面分析模型转成华为晟腾的om模型。将传入的图片做解码、resize、色域转换和归一化之后放入模型推理，推理结果再经过后处理和可视化之后，形成框出版面内容并标有版面类型与置信度的图片。


### 1.4 代码目录结构与说明

本工程名称为DocumentLayoutAnalysis，工程目录如下图所示：
```
├── evaluate.py             #精度测试
├── infer.py                #推理文件
├── model
│   ├── layout.aippconfig   #aipp配置文件，用于模型转换
├── postprocess.py          #后处理文件
├── README.md
└── utils.py                #推理用到的一些工具函数
```

### 1.5 技术实现流程图

![process](./image/process.png)

图1 文档版面分析流程图

### 1.6 适用场景

项目适用轮廓明显，且图片较清晰的文档测试图片

**注**：由于模型限制，仅支持识别['Text', 'Title', 'Figure', 'Figure caption', 'Table','Table caption', 'Header', 'Footer', 'Reference', 'Equation']列表里的 **10** 种版面类型。遇到深色背景色的文档，会识别成图片；遇到没有检测对象的空图会直接输出。

## 2 环境依赖
本项目除了依赖昇腾Driver、Firmware、CANN和MxVision及其要求的配套软件外，还需依赖以下组件：

| 软件名称 | 版本   |
| :--------: | :------: |
|numpy|1.21.5|
|opencv-python|4.5.5|

在编译运行项目前，需要设置环境变量：

- 环境变量介绍

```bash
# 执行环境变量脚本使环境变量生效
. ${ascent-tookit-path}/set_env.sh
. ${SDK-path}/set_env.sh
# SDK-path: SDK mxVision安装路径
# ascent-tookit-path: CANN安装路径

#查看环境变量
env
```

## 3 模型获取
### 3.1 下载模型相关文件
- **步骤1**  根据[**下载地址**](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/DocumentLayoutAnalysis/%E6%96%87%E6%A1%A3%E7%89%88%E9%9D%A2%E5%88%86%E6%9E%90%E6%A8%A1%E5%9E%8B%E5%A4%87%E4%BB%BD.zip)下载并解压得到picodet_lcnet_x1_0_fgd_layout_cdla_infer.onnx文件。

注：**下载后请将模型请放置于model的对应目录下**

### 3.2 onnx模型转换成om模型

**步骤1** cd 到工程目录model目录下
执行以下命令：

     atc --model=./picodet_lcnet_x1_0_fgd_layout_cdla_infer.onnx --framework=5 --output=./layout --soc_version=Ascend310B1 --insert_op_conf=./layout.aippconfig

注：1.执行成功后终端会输出相关信息提示模型转换成功。

2.模型转换使用了ATC工具，如需更多信息请参考:

https://gitee.com/ascend/docs-openmind/blob/master/guide/mindx/sdk/tutorials/%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99.md


## 4 编译与运行

示例步骤如下：

**步骤1** 自行选择一张或多张图片文件，放入工程目录`./input`下。

参考测试图片[**下载地址**](https://github.com/PaddlePaddle/PaddleDetection/blob/release/2.5/docs/images/layout.jpg)

注：**如果工程目录下没有input目录，需要自行建立**


**步骤2** cd 到该项目目录DocumentLayoutAnalysis下，然后执行
```bash
python infer.py
```

执行后会在终端按顺序输出文档的版面类别和置信度，并在`./output`目录下生成结果图片，可查看文档检测结果。

注：**如果工程目录下没有output目录，需要自行建立**



## 5 精度测试

**步骤1**获取数据集

数据集CDLA dataset:[**下载地址**](https://github.com/buptlihang/CDLA)

由于精度测试只需要用到验证集val，所以只需要保留数据集里的val文件。精度测试使用的标注json文件需要转成[coco格式](https://zhuanlan.zhihu.com/p/101984674)。
转换过程参考[转coco格式](https://github.com/buptlihang/CDLA#%E8%BD%ACcoco%E6%A0%BC%E5%BC%8F)。将转换后的val_save_path目录下的JEPGimages目录和annotations.json文件复制到工程目录val下。

注：**如果工程目录下没有val目录，需要自行建立**


**步骤2**运行精度测试python文件

cd 到该项目目录DocumentLayoutAnalysis下，然后执行
```bash
python evaluate.py
```
之后就得到精度测试的结果了,例如下图3所示：

![result](./image/result.png)

图2 文档版面识别精度测试结果
