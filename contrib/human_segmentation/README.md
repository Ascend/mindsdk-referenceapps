# MindXSDK 人体语义分割

## 1 简介
  本开发样例基于MindX SDK实现了端到端的人体语义分割功能。其主要功能是使用human_segmentation模型对输入图片中的人像进行语义分割操作，然后输出mask掩膜图，将其与原图结合，生成标注出人体部分的人体语义分割图片。  
样例输入：一张带有人体的图片。  
样例输出：一张人体对应的mask掩码图，一张标注出人体部分的人体语义分割图片。<br/>

### 1.1 支持的产品

本项目以昇腾Atlas 500 A2为主要的硬件平台。

### 1.2 支持的版本

本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0 | 7.0.0   |  23.0.0  | 
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  | 


## 2 目录结构
本工程名称为human_segmentation，工程目录如下图所示：
```
|-------- data                                // 存放测试图片
|-------- models
|           |---- human_segmentation.om       // 人体语义分割om模型
|-------- result                              // 存放测试结果
|-------- main.cpp                            // 主程序  
|-------- test.pipeline                       //pipeline流水线配置文件    
|-------- README.md   
```

## 3 设置环境变量
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

## 4 模型转换

人体语义分割采用提供的human_segmentation.pb模型。由于原模型是基于tensorflow的人体语义分割模型，因此我们需要借助于ATC工具将其转化为对应的om模型。  
**步骤1**  [下载地址](https://mindx.sdk.obs.cn-north-4.myhuaweicloud.com/mindxsdk-referenceapps%20/contrib/human_segmentation/model.zip)  

**步骤2**  将获取到的human_segmentation模型pb文件和cfg文件存放至：“项目所在目录/model”  

**步骤3**  模型转换  

在pb文件所在目录下执行以下命令  
```
#执行，转换human_segmentation.pb模型
#Execute, transform human_segmentation.pb model.
 
atc --input_shape="input_rgb:1,512,512,3" --input_format=NHWC --output=human_segmentation --soc_version=Ascend310B1 --insert_op_conf=./insert_op.cfg --framework=3 --model=./human_segmentation.pb
```
执行完模型转换脚本后，若提示如下信息说明模型转换成功，会在output参数指定的路径下生成human_segmentation.om模型文件。  
```
ATC run success  
```
模型转换使用了ATC工具，如需更多信息请参考：  

https://www.hiascend.com/document/detail/zh/canncommercial/700/inferapplicationdev/atctool/atlasatc_16_0005.html

## 5 测试

1. 获取om模型   
```
见4： 模型转换
```
2. 配置pipeline  
根据所需场景，配置pipeline文件，调整路径参数等。
```
  #配置mxpi_tensorinfer插件的模型加载路径： modelPath
  "mxpi_tensorinfer0": {
            "props": {
                "dataSource": "mxpi_imageresize0",
                "modelPath": "${human_segmentation.om模型路径}"
            },
            "factory": "mxpi_tensorinfer",
            "next": "appsink0"
        },
```
3. 准备测试图片

将带有人体的jpg格式图片命名为test.jpg存放至：“项目所在目录/data”。

4. 编译项目文件

切换至工程主目录，执行以下命令执行编译
```
bash build.sh
```
5. 运行
```
bash run.sh
```

6. 查看结果  
执行`run.sh`文件后，可在工程目录`result`中查看人体语义分割结果。mask_test.jpg为人体的mask掩码图, result_test.jpg为标注出人体部分的人体语义分割图片。

