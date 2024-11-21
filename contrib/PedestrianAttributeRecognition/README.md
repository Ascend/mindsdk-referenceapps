# MindX SDK-行人属性检测

## 1 介绍
### 1.1 简介
本开发样例是基于MindX SDK开发的端到端的Python应用实例，可在昇腾芯片上进行行人属性识别，并把可视化结果保存到本地。开发端到端行人属性识别，实现对检测图片中行人的定位与属性识别，并达到精度要求。该Sample的主要处理流程为：数据输入>预处理>行人检测>抠图缩放>行人属性识别>结果可视化。

本样例适用于常见行人所处场景，如街道、红路灯路口、商场等，对于所推理的图片中的行人对象要求尽可能的完整、清晰、无遮挡、无重叠等。
### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro。

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称    | 版本   |
| ----------- | ------ |
| pillow      | 8.0.1  |
| pickle5     | 0.0.11 |

### 1.5 代码目录结构说明

本sample工程名称为yolov3_deepmar，工程目录如下图所示：
```
.
├── dataset
│   ├── test_image
├── model
│   ├── deepmar
│       ├── deepmar_bs1_aipp_1.om
│       ├── deepmar_bs1_unaipp.om
│       ├── aipp_deepmar.config
│       ├── Deepmar_bs1.onnx
│   ├── yolov3
│       ├── coco.names
│       ├── yolov3_tf_bs1_fp16.cfg
│       ├── yolov3_tf_bs_fp16.om
│       ├── yolov3_tf.pb
│       ├── aipp_yolov3_416_416.aippconfig
├── pipeline
│   ├── test.pipeline
│   ├── test_only_deepmar.pipeline
├── License
├── main.py
└── README.md
```

### 1.6 软件方案介绍

基于MindX SDK的行人属性识别业务流程：待检测图片通过appsrc插件输入，然后使用图像解码插件mxpi_imagedecoder对图片进行解码，再通过图像缩放插件mxpi_imageresize将图像缩放至满足行人检测模型(yolov3)要求的输入图像大小要求，缩放后的图像输入模型推理插件mxpi_tensorinfer中进行推理，随后将数据送入后处理插件mxpi_objectpostprocessor中进行处理，将得到的结果经过分发插件mxpi_distributor输出，随后将数据输出到裁剪插件mxpi_imagecrop中，根据上游推理插件推理出的结果进行裁剪出行人，并将裁剪后的图像输入到Deepmar的模型推理插件中，进行行人属性推理，最后将行人属性推理插件经序列化插件mxpi_dataserialize输出，即得到属性的预测结果，并将结果进行标签化，即为该图片的属性推理结果。

表1.1 系统方案各子系统功能描述：

| 序号 | 子系统             | 功能描述                                                     |
| ---- | ------------------ | ------------------------------------------------------------ |
| 1    | 图片输入           | 获取jpg格式的输入图片                                        |
| 2    | 图片解码           | 解码图片                                                     |
| 3    | 图片缩放           | 将输入图片缩放到模型指定输入的尺寸大小                       |
| 4    | 行人检测           | 将输入的张量送入Yolov3模型推理插件中进行推理，得到行人检测框 |
| 5    | Yolov3模型后处理   | 对Yolov3推理插件的输出结果进行处理                           |
| 6    | Yolov3检测结果分发 | 对检测到的person类进行分发                                   |
| 7    | 图像裁剪           | 对Yolov3检测出的行人进行裁剪                                 |
| 8    | 行人属性检测       | 将裁剪后的图像数据送入Deepmar推理插件中进行属性推理          |
| 9    | 结果序列化         | 将35个属性推理结果序列化输出                                 |

## 2 设置环境变量
```bash
#设置CANN环境变量，ascend-toolkit-path为cann安装路径
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```

## 3 准备模型

**步骤1:** 模型获取：本项目中用到的模型有：yolov3，deeomar两个模型。模型下载链接为：[链接](https://mindx.sdk.obs.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/PedestrianAttributeRecognition/model.zip)

**步骤2:** yolo模型转换：将yolov3的pb文件下载到本地，并将其放在“/model/yolov3”路径下，在终端移至该路径下，执行下面命令：

```bash
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input/input_data:1,416,416,3" --out_nodes="conv_lbbox/BiasAdd:0;conv_mbbox/BiasAdd:0;conv_sbbox/BiasAdd:0"
```

**步骤3:** deepmar模型转换：deepmar模型，对于无aipp设置的离线模型的转换，只需将atc转换时的 --insert_op_conf参数删除即可。

对于deepmar离线模型的aipp的设置，如下:

```bash
aipp_op{
    aipp_mode:static
    input_format : YUV420SP_U8

    src_image_size_w : 224
    src_image_size_h : 224

    crop: false
    load_start_pos_h : 0
    load_start_pos_w : 0
    crop_size_w : 224
    crop_size_h: 224

    csc_switch : true
    rbuv_swap_switch : false

    mean_chn_0 : 123
    mean_chn_1 : 116
    mean_chn_2 : 103
    min_chn_0 : 0.675
    min_chn_1 : 0.28
    min_chn_2 : 0.53
    var_reci_chn_0: 0.0171
    var_reci_chn_1: 0.0175
    var_reci_chn_2: 0.0174

    matrix_r0c0: 256
    matrix_r0c1: 0
    matrix_r0c2: 359
    matrix_r1c0: 256
    matrix_r1c1: -88
    matrix_r1c2: -183
    matrix_r2c0: 256
    matrix_r2c1: 454
    matrix_r2c2: 0
    input_bias_0: 16
    input_bias_1: 128
    input_bias_2: 128}
```
将Deepmar_bs1.onnx文件拷贝到本样例的“model/deepmar”路径下，并在终端中移至该路径下，执行下面命令进行将onnx模型转om模型：

```bash
atc --model=./Deepmar_bs1.onnx --framework=5 --output=./deepmar_bs1_aipp_1 --input_format=NCHW --input_shape="actual_input_1:1,3,224,224" --enable_small_channel=1 --log=error --soc_version=Ascend310P3  --insert_op_conf=aipp_deepmar.config
```
对于无aipp设置的离线模型，可执行下面命令得到：

```bash
atc --model=./Deepmar_bs1.onnx --framework=5 --output=./deepmar_bs1_unaipp --input_format=NCHW --input_shape="actual_input_1:1,3,224,224" --enable_small_channel=1 --log=error --soc_version=Ascend310P3
```

**步骤4:** 查看结果：执行完模型转换后，若提示如下信息说明模型转换成功。

```
ATC run success, welcome to the next use.
```

## 4 运行

**步骤1:** 参照第3章节中的模型转换步骤，将yolov3的离线模型转换成功。

**步骤2:** 参照第3章节中的模型转换步骤，将deepmar的离线模型转换成功。

**步骤3:** 将需要进行推理的行人图片放入/dataset/test_image文件夹下，并修改main.py脚本中第92行中的“img_path"为需要推理的图片路径，将test.pipeline中的第40行中"SDK安装路径"修改为SDK真实安装路径。

**步骤4:** 执行命令：python main.py,得到final_result.jpg可视化结果。


## 5 常见问题

* 测试样例的像素大小要做在32\*32～8192\*8192之间(其中不包含32*32的像素，图片像素大小必须大于32\*32)，且里边的行人对象像素的高度需在[6,4096]之间，宽度需在[32,4096]之间。
* 转换模型时，soc_version的值需要通过npu-smi info命令查看得到，否则可能会导致模型转换失败。
