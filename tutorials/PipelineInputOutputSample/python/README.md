## SDK pipeline 输入输出样例运行

### 介绍
本样例基于mxVision SDK，实现pipeline不同方式的输入输出操作。

### 支持的产品
本项目以昇腾Atlas 300I pro、Atlas 300V pro为主要的硬件平台。

### 支持的版本
本样例配套的MxVision版本、CANN版本、Driver/Firmware版本如下所示：
| MxVision版本  | CANN版本  | Driver/Firmware版本  |
| --------- | ------------------ | -------------- | 
| 5.0.0 | 7.0.0   |  23.0.0  | 
| 6.0.RC2 | 8.0.RC2   |  24.1.RC2  | 

### 配置环境变量
执行以下命令：
```
. /usr/local/Ascend/ascend-toolkit/set_env.sh #CANN默认安装路径，根据实际安装路径修改
. ${SDK_INSTALL_PATH}/mxVision/set_env.sh #根据实际SDK安装路径修改
```

### 运行
```bash
## 参数为1-7的数字。对应的含义可查看main.py, 不传参默认为1。
python3 main.py 参数
```

### 查看结果
执行成功后出现result相关打印。