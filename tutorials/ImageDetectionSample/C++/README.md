# YOLOv3目标检测样例

## 1 介绍
### 1.1 简介
本开发样例基于MindX SDK实现了对本地图片进行YOLOv3目标检测，生成可视化结果。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖
无

## 2 设置环境变量

```bash
#设置CANN环境变量
. ${install_path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```

## 3 准备模型

**步骤1** 在ModelZoo上下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2** 将获取到的YOLOv3模型文件内的.pb文件存放至`ImageDetectionSample/C++/model/`下。

**步骤3** 使用ATC执行模型转换

因为ATC在识别`--model`路径时无法识别`/C++/`中的`+`, 因此建议先通过执行下面的指令先将路径更改为`/C/`:

在`ImageDetectionSample/`下执行
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
执行完模型转换脚本后，在`model/`目录下会生成相应的`.om`模型文件。执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4 编译与运行

**步骤1：** 准备一张待检测图片，放到项目目录下命名为`test.jpg`。

**步骤2：** 修改项目c++目录下的配置文件`./test.pipeline`：

1. 在第32行 配置mxpi_tensorinfer插件的模型加载路径`modelPath`:
```bash 
29  "mxpi_tensorinfer0": {
30              "props": {
31                  "dataSource": "mxpi_imageresize0",
32                  "modelPath": "${yolov3.om模型路径}"
33              },
34              "factory": "mxpi_tensorinfer",
35              "next": "mxpi_objectpostprocessor0"
36        },
```


2. 在第41和42行 配置模型后处理插件mxpi_objectpostprocessor，添加`coco.names`与 `libyolov3postprocess.so`路径:

- 文件`coco.names`来源于下载的模型文件夹内。

- `postProcessLibPath`的后处理库路径，路径根据SDK安装路径决定，可以通过`find / -name libyolov3postprocess.so`搜索路径。
```bash
37  "mxpi_objectpostprocessor0": {
38              "props": {
39                  "dataSource": "mxpi_tensorinfer0",
40                  "postProcessConfigPath": "model/yolov3_tf_bs1_fp16.cfg",
41                  "labelPath": "${YOLOv3模型文件夹路径}/coco.names",
42                  "postProcessLibPath": "${libyolov3postprocess.so路径}"
43              },
44              "factory": "mxpi_objectpostprocessor",
45              "next": "appsink0"
46          },
```

**步骤3：** 编译项目文件


在项目的c++目录下，新建立build目录，进入build执行cmake ..（..代表包含CMakeLists.txt的源文件父目录），在build目录下生成了编译需要的Makefile和中间文件。执行make构建工程，构建成功后就会生成可执行文件。

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


## 5 常见问题


### 5.1 .sh文件执行报错



**问题描述：**  如果执行`bash run.sh`报错如下：
```
run.sh: line 2: $'\r': command not found
run.sh: line 3: cd: $'.\r\r': No such file or directory
run.sh: line 4: $'\r': command not found
run.sh: line 8: $'\r': command not found
run.sh: line 10: $'\r': command not found
```

**解决方案：**  是文件格式需要转换，执行以下命令转换`run.sh`格式：
```
dos2unix run.sh
```