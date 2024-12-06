# TSM视频分类参考设计

## 1、 介绍


### 1.1 简介

使用TSM模型，基于Kinetics-400数据集，在MindX SDK环境下实现视频分类功能。将测试视频传入脚本进行前处理，模型推理，后处理等功能，最终得到模型推理的精度。

本案例中的 TSM 模型适用于Kinetics数据集中的400类视频分类，并可以返回测试集视频的精度值。

在以下两种情况视频分类情况不太好：1. 视频长度过短（小于3s）。 2. 视频帧率过低。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |


### 1.4 三方依赖

|   软件名称    |    版本     |
| :-----------: | :---------: |
| numpy |  1.24.0  |
| torchvision |  0.20.1  |
| torch |  2.5.1  |
| Pillow |  11.0.0  |
| tqdm |  4.67.1  |


### 1.5 代码目录结构与说明

```text
├── TSM
    ├── README.md                        // 相关说明
    ├── model
        ├── onnx2om.sh                   // 模型转换脚本
    ├── label
        ├── kinetics_val.csv             // label文件
    ├── download_data
        ├── k400_extractor.sh            // 解压数据集脚本
    ├── online_infer.py                  // 在线推理精度脚本
    ├── offline_infer.py                 // 离线推理精度脚本
    ├── speed.py                         // 离线单视频推理NPU性能脚本
    ├── speed_gpu.py                     // 离线单视频推理GPU性能脚本
```


## 2、 设置环境变量

**步骤1**：设置CANN和mxVision相关环境变量

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #sdk安装路径，根据实际安装路径修改
```

**步骤2**：安装并设置ffmpeg相关环境变量

下载[ffmpeg](https://github.com/FFmpeg/FFmpeg/archive/n4.2.1.tar.gz)，解压进入并执行以下命令安装：

```Shell
./configure --prefix=/usr/local/ffmpeg --enable-shared
make -j
make install
```

安装完毕后执行以下命令设置环境变量

```Shell
export PATH=/usr/local/ffmpeg/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/ffmpeg/lib:$LD_LIBRARY_PATH
```

## 3、 准备模型

**步骤1**：模型文件下载

TSM.onnx模型[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/TSM/offline_models.zip) , 将下载好压缩包解压并把模型放在“${TSM代码根目录}/model”目录下。

**步骤2** 模型转换

将模型转换为om模型，在“model”目录下，执行以下命令生成om模型

```shell
bash onnx2om.sh
```


## 4、 运行

**步骤1**：Kinetics-400数据集下载

参考[Kinetics-400 数据准备](https://github.com/PaddlePaddle/PaddleVideo/blob/develop/docs/zh-CN/dataset/k400.md#%E4%B8%8B%E8%BD%BDvideo%E6%95%B0%E6%8D%AE)中的脚本下载操作，下载验证集链接列表文件val_link.list并编写下载脚本download.sh。放在代码根目录的"download_data"目录下。

```text
├── TSM
    ├── download_data
        ├── download.sh                  // 下载数据集脚本
        ├── k400_extractor.sh            // 解压数据集脚本
        ├── val_link.list    
```

进入代码根目录的"download_data"目录下，执行以下命令下载数据集压缩包val_part1.tar、val_part2.tar、val_part3.tar：

```Shell
bash download.sh val_link.list
```

然后执行以下命令解压数据集到代码根目录下：

```Shell
bash k400_extractor.sh
```

数据集结构如下：

```text
├── TSM
    ├── data
        ├── abseiling
        ├── air_drumming
        ├── ...
        ├── zumba
```

**步骤2**：数据集预处理

1、视频抽帧

在代码根目录执行以下命令创建所需目录：

```Shell
mkdir tools
mkdir ops
```

下载[“temporal-shift-module-master.zip”](https://github.com/mit-han-lab/temporal-shift-module/tree/master)代码包并上传服务器解压，将代码包中"tools"目录下的"vid2img_kinetics.py"、"gen_label_kinetics.py"、"kinetics_label_map.txt"三个文件拷贝至参考设计代码根目录的“tools”目录下。

```text
├── TSM
    ├── tools 
        ├── gen_label_kinetics.py        // label生成脚本
        ├── vid2img_kinetics.py          // 视频抽帧脚本
        ├── kinetics_label_map.txt
```

将代码包中"ops"目录下的"basic_ops.py"、"dataset.py"、"dataset_config.py"、"models.py"、"temporal_shift.py"、"transforms.py"六个文件拷贝至参考设计代码根目录的“ops”目录下。

```text
    ├── ops
        ├── basic_ops.py
        ├── dataset.py                   // 数据集构建脚本
        ├── dataset_config.py            // 数据集配置脚本
        ├── models.py                    // 模型搭建脚本 
        ├── temporal_shift.py
        ├── transforms.py
```

修改“tools”目录下的 vid2img_kinetics.py 内容，将77、78行注释。

```text

77行 #class_name = 'test'
78行 #class_process(dir_path, dst_dir_path, class_name)

``` 

在参考设计代码根目录下，执行以下命令对数据集视频进行抽帧并生成图片：

```shell
mkdir dataset
cd ./tools
python3 vid2img_kinetics.py ../data ../dataset/
```

修改“tools”目录下gen_label_kinetics.py 内容。

```text

# 11行 dataset_path = '../dataset'           # 放视频抽帧后的图片路径
# 12行 label_path = '../label'               # 存放label路径
# 25行 files_input = ['kinetics_val.csv']
# 26行 files_output = ['val_videofolder.txt']
# 37行 folders.append(items[1])
# 57行 output.append('%s %d %d'%(os.path.join('../dataset/',os.path.join(categories_list[i], curFolder)), len(dir_files), curIDX))

``` 

在“tools”目录下，执行以下命令生成标签文件：

```shell
python3 gen_label_kinetics.py
```

**步骤3**：运行精度测试

修改${TSM代码根目录}/ops/dataset_config.py 脚本中参数root_data、filename_imglist_train和filename_imglist_val，若仅进行离线精度测试则可忽略filename_imglist_train设置。

```shell
# 8行 ROOT_DATASET = './label/'    # 标签文件所在路径

...

# 92行 def return_kinetics(modality):
# 93行     filename_categories = 400
# 94行     if modality == 'RGB':
# 95行         root_data = ROOT_DATASET                                # 训练集根目录
# 96行         filename_imglist_train = 'train_videofolder.txt'        # 训练数据集标签
# 97行         filename_imglist_val = 'val_videofolder.txt'            # 测试数据集标签
# 98行         prefix = 'img_{:05d}.jpg'
# 99行     else:
# 100行        raise NotImplementedError('no such modality:' + modality)
# 101行    return filename_categories, filename_imglist_train, filename_imglist_val, root_data, prefix
```

在参考设计代码根目录下，运行精度测试脚本

```shell
python3 offline_infer.py kinetics
```
运行完成后屏幕输出如下信息表示运行成功
```
-----finished-----
Final Prec@x XX% Prec@x XX% 
```
