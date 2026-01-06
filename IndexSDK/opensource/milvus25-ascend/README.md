# Milvus-ascend

## 1 简介

本项目基于 Milvus 开源代码进行了定制化开发，新增了对 Ascend NPU 检索类型的支持。用户可通过 Milvus Go SDK 在创建索引时指定使用 Ascend 优化的索引类型；在后续查询过程中，Knowhere 将自动调用 mxindex SDK，在 NPU 上执行向量检索，从而显著提升检索性能。

### 1.1 API 参考

目前仅对 GO SDK 进行了适配，milvus 相关接口参考[此文档](https://milvus.io/api-reference/go/v2.5.x/About.md)。

新增索引类型：

1. NewIndexAscendFlat(metricType)

    **用途**：创建一个基于 Ascend 硬件优化的 Flat 索引配置。

    **参数**：metricType(index.MetricType) 如 entity.L2 或 entity.IP。

    **返回**：index.Index

    **示例**：
    ```go
    idx := index.NewIndexAscendFlat(entity.IP)
    ```

2. NewIndexAscendFlatInt8(metricType)

    **用途**：创建一个基于 Ascend 硬件优化的 FlatInt8 索引配置。

    **参数**：metricType(index.MetricType) 如 entity.L2 或 entity.IP。

    **返回**：index.Index

    **示例**：
    ```go
    idx := index.NewIndexAscendFlatInt8(entity.IP)
    ```

**Example**
```go
index := index.NewIndexAscendFlat(entity.IP)
indexTask, err := cli.CreateIndex(ctx, milvusclient.NewCreateIndexOption("my_collection", "vector", index))
if err != nil {
    // handler err
}

err = indexTask.Await(ctx)
if err != nil {
    // handler err
}
```

### 1.2 patch 的使用方法

- milvus-v2.5.19-ascend.patch

    1. 克隆官方的 milvus 2.5.19 代码到本地，并将 patch 文件下载到同级目录

    2. cd milvus && git am < ../milvus-v2.5.19-ascend.patch

- knowhere-v2.5.13-ascend.patch

    1. 克隆官方的 knowhere 2.5.13 代码到本地，并将 patch 文件下载到同级目录

    2. cd knowhere && git am < ../knowhere-v2.5.13-ascend.patch

## 2 编译流程

此节介绍如何从源码编译 milvus-ascend，若使用镜像可跳过此节。

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

删除 milvus-standalone 部分，一会手动启动 milvus，然后执行
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

修改 `config/milvus.yaml`:
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

镜像地址：https://www.hiascend.com/developer/ascendhub/detail/ddde3f36631c4a4eb6edc1ced0cd7ca0

1. 启动容器：
    ```bash
    docker run -u <user> -e ASCEND_VISIBLE_DEVICES=0 -itd \
      --name=milvus-standalone-ascend \
      --network=milvus \
      -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
      -v /etc/ascend_install.info:/etc/ascend_install.info \
      -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
      --publish=0.0.0.0:19666:19666 \
      <镜像名称>:<镜像tag>
    ```

2. 参考第 3 节在容器外启动依赖服务，并修改 `config/milvus.yaml` 配置。

3. 参考[此文档](https://www.hiascend.com/document/detail/zh/mindsdk/72rc1/indexn/indexug/mxindexfrug_0014.html)进行算子生成和路径配置。

4. 启动 milvus 服务：
    ```bash
    cd /home/milvus
    source env.sh
    ./bin/milvus run standalone
    ```

## 5 测试用例

启动 milvus 服务后，可以运行一个简单的用例来进行测试。

1. 用例代码在 `milvus/tests/go_client/ascend/perf_test/hello_ascend.go`，镜像中 milvus-ascend 代码在 `/home/milvus/src/` 下。

2. 下载 go-api，若是源码编译可以跳过此步骤
    ```bash
    mkdir -p /home/milvus/src/milvus/cmake_build/thirdparty
    cd /home/milvus/src/milvus/cmake_build/thirdparty
    git clone https://github.com/milvus-io/milvus-proto.git
    cd milvus-proto && git checkout v2.5.19
    ```

3. 修改 go.mod 使用定制的 GO SDK
    ```bash
    cd /home/milvus/src/milvus/tests/go_client/ascend/perf_test
    # 修改 go.mod
    replace github.com/milvus-io/milvus/client/v2 => /home/milvus/src/milvus/client
    replace github.com/milvus-io/milvus-proto/go-api/v2 => /home/milvus/src/milvus/cmake_build/thirdparty/milvus-proto/go-api
    replace github.com/milvus-io/milvus/pkg/v2 => /home/milvus/src/milvus/pkg
    ```

4. 在宿主机执行 `docker network inspect milvus` 查看 ip，修改 `hello_ascend.go` 中的 `milvusAddr` 参数。

5. `go run hello_ascend.go`