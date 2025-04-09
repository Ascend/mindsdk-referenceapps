# Index SDK-test

### 介绍
**本仓库提供了昇腾Index SDK 组件实现的几种常见检索算法的demo**

#### 版本配套表
| MindSDK版本  | Index SDK版本  | CANN版本  | HDK版本 | 硬件形态  |
| -------------- | ------------ | -------- | -------- | --------- |
| master | 6.0.RC3 | 8.0.RC3  | 24.1.RC3 | Atlas推理系列产品 Atlas200/300/500 800I A2推理产品 |
| master | 5.0.0 | 7.0.0  | 23.0.0 | Atlas推理系列产品 Atlas200/300/500推理产品 |

之前版本请参见：https://gitee.com/ascend/ascend-referenceapps/tree/master/IndexSDK_samples

master分支对应版本mxIndex 6.0.RC2、mxIndex 6.0.RC1，依赖faiss版本为1.7.4

mxIndex-faiss1.7.1分支对应版本mxIndex 5.0.0、mxIndex 5.0.1，依赖faiss版本为1.7.1

#### 关于MindSDK 更多信息
请关注昇腾社区[MindSDK](https://www.hiascend.com/zh/software/mindx-sdk)的最新版本


### 安装教程

1.  Index SDK [用户指南](https://www.hiascend.com/document/detail/zh/mindsdk/600/index/indexug/mxindexfrug_0007.html)
2. gtest安装教程
``` shell
wget https://github.com/google/googletest/archive/refs/tags/release-1.8.1.tar.gz && \
tar xf release-1.8.1.tar.gz && cd googletest-release-1.8.1 && \
cmake -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/usr/local/gtest . && make -j && make install && \
cd .. && rm -rf release-1.8.1.tar.gz googletest-release-1.8.1
```

### 代码目录结构说明

```
.
|-- CMakeLists.txt
|-- Dockerfile
|   |-- Dockerfile-ascend-toolkit.txt              # 昇腾镜像文件
|   |-- Dockerfile-ascendbase-infer.txt            # 基础镜像文件
|   `-- install_deps.sh                            # 依赖下载安装脚本
|-- README.md
|-- TestAscendIReduction.cpp                       # 降维算法 NN降维 Pcar降维  demo
|-- TestAscendIndexAggressTs.cpp                   # 时空库 IP距离，带属性过滤 支持组batch demo
|-- TestAscendIndexBinaryFlat.cpp                  # 二值化底库特征汉明距离 BinaryFlat算法demo
|-- TestAscendIndexCluster.cpp                     # FP32 聚类场景 AscendCluster算法demo
|-- TestAscendIndexFlat.cpp                        # FP32转FP16 Flat算法暴搜demo 
|-- TestAscendIndexGreat.cpp                       # Great近似检索算法demo
|-- TestAscendIndexIVFSP.cpp                       # IVFSP近似检索算法demo
|-- TestAscendIndexIVFSQ.cpp                       # IVFSQ 近似检索算法demo
|-- TestAscendIndexIVFSQT.cpp                      # IVFSQT近似检索算法demo  
|-- TestAscendIndexIVFSQTwithCpuFlat.cpp           # IVFSQT粗搜加cpu精搜demo
|-- TestAscendIndexInt8Flat.cpp                    # 底库数据为int8 int8Flat算法暴搜demo
|-- TestAscendIndexInt8FlatWithCPU.cpp             # 底库数据为int8 int8Flat算法CPU同步落盘 demo 
|-- TestAscendIndexInt8FlatWithReduction.cpp       # FP32 降维量化为Int8后，int8Flat算法暴搜demo
|-- TestAscendIndexInt8FlatWithSQ.cpp              # FP32 SQ 量化为 int8后, 暴搜demo
|-- TestAscendIndexSQ.cpp                          # FP32 SQ 量化为Int8后，反量化SQ算法暴搜demo
|-- TestAscendIndexSQMulPerformance.cpp            # 布控库 IP距离 SQ算法demo
|-- TestAscendIndexTS.cpp                          # 时空库，汉明距离，带属性过滤demo 
|-- TestAscendIndexTS_int8Cos.cpp                  # 时空库，int8 cos距离，带属性过滤demo  
|-- TestAscendIndexVStar.cpp                       # VStar近似检索算法demo
|-- TestAscendMultiSearch.cpp                      # 多Index批量检索demo
|-- build.sh                                       # 编译安装脚本
|-- dependencies.cmake
`-- faiss-python                                   # python接口
    |-- Faiss安装参考.md                            # python接口安装说明
    |-- MANIFEST.in
    |-- Makefile
    |-- ascendfaiss.py
    |-- setup.py
    |-- swig_ascendfaiss.swig                      # swig 配置文件
    `-- test_ascend_index_flat.py                  # flat算法demo

```

**注：**<kbd>TestAscendIndexIVFSP.cpp</kbd> 需要根据实际情况填写数据集（特征数据、查询数据、groundtruth数据）、码本，所在的目录。
**注：**<kbd>TestAscendIndexGreat.cpp</kbd> 需要根据实际情况填写数据集（特征数据、查询数据、groundtruth数据）、码本，所在的目录。
**注：**<kbd>TestAscendIndexVStar.cpp</kbd> 需要根据实际情况填写数据集（特征数据、查询数据、groundtruth数据）、码本，所在的目录。

<kbd>TestAscendIReduction.cpp</kbd> 需要根据实际情况填写对应的NN降维模型所在的目录。

### Demo使用说明

**1.  请先正确安装Index SDK 组件及其依赖的driver、firmware、Ascend toolkit、OpenBLAS、Faiss** (具体可参考用户指南 安装部署章节)

2.  修改dependencies.cmake 中的 MXINDEX_HOME
```
SET(MXINDEX_HOME /home/work/FeatureRetrieval/mxIndex/    CACHE STRING "")
```
本例中Index SDK默认安装路径为 /home/work/FeatureRetrieval/mxIndex/，可将其修改为Index SDK实际安装路径。

3.  执行一下命令编译demo
``` shell
bash build.sh
```

4.  设置环境变量与生成算子

执行如下命令设置环境变量（根据CANN软件包的实际安装路径修改）：
```
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export LD_LIBRARY_PATH=${MXINDEX_INSTALL_PATH}/host/lib:$LD_LIBRARY_PATH
``` 

MXINDEX_INSTALL_PATH为Index SDK实际安装路径，本例中为/home/work/FeatureRetrieval/mxIndex/

生成算子：

所有算子生成的python文件均在MXINDEX_INSTALL_PATH/tools/目录下，可执行 -h参数 查看具体参数意义

以TestAscendIndexFlat.cpp中需要生成的Flat算子为例, 执行：
```
cd ${MXINDEX_INSTALL_PATH}/ops/
bash custom_opp_{arch}.run

cd ${MXINDEX_INSTALL_PATH}/tools/
生成aicpu和flat 512维的算子
```

算子默认生成在${MXINDEX_INSTALL_PATH}/tools/op_models 路径下，将算子移动至算子目录，执行：
```
mv ${MXINDEX_INSTALL_PATH}/tools/op_models/* ${MXINDEX_INSTALL_PATH}/modelpath/
```

设置算子的环境变量：
```
export $MX_INDEX_MODELPATH=${MXINDEX_INSTALL_PATH}/modelpath
```
注意：算子环境变量请勿使用软链接，而是算子实际所在目录。本例中为/home/work/FeatureRetrieval/mxIndex-{version}/modelpath/

5.  在build目录中找到对应的二进制可执行文件
以TestAscendIndexFlat.cpp为例，执行:
```
cd build/
./TestAscendIndexFlat
```