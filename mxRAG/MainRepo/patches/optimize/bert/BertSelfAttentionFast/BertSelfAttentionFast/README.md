# BertSelfAttention融合算子使用说明

## BertSelfAttention融合算子注册

### 步骤1
root用户默认安装路径下配置环境变量
```sh
source /usr/local/Ascend/ascend-toolkit/set_env.sh
```
非root用户默认安装路径下配置环境变量
```sh
source /home/{当前用户名}/Ascend/ascend-toolkit/set_env.sh
```

### 步骤2
在ops目录下运行run包注册算子
Arm架构对应custom_opp_aarch64.run
x86_64架构对应custom_opp_x86_64.run
```sh
cd ops
./build.sh
cd BertSelfAttention/build_out/
./custom_opp_{arch}.run
```

### 步骤3
在ops目录下拉取ascend/op-plugin工程，并执行一键式注入脚本
运行一键式注入脚本会将op_plugin_patch文件夹中的文件注入到op-plugin工程中，然后编译出包含融合算子的torch_npu包并替换原有的torch_npu包
```sh
cd ops
git clone https://gitee.com/ascend/op-plugin.git
cd op-plugin & git reset --hard a6c6baddb44a9a700d45b543bb5d60770929c1ae & cd ../
bash run_op_plugin.sh
```

#### 表1 custom_opp_{arch}.run参数说明
| 参数           | 说明      |
|--------------|-----------|
| --help \| -h      | 显示帮助信息  |
| --info       | 打印安装包的信息。  |
| --list | 打印安装包的文件列表。 |
| --check | 检测压缩包完整性。 |
| --quiet | 不打印解压过程中的非错误信息。|
| --install-path | 安装到指定路径。|

### 步骤4
在mindxsdk-mxrag/patches/BertSelfAttentionFast 目录下运行一键补丁脚本，给transformers的bert_model.py打一个补丁使能融合算子
```sh
bash bertSAFast_patch.sh
```

## 注意事项
1. 安装patch前，请先设置CANN环境变量
```sh
    source [cann安装路径]（默认为/usr/local/Ascend/ascend-toolkit）/set_env.sh
```
2. 安装patch后使用bert_model请确保已经完成了自定义算子的注册，运行run包注册。

```sh
    custom_opp_aarch64.run
```
3. 出现 aclnnBertSelfAttention not find的问题时请查看是否有设置LD_LIBRARY_PATH环境变量如下：
```sh
export LD_LIBRARY_PATH=$ASCEND_OPP_PATH/vendors/mxRAG/op_api/lib/:$LD_LIBRARY_PATH
```

4. 如果出现protobuf 需要降低版本问题 则需要将pip3 install protobuf==3.19.0版本，安装完成之后可以还原

## 版本依赖
| 软件           | 版本要求      |
|--------------|-----------|
| pytorch      | == 2.1.0  |
| python       | >= 3.8.0  |
| transformers | == 4.41.1 |


