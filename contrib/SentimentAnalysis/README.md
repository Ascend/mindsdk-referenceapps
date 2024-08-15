# 情感极性分类

## 1. 介绍

本项目是一个面向酒店服务领域的句子级情感极性分类系统。分类插件基于 MindXSDK 开发，在晟腾芯片上进行句子情感极性分类，将分类结果保存。输入一段句子，可以判断该句子属于哪个情感极性。
该模型支持3个类别：消极，积极，中性。

### 1.1 支持的产品

本项目以昇腾Atlas 500 A2/Atlas 200I DK A2为主要的硬件平台。

### 1.2 支持的版本

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 5.0.0 | 7.0.0   |  23.0.0  |
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  |


### 1.3 软件方案介绍

基于MindX SDK的句子情感分类分类业务流程为：待分类文本通过预处理，将文本根据字典vocab.txt进行编码，组成numpy形式的向量，将向量通过 appsrc 插件输入，然后由模型推理插件mxpi_tensorinfer得到每种类别的得分，再通过后处理插件mxpi_classpostprocessor将模型输出的结果处理，最后得到该文本的类别。本系统的各模块及功能描述如表1所示：


表1.1 系统方案各子系统功能描述：

| 序号 | 子系统 | 功能描述     |
| ---- | ------ | ------------ |
| 1    | 文本输入    | 读取输入文本 |
| 2    | 文本编码    | 根据字典对输入文本编码 |
| 3    | 模型推理    | 对文本编码后的张量进行推理 |
| 5    | 后处理      | 从模型推理结果中寻找对应的分类标签 |
| 7    | 保存结果    | 将分类结果保存文件|

### 1.4 代码目录结构与说明

本工程名称为句子情感分类，工程目录如下图所示（tokenizer.py引用于https://gitee.com/ascend/samples/blob/master/python/level2_simple_inference/5_nlp/bert_text_classification/src/tokenizer.py）：

```
.
│  build.sh
│  README.md
│  tree.txt
│  
├─mxBase
│  │  build.sh
│  │  CMakeLists.txt
│  │  main.cpp
│  │  
│  ├─SentimentAnalysis
│  │      SentimentAnalysis.cpp
│  │      SentimentAnalysis.h
│  │      
│  ├─data
│  │      vocab.txt
│  │      
│  ├─model
│  │      sentiment_analysis_label.names
│  │ 
│  ├─out
│  │      prediction_label.txt
│  │      
│  └─test
│          Test.cpp
│          Test.h
│          
└─sdk
    │  build.sh
    │  flowChart.jpg
    │  main.py
    │  run.sh
    │  tokenizer.py
    │  
    ├─config
    │      sentiment_analysis_aipp_tf.cfg
    │      sentiment_analysis_label.names
    │      
    ├─data
    │      vocab.txt
    |
    ├─model
    │      model_conversion.sh
    │      
    ├─out
    │      prediction_label.txt
    │      
    ├─pipeline
    │      sentiment_analysis.pipeline
    │      
    └─test
            test.py
            test.sh
            test_input.py
```
### 1.5 技术实现流程图

![image](sdk/flowChart.jpg)

## 2 环境依赖
确保环境中正确安装mxVision SDK。

在编译运行项目前，需要设置环境变量：

```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh  #sdk安装路径，根据实际安装路径修改
```

## 3 模型获取及转换

> 若使用A200I DK A2运行，推荐使用PC转换模型，具体方法可参考A200I DK A2资料

**步骤1**  
本项目使用的h5和pb模型已打包至[model.zip](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/SentimentAnalysis/model.zip) ，下载后解压获得。
也可以参考[源码](https://github.com/percent4/keras_bert_text_classification)，按照其README.md准备好自己的分类的数据完成模型的训练。分类数据可以参考[coarse](https://gitee.com/ascend/samples/tree/master/python/contrib/SentimentAnalysis/data/coarse-big-corpus/coarse)，需转成csv格式。
本项目使用的数据为[data.zip](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/SentimentAnalysis/data.zip) 解压后data目录下的train.csv。
h5模型转pb可以参考[源码](https://github.com/amir-abdi/keras_to_tensorflow) ，将自己训练好的h5模型转成pb模型。

**步骤2** 将得到的pb文件，存放到开发环境普通用户下的任意目录，例如：$HOME/models/sentiment_analysis。

**步骤3** 执行以下命令使用atc命令进行模型转换：

```bash
# 进入模型文件所在目录
cd $HOME/models/sentiment_analysis
# 执行模型转换命令
atc --model=./sentiment_analysis.pb --framework=3 --input_format=ND --output=./sentiment_analysis --input_shape="Input-Token:1,500;Input-Segment:1,500" --out_nodes="dense_1/Softmax:0" --soc_version=Ascend310B1 --op_select_implmode="high_precision"
```

执行成功后终端输出为：

```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

**步骤4** 执行以下命令将转换好的模型复制到项目中的model文件夹中：
``` bash
cp ./sentiment_analysis.om /SentimentAnalysis/sdk/model/
cp ./sentiment_analysis.om /SentimentAnalysis/mxbase/model/
```
## 4 编译与运行

**步骤1** 从https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/SentimentAnalysis/data.zip 下载测试数据并解压，解压后的sample.txt和test.csv文件放在项目的/SentimentAnalysis/mxBase/data和/SentimentAnalysis/sdk/data目录下。

**步骤2** 按照第 2 小节 环境依赖 中的步骤设置环境变量。

**步骤3** 按照第 3 小节 模型获取及转换 中的步骤获得 om 模型文件。

**步骤4** pipeline项目运行在sdk目录下执行命令：

```
python3 main.py
```

命令执行成功后在out目录下生成分类结果文件 prediction_label.txt，查看结果文件验证分类结果。

**步骤5** mxBase项目在mxBase目录中，执行以下命令进行编译运行。

```bash
bash build.sh
./mxBase_sentiment_analysis ./data/sample.txt
```

执行成功后在服务器的mxBase/out目录下生成分类结果文件 prediction_label.txt，查看结果文件验证分类结果。

## 5 精度测试

**步骤1** 按照第 4 小节 编译与运行 的步骤将样例运行成功。

**步骤2** 从网址 https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/SentimentAnalysis/data.zip  下载后解压，将解压后的test.csv文件分别放在sdk/data目录和mxBase/data目录。

**步骤3** pipeline项目中的精度测试文件为sdk/test目录下的test.py，将test.py移到sdk目录下，执行下面代码，得到pipeline的精度测试结果。

```
python3 test.py
```

**步骤4** mxBase项目中，将mxBase目录下main.cpp中main函数替换为以下的代码，然后执行编译脚本，再次运行可得到mxBase的精度测试结果，具体执行命令如下。
替换代码：
```
int main(int argc, char* argv[]) {
    Test::test_accuracy();
}
```
编译运行命令
```bash
bash build.sh
./mxBase_sentiment_analysis
```

## 6 其他问题

1.本项目的设计限制输入样例为文本文件，其他文件如图片、音频不能进行推理。

2.本项目的模型对中性数据进行分类时预测结果较差，可能有以下几个方面，一是对中性数据的分类本身有一定的难度；二是在训练模型时提供数据集中的中性数据较少，模型对于中性数据的分类效果并不好；三是在模型转换的过程中可能会存在精度的缺失。

3.若使用者是采用的先将代码下载至本地，再上传至服务器的步骤运行代码，词表文件data/vocab.txt可能会编码异常，造成mxbase代码读取词表有误，精度下降的问题；建议使用者直接下载项目文件至服务器运行，避免该问题。
