## 1 介绍

### 1.1 简介

mxVison ascend 硬件平台内置了视频相关的硬件加速编解码器，为了提升用户的易用性，Vision SDK提供了 Ffmepg-Ascend 解决方案。

支持的功能：

|功能|mpeg4|h264/h265| mjpeg |多路 |
|:----:|:----:|:----:|:-----:|:-------:|
|硬件解码|√|√|   √   |    √    |
|硬件编码|√|√|       |    √    |
|硬件转码|√|√|   √   |    √    |
|硬件缩放|√|√|       |    √    |

注意：mjpeg视频流的转码相关功能只在Atlas A500 A2上适用。

### 1.2 支持的产品

本项目支持昇腾Atlas 300I pro、 Atlas 300V pro、 Atlas A500 A2。

### 1.3 支持的版本
本样例配套的CANN版本、Driver/Firmware版本如下所示：

| CANN版本  | Driver/Firmware版本  |
| ------------------ | -------------- |
| 8.0.RC3   |  24.1.RC3  |


## 2 设置环境变量
* `ASCEND_HOME`     Ascend 安装的路径，一般为 `/usr/local/Ascend`
* 执行命令
    ```bash
    export ASCEND_HOME=/usr/local/Ascend
    . /usr/local/Ascend/ascend-toolkit/set_env.sh #toolkit默认安装路径，根据实际安装路径修改
    ```


## 3 编译

**步骤1：** 在项目目录`Ascendffmpeg/`下添加可执行权限：
```bash
chmod +x ./configure
chmod +x ./ffbuild/*.sh
```

**步骤2：** 在项目目录`Ascendffmpeg/`下执行编译：

编译选项说明：
* `prefix`    -   FFmpeg 及相关组件安装目录
* `enable-shared`    -   FFmpeg 允许生成 so 文件
* `extra-cflags`    -   添加第三方头文件
* `extra-ldflags`    -   指定第三方库位置
* `extra-libs`    -   添加第三方 so 文件
* `enable-ascend`    -   允许使用 ascend 进行硬件加速

执行编译命令：
  ```bash
  ./configure \
      --prefix=./ascend \
      --enable-shared \
      --extra-cflags="-I${ASCEND_HOME}/ascend-toolkit/latest/acllib/include" \
      --extra-ldflags="-L${ASCEND_HOME}/ascend-toolkit/latest/acllib/lib64" \
      --extra-libs="-lacl_dvpp_mpi -lascendcl" \
      --enable-ascend \
      && make -j && make install
  ```

**步骤3：** 添加环境变量

通过指令`find / -name libavdevice.so`查找到文件所在路径，形如`/PATH/TO/mindxsdk-referenceapps/VisionSDK/Ascendffmpeg/ascend/lib/libavdevice.so`，则执行：
```bash
export LD_LIBRARY_PATH=/PATH/TO/mindxsdk-referenceapps/VisionSDK/Ascendffmpeg/ascend/lib:$LD_LIBRARY_PATH
```



## 4 特性介绍

Ascendffmpeg在ffmpeg开源软件基础上，结合昇腾NPU设备硬件加速，扩充了视频编解码能力。

### 4.1 解码

<table><thead>
  <tr>
    <th width='250'>解码器</th>
    <th>介绍</th>
    <th>Mcore</th>
    <th>Legacy</th>
  </tr></thead>
<tbody>
  <tr>
    <td rowspan="5"> h264_ascend</td>
    <td><a href="doc/dec_h26x_ascend.md">link</a></td>
    <td style="text-align: center; vertical-align: middle">✅</td>
    <td style="text-align: center; vertical-align: middle">✅</td>
  </tr>
<tbody>
  <tr>
    <td rowspan="5"> h265_ascend</td>
    <td><a href="doc/dec_h26x_ascend.md">link</a></td>
    <td style="text-align: center; vertical-align: middle">✅</td>
    <td style="text-align: center; vertical-align: middle">✅</td>
  </tr>
  <tbody>
  <tr>
    <td rowspan="5"> mjpeg_ascend</td>
    <td><a href="doc/dec_mjpeg_ascend.md">link</a></td>
    <td style="text-align: center; vertical-align: middle">✅</td>
    <td style="text-align: center; vertical-align: middle">✅</td>
  </tr>
  <tbody>
</table>


### 4.2 编码

<table><thead>
  <tr>
    <th width='250'>编码器</th>
    <th>介绍</th>
    <th>Mcore</th>
    <th>Legacy</th>
    <th>Released</th>    
  </tr></thead>
<tbody>
  <tr>
    <td rowspan="5"> h264_ascend</td>
    <td><a href="doc/enc_h26x_ascend.md">link</a></td>
    <td style="text-align: center; vertical-align: middle">✅</td>
    <td style="text-align: center; vertical-align: middle">✅</td>
    <td style="text-align: center; vertical-align: middle">✅</td>
  </tr>
<tbody>
  <tr>
    <td rowspan="5"> h265_ascend</td>
    <td><a href="doc/enc_h26x_ascend.md">link</a></td>
    <td style="text-align: center; vertical-align: middle">✅</td>
    <td style="text-align: center; vertical-align: middle">✅</td>
    <td style="text-align: center; vertical-align: middle">✅</td>
  </tr>

</table>


## 5 常见问题
### 5.1 文件编译不通过

问题描述： 文件编译不通过

解决方案： 可能是文件格式被改变或者破坏，建议通过以下两种方式直接获取代码，而非文件传输：
- 在环境上通过git clone直接下载该代码仓。
- 直接从代码仓网页gitee下载zip包，并在环境上通过`unzip`解压。

