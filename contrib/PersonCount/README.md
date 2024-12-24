# 人群密度计数

## 1 介绍

### 1.1 简介
本开发样例基于VisionSDK实现端到端人群计数-人群密度估计，输入为一幅人群图像，输出为该图像对应的热力图，并在图上显示对人群数量的估计值。

### 1.2 支持的产品
Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 6.0.RC3 | 8.0.RC3   |  24.1.RC3  | 

## 2 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 3 准备模型
**步骤1**：下载原始caffemodel模型：[下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/PersonCount/model.zip)，并将解压后获取到的所有文件存放至本案例代码的PersonCount/model 目录下。

**步骤2**： 在项目根目录下执行以下命令。
```
atc --input_shape="blob1:8,3,800,1408" --weight="model/count_person.caffe.caffemodel" --input_format=NCHW --output="model/count_person_8.caffe" --soc_version=Ascend310P3 --insert_op_conf=model/insert_op.cfg --framework=0 --model="model/count_person.caffe.prototxt"
```

## 4 编译与运行
**步骤1**：编译后处理插件so：在项目根目录下执行
```
bash build.sh #编译
chmod 440 ./Plugin1/build/libcountpersonpostprocess.so #修改so权限
```

**步骤2**：准备输入图片：在项目根目录下使用`mkdir input`创建input目录，将输入图片命名为IMG_id.jpg放到input目录，其中id替换为图片编号（例如IMG_1.jpg、IMG_2.jpg,需要从1开始严格按照顺序命名）。

**步骤3**：创建输出目录：在项目根目录下使用`mkdir result`创建result目录。

**步骤4**：运行
```
bash run.sh
```

**步骤5**：查看结果：
运行成功后回显会显示输入图片的张数total image number，输出图片存放在result目录。