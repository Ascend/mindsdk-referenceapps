## 1 patch 的使用方法

### 1.1 milvus-v2.5.19-ascend.patch

1. 首先克隆官方的 milvus 2.5.19 代码到本地，并将 patch 文件下载到同级目录

2. cd milvus && git am < ../milvus-v2.5.19-ascend.patch

### 1.2 knowhere-v2.5.13-ascend.patch

1. 克隆官方的 knowhere 2.5.13 代码到本地，并将 patch 文件下载到同级目录

2. cd knowhere && git am < ../knowhere-v2.5.13-ascend.patch

## 2 编译流程

### 2.1 安装依赖

安装 Index SDK [相关依赖](https://www.hiascend.com/document/detail/zh/mindsdk/72rc1/indexn/indexug/mxindexfrug_0007.html)

```bash
apt install -y ninja-build libaio-dev libopenblas-dev pkg-config
```

- protobuf >= 3.7
- gcc >= 7.5
- cmake >= 3.26.4
- go >= 1.24.6
- conan == 1.61.0

### 2.2 编译

```bash
export MX_INDEX_HOME=/usr/local/Ascend/
export ASCEND_DEPEND_FAISS_DIR=/usr/local/faiss/faiss1.10.0/
export KNOWHERE_SOURCE_DIR=/path/to/knowhere/
export LD_LIBRARY_PATH=${MX_INDEX_HOME}/mxIndex/host/lib:$LD_LIBRARY_PATH
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /etc/profile

cd milvus
make milvus
```

## 3 运行说明

### 3.1 启动 etcd 和 minio

milvus 服务依赖 etcd 和 minio，我们可以通过 docker compose 进行启动。首先下载配置文件：
```bash
wget https://github.com/milvus-io/milvus/releases/download/v2.5.19/milvus-standalone-docker-compose.yml -O docker-compose.yml
```

删除 milvus-standalone 部分，一会手动启动milvus，然后执行
```bash
docker-compose up -d
```

### 3.2 环境配置

启动一个容器用来运行 milvus，并配置环境变量：
```bash
export LD_LIBRARY_PATH=/usr/lib:/usr/local/Ascend/ascend-toolkit/latest/lib64:/usr/local/Ascend/ascend-toolkit/latest/lib64/plugin/opskernel:/usr/local/Ascend/ascend-toolkit/latest/lib64/plugin/nnengine:/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/mxIndex/host/lib:/usr/local/Ascend/OpenBLAS/lib:/usr/local/faiss/faiss1.10.0/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/path/to/milvus/cmake_build/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/path/to/milvus/internal/core/output/lib:$LD_LIBRARY_PATH
export ASCEND_HOME_PATH=/usr/local/Ascend/ascend-toolkit/latest
export ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit/latest
export TOOLCHAIN_HOME=/usr/local/Ascend/ascend-toolkit/latest/toolkit
export PYTHONPATH=/usr/local/Ascend/ascend-toolkit/latest/python/site-packages:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe
```

修改 config/milvus.yaml:
```yaml
etcd:
    endpoints: milvus-etcd:2379

minio:
    address: milvus-minio
    port: 9000

proxy:
    port: 19666 # 启动容器时映射的端口
```

### 3.3 启动 milvus

参考[此文档](https://www.hiascend.com/document/detail/zh/mindsdk/72rc1/indexn/indexug/mxindexfrug_0014.html)生成并配置算子路径，执行以下命令启动 milvus：
```bash
./bin/milvus run standalone
```

## 4 镜像使用

镜像地址：https://console.huaweicloud.com/swr/?region=cn-north-4#/swr/warehouse/detail/qanly_949120498/mxrag/milvus/tag

启动容器：
```bash
docker run -itd \
  --privileged \
  --user root \
  --name milvus25_test \
  --net host \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  {镜像名}:{版本号} \
  bash
```

参考 3.1 在容器外启动依赖服务。

启动 milvus 服务：
```bash
cd /home/milvus
source env.sh
./bin/milvus run standalone
```