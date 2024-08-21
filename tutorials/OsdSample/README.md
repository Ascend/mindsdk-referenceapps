# SampleOsd 样例说明

## 1 介绍
### 1.1 简介
* 本样例从ExternalOsdInstances.json构建一个绘图单元集合（MxpiOsdInstancesList）的元数据（metadata）并送入stream

* 如构建的proto数据正确则可在程序运行结束后在运行目录找到图片testout.jpg，此图片为输入图像经过缩放后加上绘图单元集合后的输出结果。

### 1.2 支持的产品
本项目以昇腾Atlas 500 A2卡为主要硬件平台。

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 5.0.0 | 7.0.0   |  23.0.0  |
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  |

### 1.4 代码目录结构说明

```
.
|
|-------- C++
|           |---- CMakeLists.txt                    // 编译所需文件
|           |---- main.cpp                          // C++样例主文件
|           |---- run.sh                            // 编译脚本
|-------- image
|           |---- test.jpg                          // 测试图片(需自行准备)
|-------- json
|           |---- ExternalOsdInstances.json         // 绘图单元配置信息
|-------- pipeline
|           |---- SampleOsd.pipeline                // 流程编排文件
|-------- python
|           |---- main.py                           // python样例主文件
|-------- README.md                                 // ReadMe

```

## 2 设置环境变量
在编译和运行项目需要的环境变量如下。

  ```
# 设置环境变量（请确认install_path路径是否正确）
. /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh
  ```

## 3 准备模型
使用mxpi_opencvosd插件前，需要使用osd相关的模型文件，请执行mxVision安装目录下operators/opencvosd/generate_osd_om.sh脚本并生成所需的模型文件。
```bash
# 执行脚本之前需要进入到运行目录下
cd ${SDK_INSTALL_PATH}/mxVision/operators/opencvosd
bash generate_osd_om.sh
```

## 4 编译与运行
>本样例分为C++版本和Python版本，请根据自身需要运行对应样例

**步骤1**：图片准备
```
准备一张测试图片，置于 image 文件夹中，并重命名为 `test.jpg`
```

**步骤2**：编译与运行，C++样例需要先编译再执行，Python样例无编译过程，可以直接执行
#### C++样例
```bash
# 于C++样例主文件所在目录执行以下命令
bash build.sh  # 编译 
./main         # 执行
```
#### Python样例

```bash
# 于python样例主文件所在目录执行以下命令
python3 main.py  # 执行
```


**步骤3**：查看结果
```
运行目录下会生成testout.jpg，图像中存在"Hello, world!"字样
```
