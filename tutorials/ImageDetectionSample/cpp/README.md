# YOLOv3目标检测样例

## 1 介绍
### 1.1 简介
本开发样例基于Vision SDK实现了对本地图片进行YOLOv3目标检测，生成可视化结果。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的Vision SDK版本、CANN版本、Driver/Firmware版本如下所示：

| Vision SDK版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖
无

## 2 设置环境变量

```bash
#设置CANN环境变量，cann_install_path为CANN安装路径
. ${cann_install_path}/set_env.sh

#设置Vision SDK 环境变量，sdk_install_path为Vision SDK 安装路径
. ${sdk_install_path}/set_env.sh
```

## 3 准备模型

**步骤1** 下载YOLOv3模型。[下载地址](https://gitee.com/link?target=https%3A%2F%2Fobs-9be7.obs.cn-east-2.myhuaweicloud.com%2F003_Atc_Models%2Fmodelzoo%2Fyolov3_tf.pb)

**步骤2** 将获取到的YOLOv3模型文件内的.pb文件存放至`ImageDetectionSample/C++/model/`下。

**步骤3** 使用ATC执行模型转换

在`ImageDetectionSample/cpp/model/`目录下执行以下命令

```bash
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
```
执行后终端输出为：
```bash
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```
表示命令执行成功。

## 4 编译与运行

**步骤1：** 准备一张待检测图片，放到项目根目录下命名为`test.jpg`。

**步骤2：** 编译项目文件


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