# YOLOv3目标检测样例

## 1 介绍
### 1.1 简介
本开发样例基于MindX SDK实现了对本地图片进行YOLOv3目标检测，生成可视化结果。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖
无

## 2. 设置环境变量

```bash
# 设置CANN环境变量（请确认install_path路径是否正确）
# Set environment PATH (Please confirm that the install_path is correct).

export install_path=/usr/local/Ascend/ascend-toolkit/latest
export PATH=/usr/local/python3.9.2/bin:${install_path}/atc/ccec_compiler/bin:${install_path}/atc/bin:$PATH
export PYTHONPATH=${install_path}/atc/python/site-packages:${install_path}/atc/python/site-packages/auto_tune.egg/auto_tune:${install_path}/atc/python/site-packages/schedule_search.egg
export LD_LIBRARY_PATH=${install_path}/atc/lib64:$LD_LIBRARY_PATH
export ASCEND_OPP_PATH=${install_path}/opp

#设置CANN环境变量
. ${install_path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```

```
# 执行如下命令，打开.bashrc文件
vi .bashrc
# 在.bashrc文件中添加以下环境变量
MX_SDK_HOME=${SDK安装路径}

LD_LIBRARY_PATH=${MX_SDK_HOME}/lib:${MX_SDK_HOME}/opensource/lib:${MX_SDK_HOME}/opensource/lib64:/usr/local/Ascend/ascend-toolkit/latest/acllib/lib64:/usr/local/Ascend/driver/lib64/

GST_PLUGIN_SCANNER=${MX_SDK_HOME}/opensource/libexec/gstreamer-1.0/gst-plugin-scanner

GST_PLUGIN_PATH=${MX_SDK_HOME}/opensource/lib/gstreamer-1.0:${MX_SDK_HOME}/lib/plugins

# 保存退出.bashrc文件
# 执行如下命令使环境变量生效
source ~/.bashrc

#查看环境变量
env
```



## 3. 准备模型

**步骤1** 在ModelZoo上下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2** 将获取到的YOLOv3模型文件内的.pb文件存放至`ImageDetectionSample/C++/model/`下。

**步骤3** 使用ATC执行模型转换

因为ATC在识别`--model`路径时无法识别`/C++/`中的`+`, 因此建议通过执行下面的指令先将路径更改为`/C/`:
在`ImageDetectionSample/`下执行：
```bash
mv ./C++ ./C
```

在`model/`目录下执行以下命令

```bash
# 执行，转换YOLOv3模型
# Execute, transform YOLOv3 model.

atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
# 说明：out_nodes制定了输出节点的顺序，需要与模型后处理适配。
```
执行完模型转换脚本后，会生成相应的.om模型文件。执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4 编译与运行
**步骤1：** 修改配置文件./test.pipeline：

1. 配置mxpi_tensorinfer插件的模型加载路径`modelPath`:
```
"mxpi_tensorinfer0": {
            "props": {
                "dataSource": "mxpi_imageresize0",
                "modelPath": "${yolov3.om模型路径}"
            },
            "factory": "mxpi_tensorinfer",
            "next": "mxpi_objectpostprocessor0"
        },
```
配置模型后处理插件mxpi_objectpostprocessor，`postProcessLibPath`的后处理库路径，路径根据SDK安装路径决定，可以通过`find -name libyolov3postprocess.so`搜索路径。

2. 配置`coco.names`与 `libyolov3postprocess.so`路径:

文件`coco.names`来源于下载的模型文件夹内。
```
"mxpi_objectpostprocessor0": {
            "props": {
                "dataSource": "mxpi_tensorinfer0",
                "postProcessConfigPath": "model/yolov3_tf_bs1_fp16.cfg",
                "labelPath": "${YOLOv3模型文件夹路径}/coco.names",
                "postProcessLibPath": "${libyolov3postprocess.so路径}"
            },
            "factory": "mxpi_objectpostprocessor",
            "next": "appsink0"
        },
```

**步骤2：** 配置CMakeLists.txt文件中的`MX_SDK_HOME`环境变量:

```
set(MX_SDK_HOME ${SDK安装路径})
```


**步骤3：** 编译项目文件


新建立build目录，进入build执行cmake ..（..代表包含CMakeLists.txt的源文件父目录），在build目录下生成了编译需要的Makefile和中间文件。执行make构建工程，构建成功后就会生成可执行文件。

```
# 新建立build目录
mkdir build

#进入build
cd build

# 执行
cmake ..

# 执行make构建工程
make
```
构建成功后就会生成可执行文件，回显为：
```
Scanning dependencies of target sample
[ 50%] Building CXX object CMakeFiles/sample.dir/main.cpp.o
[100%] Linking CXX executable ../sample
[100%] Built target sample
# sample就是CMakeLists文件中指定生成的可执行文件。
```

**步骤4：** 执行脚本

执行run.sh脚本前请先确认可执行文件sample已生成。

```
# 添加执行权限
chmod +x run.sh 

#执行脚本
bash run.sh
```

**步骤5：** 查看结果

执行run.sh完毕后，sample会将目标检测结果保存在工程目录下`result.jpg`中。