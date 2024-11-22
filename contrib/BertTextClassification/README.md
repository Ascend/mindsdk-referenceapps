# 文本分类

## 1. 介绍

### 1.1 简介

文本分类插件基于 MindXSDK 开发，在昇腾芯片上进行文本分类，将分类结果保存。输入一段新闻，可以判断该新闻属于哪个类别。
该模型支持5个新闻类别：体育、健康、军事、教育、汽车。

### 1.2 支持的产品

本项目以昇腾Atlas 300I pro、 Atlas300V pro为主要的硬件平台。

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称 | 版本   |
| -------- | ------ |
|numpy|1.24.0|


### 1.5 代码目录结构与说明

本工程名称为文本分类，工程目录如下图所示：  

```
├── README.md
├── mxBase
│   ├── BertClassification
│   │   ├── BertClassification.cpp
│   │   └── BertClassification.h
│   ├── build.sh
│   ├── CMakeLists.txt
│   ├── data
│   │   └── vocab.txt
│   ├── main.cpp
│   ├── model
│   │   ├── bert_text_classification_labels.names
│   ├── mxBase_text_classification
│   ├── out
│   │   └── prediction_label.txt
│   └── test
│       ├── Test.cpp
│       └── Test.h
└── sdk
    ├── config
    │   ├── bert_text_classification_aipp_tf.cfg
    │   └── bert_text_classification_labels.names
    ├── data
    │   └── vocab.txt
    ├── main.py
    ├── model
    │   └── model_conversion.sh
    ├── out
    │   └── prediction_label.txt
    ├── pipeline
    │   └── BertTextClassification.pipeline
    ├── test
    │   ├── test.py
    └── tokenizer.py
```


## 2. 设置环境变量


在编译运行项目前，需要设置环境变量：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```

## 3. 准备模型

**步骤1** 

下载模型的pb文件 [模型下载地址](https://mindx.sdk.obs.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/BertTextClassification/bert_text_classification.pb)
将模型文件存放到当前项目根目录`./BertTextClassification`。

**步骤2** 进入模型所在文件夹使用atc命令进行模型转换：

```bash
atc --model=bert_text_classification.pb --framework=3 --input_format="ND" --output=bert_text_classification --input_shape="input_1:1,300;input_2:1,300" --out_nodes=dense_1/Softmax:0 --soc_version=Ascend310P3 --op_select_implmode="high_precision"
```

执行完模型转换脚本后，会生成相应的.om模型文件。 执行后终端输出为：

```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

**步骤3** 执行以下命令将转换好的om模型复制到项目中model文件夹中：

```
cp ./bert_text_classification.om ./sdk/model/
cp ./bert_text_classification.om ./mxBase/model/
```

## 4. 编译与运行

**步骤1** 

下载测试数据并解压，[下载地址](https://mindx.sdk.obs.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/BertTextClassification/data.zip)
将解压后的sample.txt和test.csv文件放在项目的mxBase/data和sdk/data目录下。

**步骤2** 

将本项目代码/BertTextClassification/sdk/pipeline目录下BertTextClassification.pipeline文件中的第26行的文件路径中出现的 ${SDK目录} 替换成mxVision SDK的安装目录，下面是需要替换的代码片段。
```
"postProcessLibPath": "${SDK目录}/lib/modelpostprocessors/libresnet50postprocess.so"
```

**步骤3** 运行pipeline项目，进入/BertTextClassification/sdk目录，执行以下命令：

```
python3 main.py
```

命令执行成功后在屏幕打印输出分类结果，同时在/BertTextClassification/sdk/out目录下生成分类结果文件 prediction_label.txt。

**步骤4** 运行C++项目，进入/BertTextClassification/mxBase目录，执行以下命令进行编译。

```
bash build.sh
```
编译完成后，执行以下命令运行
```
./mxBase_text_classification ./data/sample.txt
```
命令执行成功后在屏幕打印输出分类结果，同时在/BertTextClassification/mxBase/out目录下生成分类结果文件 prediction_label.txt。


## 5. 精度测试

**步骤1** 将第4节中下载的数据集中的test.csv文件分别放在sdk/data目录和mxBase/data目录。

**步骤2** pipeline项目中的精度测试文件为sdk/test目录下的test.py，将test.py移到sdk目录后，再执行下面的命令。

```
python3 test.py
```
执行后在屏幕输出类似如下精确度结果表示运行成功：
```
time cost: 0.0195 s
体育类的精确度：1.0000
健康类的精确度：0.9697
军事类的精确度：1.0000
教育类的精确度：0.9697
汽车类的精确度：0.9596
全部类别的精确度：0.9798
```

**步骤3** mxBase项目中，将mxBase目录下main.cpp中main方法里Test::test_accuracy();的注释去掉，然后将test1注释。修改后的代码片段如下：

```
int main(int argc, char* argv[]) {
  //test1(argc,argv);
  Test::test_accuracy();
}
```
重新编译，再./mxBase目录执行以下命令
```
bash build.sh
```
编译完成后，执行以下命令运行
```
./mxBase_text_classification
```
执行后在屏幕输出类似如下精确度结果表示运行成功：
```
体育类的精确度为：1
健康类的精确度为：0.969697
军事类的精确度为：1
教育类的精确度为：0.969697
汽车类的精确度为：0.959596
全部类的精确度为：0.979798
```
