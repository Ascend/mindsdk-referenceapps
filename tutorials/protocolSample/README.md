# protocolSample 样例说明

## 1 介绍
### 1.1 简介
* 本样例构建一个metadata的protocol数据并送入stream，随后输出至log

* 上传一张jpg格式图片并重命名为test.jpg，在运行目录下执行run.sh

* 请勿使用大分辨率图片

### 1.2 支持的产品
本项目支持昇腾Atlas 300I pro、 Atlas 300V pro

### 1.3 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本：

| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- |
| 6.0.RC3   | 8.0.RC3   |  24.1.RC3  |

### 1.4 三方依赖

| 软件名称  | 版本   |
|-------|------|
| cmake | 3.16 |

### 1.5 代码目录结构说明

```
.
|
|-------- CMakeLists.txt 
|-------- main.cpp  
|-------- run.sh 
|-------- pipeSample.pipeline
|-------- README.md                                
|-------- test.jpg       // 需用户准备

```

## 2 设置环境变量

```bash
#设置CANN环境变量，ascend-toolkit-path为cann安装路径
. ${ascend-toolkit-path}/set_env.sh

#设置MindX SDK 环境变量，SDK-path为mxVision SDK 安装路径
. ${SDK-path}/set_env.sh
```


## 3 编译与运行

**步骤1**：修改日志配置

修改${SDK-path}/config/logging.conf中的第21行console_level为0

```bash
21   console_level=0
```

**步骤2**：图片准备
```
准备一张测试图片，项目文件中并重命名为 `test.jpg`
```

**步骤3**：编译与运行

执行以下命令：
```bash
bash run.sh
```

**步骤4**：查看结果
```
如构建的proto数据正确则可在命令行输出中看到warn登记的日志，以"Output:"开头
```
