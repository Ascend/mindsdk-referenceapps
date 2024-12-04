# 模型推理工具

## 1 介绍

### 1.1 简介
基于MindX SDK实现开发模型推理工具，本例为msame的python版本实现，适用于单输入或多输入的om模型推理。[msame-C++工具链接](https://gitee.com/ascend/tools/tree/master/msame)

技术实现流程图如下：

![image-20220401173124980](./img/process.png)

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 依赖软件 | 版本   | 说明                   |
| -------- | ------ | ---------------------- |
| numpy    | 1.24.0 | 将数据保存为二进制文件 |

### 1.5 代码目录结构与说明

```
.
├── img
│   ├── error1.jpg                            // msame-C++推理结果
│   │── error2.jpg                            // 本例(msame-python)推理结果
│   │── process.jpg                           // 流程图
├── test
│   ├── gen_input_data.py                     // 生成单输入、多输入测试数据脚本
│   ├── yolox_bgr.cfg                         // YOLOX相关配置，配合YOLOX测试模型使用
├── msame.py                                  // 模型推理工具代码
└── README.md
```

## 2 设置环境变量

```
. /usr/local/Ascend/ascend-toolkit/set_env.sh   # toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/set_env.sh                # SDK_INSTALL_PATH: mxVision SDK 安装路径
```

## 3 准备模型

本项目为通用工具，示例中采用的模型分别为单输入模型和多输入模型，实际执行选择其中一项即可，下面依次介绍：

- 单输入模型——YOLOX模型。

**步骤1：** 下载 onnx 模型 yolox_nano.onnx 至 `test` 文件夹下。[模型下载链接](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/YOLOX/yolox_nano.onnx) 。本项目使用模型转换工具 ATC 将 onnx 模型转换为 om 模型。

**步骤2：** 将该模型转换为om模型，具体操作为先进入 `test` 文件夹下, 然后执行atc指令如下：

```
atc --model=yolox_nano.onnx --framework=5 --output=./yolox_pre_post --output_type=FP32 --soc_version=Ascend310P3 --input_shape="images:1, 3, 416, 416" --insert_op_conf=./yolox_bgr.cfg
```

若终端输出：
```
ATC start working now, please wait for a moment.

ATC run success, welcome to the next use.
```

表示命令执行成功。

- 多输入模型——BertTextClassification模型

**步骤1：** 下载模型的pb文件 [模型下载地址](https://mindx.sdk.obs.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/BertTextClassification/bert_text_classification.pb)

**步骤2：** 将模型文件存放到当前项目的 `test` 文件夹下，使用atc命令进行模型转换：

```bash
atc --model=bert_text_classification.pb --framework=3 --input_format="ND" --output=bert_text_classification --input_shape="input_1:1,300;input_2:1,300" --out_nodes=dense_1/Softmax:0 --soc_version=Ascend310P3 --op_select_implmode="high_precision"
```

若终端输出：
```bash
ATC start working now, please wait for a moment.

ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4 运行

示例步骤如下：

**步骤1：** 准备模型输入的测试数据。在 `test` 文件夹中执行命令 `python3 gen_input_data.py`，生成所需输入测试数据。

**步骤2：** 执行模型推理。根据准备的模型类型，在项目**根目录**选择 “模型不加input输入”、“单输入模型”、“多输入模型” 中对应的执行命令，：

```
python3.9 msame.py --model xxx --input xxx --output xxx  --loop xxx --outfmt xxx
```
在输出路径下成功输出预期的“.txt”或“.bin”则运行成功，否则报错。   
参数说明：
```
--input   
功能说明：模型的输入路径 参数值：bin或npy文件路径与文件名 示例：--input dog.npy
注：多输入样例在输入时，多个输入用","隔开，且不能有空格
--output   
功能说明：模型的输出路径 参数值：bin或txt文件路径 示例：--output .
--model   
功能说明：om模型的路径 参数值：模型路径与模型名称 示例：--model yolov3.om
--outfmt    
功能说明：模型的输出格式 参数值：TXT 或 BIN 示例：--outfmt TXT
--loop   
功能说明：执行推理的次数 默认为1 参数值：正整数 示例：--loop 2
--device   
功能说明：执行代码的设备编号 参数值：自然数 示例：--device 1 
```

- 模型不加input输入：

```
python3 msame.py --model ./test/yolox_pre_post.om --output test --outfmt BIN
```

- 单输入模型：

以yolox模型作为示例参考：

```
python3 msame.py --model ./test/yolox_pre_post.om --input test/test1.npy --output test --outfmt TXT
```

- 多输入模型：

以bert_text_classification模型作为示例参考：

```
python3 msame.py --model ./test/bert_text_classification.om --input test/test2.npy,test/test2.npy --output test --outfmt TXT --loop 2
```

**步骤3：**  查看结果。执行成功后，在test目录下生成 `.txt` 或 `.bin` 输出文件，文件类型取决于命令中的 `--outfmt`参数配置    

## 5 常见问题
### 5.1 存储为txt格式时可能会出现第六位开始的误差

**问题描述：**

与msame-C++对比，存储为txt格式时可能会出现第六位开始的误差，见下图

 执行msame-C++输出结果：   
![image-20220401173124980](./img/error1.png)
 执行本例（msame-python）输出结果：   
![image-20220401173124980](./img/error2.png)

**解决方案：**

可以忽略此问题。

### 5.2 模型需要的输入与提供的数据不一致

**问题描述：**

模型需要的输入shape、dtype与提供的数据shape、dtype不一致。 
```
Error : Please check the input shape and input dtype
或者
InputTensor Data Type mismatches.
```

**解决方案：**

可在 msame.py 第218行 `t_save` 函数中新增如下代码，自行打印输出，查看模型需要的输入shape和dtype。

```
print(m.input_shape(0))
print(m.input_dtype(0))
```

自行编写脚本查看输入测试数据的bin或npy文件shape和dtype，与模型的shape和dtype对齐。
