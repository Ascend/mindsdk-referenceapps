# 模型Tensor数据处理&插件后处理

## 1 介绍

本章节将指导模型Tensor数据解析和封装相关操作，并配套样例描述如何自定义一个插件进行后处理操作。
****
**注意！**  
本样例中后处理指使用模型输出的原始metadata，自行开发插件来进行后处理。  
当类型为4-2中相关的内置类型时，效率不如后处理so库方式
****

### 1.1 简介

#### 1.1.1 metadata结构说明

该结构为模型推理插件mxpi_tensorinfer输出的原始数据，按以下层级封装。

· MxpiTensorPackageList 模型tensor组合列表。

```protobuf
repeated MxpiTensorPackage tensorPackageVec;
```
· MxpiTensorPackage 模型tensor组合数据结。

```protobuf
repeated MxpiMetaHeader headerVec;
repeated MxpiTensor tensorVec;
```
· MxpiTensor 模型tensor数据结构。

```protobuf
uint64 tensorDataPtr; // 内存指针数值
int32 tensorDataSize; // 内存大小，需要和实际内存大小一致，否则可能会导致coredump
uint32 deviceId; // Device编号
MxpiMemoryType memType; // 内存类型
uint64 freeFunc; // 内存销毁函数指针
repeated int32 tensorShape; // 张量形状
bytes dataStr; // 内存中的数据
int32 tensorDataType; //内存中张量的数据类型
```
#### 1.1.2 C++结构体说明
该结构体为TensorBase数据结构相关说明，详情可参考TensorBase.h头文件（位于%SDK%/include/MxBase/Tensor/TensorBase/），本处仅摘抄部分关键信息。
```c++
enum TensorDataType {
    TENSOR_DTYPE_UNDEFINED = -1,
    TENSOR_DTYPE_FLOAT32 = 0,
    TENSOR_DTYPE_FLOAT16 = 1,
    TENSOR_DTYPE_INT8 = 2,
    TENSOR_DTYPE_INT32 = 3,
    TENSOR_DTYPE_UINT8 = 4,
    TENSOR_DTYPE_INT16 = 6,
    TENSOR_DTYPE_UINT16 = 7,
    TENSOR_DTYPE_UINT32 = 8,
    TENSOR_DTYPE_INT64 = 9,
    TENSOR_DTYPE_UINT64 = 10,
    TENSOR_DTYPE_DOUBLE64 = 11,
    TENSOR_DTYPE_BOOL = 12
};
    // 获取tensor部署的设备类型
    MemoryData::MemoryType GetTensorType() const;
    // buffer记录的数据量
    size_t GetSize() const;
    // buffer 字节数据量
    size_t GetByteSize() const;
    // tensor 的shape
    std::vector<uint32_t> GetShape() const;
    std::vector<uint32_t> GetStrides() const;
    // tensor 的 device
    int32_t GetDeviceId() const;
    // tensor 数据类型
    TensorDataType GetDataType() const;
    uint32_t GetDataTypeSize() const;
    // 判断是否在Host
    bool IsHost() const;
    // 判断是否在Device
    bool IsDevice() const;
    // 获取tensor指针
    void* GetBuffer() const;
    APP_ERROR GetBuffer(void *&ptr, const std::vector<uint32_t> &indices) const;
    // host to device
    APP_ERROR ToDevice(int32_t deviceId);
    // host to dvpp
    APP_ERROR ToDvpp(int32_t deviceId);
    // device to host
    APP_ERROR ToHost();
    // 组batch相关
    static APP_ERROR BatchConcat(const std::vector<TensorBase> &inputs, TensorBase &output);
    static APP_ERROR BatchStack(const std::vector<TensorBase> &inputs, TensorBase &output);
    static APP_ERROR BatchVector(const std::vector<TensorBase> &inputs, TensorBase &output,
        const bool &keepDims = false);
    // 详细信息
    std::string GetDesc();
    // 检查错误
    APP_ERROR CheckTensorValid() const;
```

### 1.2 支持的产品

Atlas 300I pro、Atlas 300V pro

### 1.3 支持的版本

| MxVision版本 | CANN版本  | Driver/Firmware版本 |
|------------|---------|-------------------|
| 6.0.RC2    | 8.0.RC2 | 24.1.RC2          |

### 1.4 三方依赖
cmake>=3.6, python=3.9.2

### 1.5 代码目录结构说明

```
├── samplePluginPostProc
|   ├── mindx_sdk_plugin    // 插件样例
|   |   ├── src
|   |   |   ├── mxpi_sampleplugin
|   |   |   |   ├── MxpiSamplePlugin.cpp
|   |   |   |   ├── MxpiSamplePlugin.h
|   |   |   |   └── CMakeLists.txt
|   |   ├── CMakeLists.txt
|   ├── mxVision            // 图像分类识别样例
|   |   ├── C++
|   |   |   ├── main.cpp
|   |   |   ├── run.sh
|   |   |   ├── README.MD
|   |   |   ├── CMakeLists.txt
|   |   |   └── test.jpg    // 自行准备测试图片
|   |   ├── models
|   |   |   ├── yolov3      // 自行准备转换模型
|   |   |   |   ├── yolov3_tf_bs1_fp16.cfg
|   |   |   |   ├── yolov3_tf_bs1_fp16.om
|   |   |   |   └── yolov3.names
|   |   ├── pipeline
|   |   |   └── Sample.pipeline
|   |   ├── python
|   |   |   ├── main.py
|   |   |   ├── run.sh
|   |   |   ├── README.MD
|   |   |   └── test.jpg    // 自行准备测试图片
|   ├── SamplePluginPost.pipeline
|   └── CMakeLists.txt
```
上述目录中`samplePluginPostProc`为工程根目录，`mindx_sdk_plugin`为[插件工程目录](https://gitee.com/ascend/mindxsdk-referenceapps/tree/master/tutorials/mindx_sdk_plugin)，`mxVision`为图像分类识别样例工程目录(直接从SDK中/samples/mxVision获取)。

## 2 设置环境变量

```
# MindX SDK环境变量:
.${SDK-path}/set_env.sh

# CANN环境变量:
.${ascend-toolkit-path}/set_env.sh

# 环境变量介绍
SDK-path:SDK mxVision安装路径
ascend-toolkit-path:CANN安装路径
```
`./mxVision/C++/`和`./mxVision/python/`目录下的run.sh脚本也需要按照对应的环境变量进行修改。

## 3 准备模型

**步骤1** 下载[YOLOv3模型](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/ActionRecognition/ATC%20YOLOv3%28FP16%29%20from%20TensorFlow%20-%20Ascend310.zip)YOLOv3模型。

**步骤2** 将获取到的zip文件解压，并将YOLOV3模型pb文件存放至`./mxVision/models/yolov3/`目录下。

**步骤3** YOLOV3模型转换。

在`./mxVision/models/yolov3/`目录下执行如下命令

```
# 设置环境变量
export install_path=/usr/local/Ascend/ascend-toolkit/latest
export PATH=/usr/local/python3.9.2/bin:${install_path}/atc/ccec_compiler/bin:${install_path}/atc/bin:$PATH
export PYTHONPATH=${install_path}/atc/python/site-packages:${install_path}/atc/python/site-packages/auto_tune.egg/auto_tune:${install_path}/atc/python/site-packages/schedule_search.egg
export LD_LIBRARY_PATH=${install_path}/atc/lib64:$LD_LIBRARY_PATH
export ASCEND_OPP_PATH=${install_path}/opp

# 模型转换
atc --model=./yolov3_tf.pb --framework=3 --output=./yolov3_tf_bs1_fp16 --soc_version=Ascend310P3 --insert_op_conf=./aipp_yolov3_416_416.aippconfig --input_shape="input:1,416,416,3" --out_nodes="yolov3/yolov3_head/Conv_6/BiasAdd:0;yolov3/yolov3_head/Conv_14/BiasAdd:0;yolov3/yolov3_head/Conv_22/BiasAdd:0"
# 说明：out_nodes制定了输出节点的顺序，需要与模型后处理适配。
```

执行完模型转换脚本后，会生成相应的.om模型文件。 执行后终端输出为：
```
ATC start working now, please wait for a moment.
ATC run success, welcome to the next use.
```

## 4 编译与运行

**步骤1** CmakeLists文件配置。

将主目录下的`samplePluginPostProc`、`mindx_sdk_plugin`和`mxVision/C++/`目录下`CMakeLists.txt`文件中`MX_SDK_HOME`设置为上述SDK安装路径。

**步骤2** 配置pipeline。

将`SamplePluginPost.pipeline`复制到`/mxVision/pipeline/`目录下并重命名为`Sample.pipeline`。

**步骤3** 对主工程进行编译。
```
# 创建build目录
cd samplePluginPostProc
mkdir build
cd build

# cmake编译
cmake ..
make
```
编译完成后在`mindx_sdk_plugin/lib/plugins/`下会生成自定义插件*.so文件，在mxVision/C++/目录下会生成可执行文件`main`。

**步骤4** 将插件复制到`${SDK-path}/lib/plugins/`目录下。

**步骤5** 基于自定义插件运行样例。
```
## C++编译运行
cd mxVision/C++/
bash run.sh

# python运行
cd mxVision/python/
bash run.sh
```
**步骤6** 查看结果。

正确运行时会输出类似如下字段结果。其中MxpiSamplePlugin.cpp文件中的日志输出为插件内部结果，main.cpp日志输出为stream结果。此处tensor[0]相关值应该相同
`
```
I20240827 14:57:11.715646 4148982 MxpiSamplePlugin.cpp:117] MxpiSamplePlugin::Process start
W20240827 14:57:11.715947 4148982 MxpiSamplePlugin.cpp:97] source Tensor number:3
W20240827 14:57:11.715998 4148982 MxpiSamplePlugin.cpp:98] Tensor[0] ByteSize in .cpp:172380
Results:{"MxpiClass":[{"classId":42,"className":"The shape of tensor[0] in metadata is 172380, Don’t panic!","confidence":0.314}]}
I20240827 14:57:11.717183 4148982 MxpiSamplePlugin.cpp:173] MxpiSamplePlugin::Process end
```

## 5 常见问题

### 5.1 权限问题

**问题描述：**
```
提示：Check Owner permission failed: Current permission is 7, but required no greater than 6.
```

**解决方案：**

生成的插件*.so文件权限问题，执行`chmod 440 *.so`修改文件权限。


### 5.2 找不到插件

**问题描述：**

```
# 错误1
GStreamer-WARNING **: Failed to load plugin '*/lib/plugins/*.so': libpython3.9.so.1.0: cannot open shared object file: No such file or directory.

# 错误2
E20240827 13:21:49.997465 3987495 MxsmElement.cpp:487] Feature is NULL, can not find the element factory: mxpi_sampleplugin (Code = 6014, Message = "element invalid factory")
E20240827 13:21:49.997692 3987495 MxsmElement.cpp:890] Invalid element factory. (Code = 6014, Message = "element invalid factory")
E20240827 13:21:49.997721 3987495 MxsmDescription.cpp:434] mxpi_sampleplugin0 is an invalid element of "mxpi_sampleplugin". (Code = 6011, Message = "stream element invalid")
E20240827 13:21:49.997758 3987495 MxsmStream.cpp:919] Creates classification+detection Stream failed. (Code = 6014, Message = "element invalid factory")
E20240827 13:21:49.997790 3987495 MxStreamManagerDptr.cpp:555] Create stream(classification+detection) failed. (Code = 6014, Message = "element invalid factory")
```

**解决方案：**

**步骤1** 将Python 3.9.2安装目录下的“libpython3.9.so.1.0”拷贝至“/usr/lib64/”路径下，清除Gstreamer缓存，并将该路径加入到LD_LIBRARYPATH
```
mkdir /usr/lib64
cp /usr/local/Python-3.9.2/libpython3.9.so.1.0 /usr/lib64/
rm ~/.cache/gstreamer-1.0/registry.{arch}.bin
export LD_LIBRARY_PATH=/usr/lib64:$LD_LIBRARY_PATH
```
此时一般错误1可以解决。

**步骤2** 如果错误2未解决，尝试将对应插件复制到`${SDK-path}/lib/plugins/`目录下。
