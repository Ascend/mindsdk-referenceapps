# 基于MxBase接口的OCR字符识别

## 1 介绍
### 1.1 简介


开发样例是基于mxBase开发的OCR应用，实现识别输入图片中的文字功能。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro。

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：

| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- |---------| -------------- |
| 6.0.RC3   | 8.0.RC3 |  24.1.RC3  |

### 1.4 三方依赖

第三方依赖软件和版本如下表。请确认环境已安装pip3后，使用`pip3 install * `安装以下依赖：

|软件名称    | 版本        |
|-----------|-----------|
| numpy     | 1.24.0    |
| paddle2onnx     | 1.2.4    |
| paddlepaddle     | 2.6.0    |
| tqdm | 4.66.5 |
| shapely | 2.0.6 |
| joblib | 1.4.2 |

### 1.5 代码目录结构说明
本工程名称为OpticalCharacterRecognition，工程目录如下图所示：

```
.
├── src
│   └── main.cpp          // OCR主函数
│   └── build.sh
│   └── CMakeLists.txt
│   └── AscendBase
│       ├── Base
│       │   ├── ArgumentParser          // 命令行参数解析模块
│       │   ├── BlockingQueue           // 阻塞队列模块
│       │   ├── ConfigParser            // 配置文件解析模块
│       │   ├── Framework               // 流水并行框架模块
│       │   │   ├── ModuleManagers      // 业务流管理模块
│       │   │   ├── ModuleProcessors    // 功能处理模块
│       │   │   │   ├── CharacterRecognitionPost       // 字符识别后处理模块
│       │   │   │   ├── CommonData       // 各功能模块间共用的数据结构
│       │   │   │   ├── Processors       // 各功能处理模块
│       │   │   │   │   ├── HandOutProcess       // 图片分发模块
│       │   │   │   │   ├── DbnetPreProcess      // Dbnet前处理模块
│       │   │   │   │   ├── DbnetInferProcess    // Dbnet推理模块
│       │   │   │   │   ├── DbnetPostProcess     // Dbnet后处理模块
│       │   │   │   │   ├── ClsPreProcess        // Cls前处理模块
│       │   │   │   │   ├── ClsInferProcess      // Cls推理模块
│       │   │   │   │   ├── ClsPostProcess       // Cls后处理模块
│       │   │   │   │   ├── CrnnPreProcess       // Crnn前处理模块
│       │   │   │   │   ├── CrnnInferProcess     // Crnn推理模块
│       │   │   │   │   ├── CrnnPostProcess      // Crnn后处理模块
│       │   │   │   │   ├── CollectProcess       // 推理结果保存模块
│       │   │   │   ├── Signal       // 程序终止信号处理模块
│       │   │   │   ├── TextDetectionPost       // 文本检测后处理模块
│       │   │   │   │   ├── clipper.cpp
│       │   │   │   │   ├── clipper.hpp
│       │   │   │   │   ├── TextDetectionPost.cpp
│       │   │   │   │   ├── TextDetectionPost.h
│       │   │   │   ├── Utils       // 工具函数模块
│   └── Common
│       ├── EvalScript
│       │   ├── eval_script.py       // 精度测试脚本
│       │   └── requirements.txt     // 精度测试脚本的python三方库依赖文件
│       ├── InsertArgmax
│       │   ├── insert_argmax.py     // ArgMax算子插入模型脚本
│       │   └── requirements.txt     // ArgMax算子插入模型脚本的python三方库依赖文件
│       ├── LabelTrans                     // 数据集标签转换脚本
│   └── data
│       ├── config
│       │   ├── setup.config       // 配置文件
│       ├── models
│       │   ├── cls
│       │   ├── crnn
│       │   ├── dbnet
├── README.md
```
**注意**：代码目录中的`src/AscendBase/Base/Framework/ModuleProcessors/TextDetectionPost/`下的`clipper.cpp`、`clipper.hpp`为开源第三方模块，需用户自行下载这两个文件，然后放在对应位置。

- clipper.cpp、clipper.hpp文件[下载链接](https://sourceforge.net/projects/polyclipping/files/clipper_ver6.4.2.zip/download)， 在文件夹`cpp`下可以找到。

### 1.6 相关约束

本样例是面向直排文本，不考虑弯曲文本的情况，仅支持JPEG作为输入图像格式。


## 2 设置环境变量

```bash
#设置CANN环境变量
. ${ascend-toolkit-path}/set_env.sh

#设置Vision SDK环境变量，SDK-path为Vision SDK 安装路径
. ${SDK-path}/set_env.sh
```

## 3 准备模型

**步骤1：** 下载模型

Paddle PP-OCR server 2.0模型（`.onnx`格式文件）:

| 名称      | 下载链接 |
| --------------- | -------------- |
| Paddle PP-OCR server 2.0 DBNet   | [ch_ppocr_server_v2.0_det_infer.onnx](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/mxVision/OpticalCharacterRecognition/ch_ppocr_server_v2.0_det_infer.onnx) |
| Paddle PP-OCR server 2.0 Cls  | [ch_ppocr_mobile_v2.0_cls_infer.onnx](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/mxVision/OpticalCharacterRecognition/ch_ppocr_mobile_v2.0_cls_infer.onnx) |
| Paddle PP-OCR server 2.0 CRNN | [ch_ppocr_server_v2.0_rec_infer_argmax.onnx](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/mxVision/OpticalCharacterRecognition/ch_ppocr_server_v2.0_rec_infer_argmax.onnx) |


**步骤2：** 放置模型文件

将下载的文件放置在路径`OpticalCharacterRecognition/src/data/models`下对应的文件夹内。

**步骤3：** 模型转换

在三个模型目录下分别执行对应的atc转换脚本：
```bash
bash atc.sh
```
执行完模型转换脚本后，若提示如下信息说明模型转换成功，并可以找到对应的`.om`模型文件。

```
ATC run success, welcome to the next use.
```  

**步骤4：** CRNN模型文件放置

在`OpticalCharacterRecognition/src/data/models/crnn`下可以看到5个`.om`模型文件，在该目录下执行以下命令将`.om`模型文件都移动到新建目录`OpticalCharacterRecognition/src/data/models/crnn/static`目录下：
```bash
mkdir static
mv crnn_dynamic_dims_16_bs1.om ./static
mv crnn_dynamic_dims_16_bs4.om ./static
mv crnn_dynamic_dims_16_bs8.om ./static
mv crnn_dynamic_dims_16_bs16.om ./static
mv crnn_dynamic_dims_16_bs32.om ./static
```

## 4 编译与运行

**步骤1：** 准备数据集

1. 准备识别模型字典文件:

- 可通过[下载地址](https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/release/2.5/ppocr/utils/ppocr_keys_v1.txt)直接下载文件；

- 或者通过以下指令下载：
```bash
wget -O ppocr_keys_v1.txt https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/release/2.5/ppocr/utils/ppocr_keys_v1.txt
```



2. 准备数据集ICDAR-2019 LSVT：

- 可通过下方表格的下载链接直接下载；

| 名称 | 下载链接 |
|---------|----------|
| 图片压缩包1 | (train_full_images_0.tar.gz)[https://dataset-bj.cdn.bcebos.com/lsvt/train_full_images_0.tar.gz]|
| 图片压缩包2 | (train_full_images_1.tar.gz)[https://dataset-bj.cdn.bcebos.com/lsvt/train_full_images_1.tar.gz]|
| 标注文件 | (train_full_labels.json)[https://dataset-bj.cdn.bcebos.com/lsvt/train_full_labels.json]|

- 或通过指令下载：
```bash
wget https://dataset-bj.cdn.bcebos.com/lsvt/train_full_images_0.tar.gz
wget https://dataset-bj.cdn.bcebos.com/lsvt/train_full_images_1.tar.gz
wget https://dataset-bj.cdn.bcebos.com/lsvt/train_full_labels.json
```

**步骤2：** 解压并放置数据集

1. 通过以下指令在当前位置创建数据集目录：
```bash
mkdir -p ./icdar2019/images
```
2. 在当前目录下解压图片并移动到对应目录：
```bash
tar -zvxf ./train_full_images_0.tar.gz  # 确认当前目录下有对应数据包
tar -zvxf ./train_full_images_1.tar.gz
mv train_full_images_0/* ./icdar2019/images
mv train_full_images_1/* ./icdar2019/images
rm -r train_full_images_0
rm -r train_full_images_1
```

**步骤3：** 标签格式转换

label标注文件格式转换为ICDAR2015格式, 执行的转换脚本为`OpticalCharacterRecognition/src/Common/LabelTrans/label_trans.py`。
参数`label_json_path`为上述“4 编译与运行”步骤1.2所下载的`train_full_labels.json`文件所在路径；
参数`output_path`为上述“4 编译与运行”步骤1.2所创建的数据集目录`icdar2019`所在路径。

执行命令：
```bash
python3 ./label_trans.py --label_json_path=/PATH/TO/train_full_labels.json --output_path=/PATH/TO/icdar2019/
```

**步骤4：** 修改配置文件

 修改配置文件`OpticalCharacterRecognition/src/data/config/setup.config`：
 1. 第5行修改推理使用的device的ID：
  ```bash
  deviceId = 0 // 进行推理的device的id
  ```
2. 第28行配置文本识别模型字符标签文件路径:（上述“4 编译与运行”步骤1.1所下载的模型字典文件）
  ```bash
  dictPath = /PATH/TO/ppocr_keys_v1.txt // 识别模型字典文件
  ```

**步骤5：** 编译项目

在目录`OpticalCharacterRecognition/src/`下执行：
  ```bash
  bash build.sh
  ```
编译完成后，在`OpticalCharacterRecognition/src/dist/`目录下会生成可执行文件`main`。

**步骤6：** 准备输入图片

需要使用的输入图片必须为JPEG格式，图片名格式严格按照前缀+下划线+数字的形式，如`xxx_xx.jpg`。
将需要输入的图片放在目录`/PATH/TO/icdar2019/images/`下。（上述“4 编译与运行”步骤1.2所创建的数据集目录`icdar2019/images/`）


**步骤7：** 运行程序

在目录`OpticalCharacterRecognition/src/`下执行如下命令，启动程序：

注意：参数`image_path`为上述“4 编译与运行”步骤1.2所创建的数据集目录`icdar2019/images/`所在路径。

```bash
./dist/main -image_path /PATH/TO/icdar2019/images/ -thread_num 1 -direction_classification false -config ./data/config/setup.config
```
运行可使用的参数说明：

| 参数名称 | 意义 | 
| --- | --- | 
| image_path | 输入图片所在的文件夹路径。 |
| thread_num | 运行程序的线程数，取值范围1-4，请根据环境内存设置合适值。 | 
| direction_classification | 是否在检测模型之后使用方向分类模型。True为开启使用，False为不使用。 | 
| config | 配置文件setup.config的完整路径。 | 

**步骤8：** 查看结果


根据屏幕日志确认是否执行成功。

- 结果位置：


识别结果默认存放在`OpticalCharacterRecognition/src/result`目录下。

**注意**：推理结果写文件是追加写的，如果推理结果保存路径中已经存在推理结果文件，推理前请手动删除推理结果文件，如果有需要，提前做好备份。

- 结果内容：

每个infer_img_x.txt（x 为图片id）中保存了每个图片文本框四个顶点的坐标位置以及文本内容，格式如下:
  ```bash
  1183,1826,1711,1837,1710,1887,1181,1876,签发机关/Authority
  2214,1608,2821,1625,2820,1676,2212,1659,有效期至/Dateofexpin
  1189,1590,1799,1606,1797,1656,1187,1641,签发日期/Dateofissue
  2238,1508,2805,1528,2802,1600,2235,1580,湖南/HUNAN
  2217,1377,2751,1388,2750,1437,2216,1426,签发地点/Placeofis
  ```
**注意**：如果输入图片中包含敏感信息，使用完后请按照当地法律法规要求自行处理，防止信息泄露。


## 5 精度验证

**步骤1：** 准备验证数据集

执行完“4 编译与运行”的“步骤2”后的`icdar2019/images`为测试所用的所有输入图片。

**步骤2：** 生成运行结果

按照上述的“4 编译与运行”完成所有输入图片的结果生成。

**步骤3：** 进行精度计算

在目录`OpticalCharacterRecognition/src/Common/EvalScript`下执行：

注意：参数`gt_path`为上述“4 编译与运行”步骤1.2所创建的数据集目录`icdar2019/labels`所在路径；参数`pred_path`为上述“4 编译与运行”步骤8结果存放位置所在路径。

```bash
python3 eval_script.py --gt_path=/PATH/TO/icdar2019/labels --pred_path=/PATH/TO/result
```
运行可使用的参数说明：

| 选项 | 意义 | 
| --- | --- | 
| --gt_path | 测试数据集标注文件路径。 | 
| --pred_path | Ocr Demo运行的推理结果存放路径。 |

**步骤4：** 查看精度结果

根据屏幕回显日志获取精度结果。

