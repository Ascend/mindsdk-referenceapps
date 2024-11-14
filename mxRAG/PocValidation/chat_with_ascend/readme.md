# mxRAG运行说明

## 环境准备(容器化部署)

1.下载mxrag镜像并按操作步骤启动容器,下载参考地址：https://www.hiascend.com/developer/ascendhub/detail/27c1cba133384f59ac7ec2500b0e3ffc

2.下载mindie镜像并按操作步骤启动大模型,下载参考地址：https://www.hiascend.com/developer/ascendhub/detail/af85b724a7e5469ebd7ea13c3439d48f

注意：按照操作步骤完成并执行推理脚本成功后，需按以下步骤继续启动MindIE server大模型推理服务，以供mxRAG调用。参考地址：https://www.hiascend.com/document/detail/zh/mindie/10RC2/envdeployment/instg/mindie_instg_0025.html

3.下载embedding模型,存放在指定目录：如/data/bge-large-zh-v1.5/（与app.py中embedding模型路径对应一致）

4.安装mxRAG软件包(如果容器中已安装mxRAG软件包可跳过此步骤)

（1）解压到指定目录

    tar -xf Ascend-mindxsdk-mxrag_{version}_linux-{arch}.tar.gz --no-same-owner-C 指定路径

（2）安装mxRAG

    pip3 install mx_rag-{version}-py3-none-linux_{arch}.whl
    pip3 install -r requirements.txt

（3）设置环境变量

    source /usr/local/Ascend/ascend-toolkit/set_env.sh
    export PYTHONPATH=/usr/local/lib/python3.10/dist-packages/mx_rag/libs/:$PYTHONPATH

5.编译检索算子，这里-d <dim>表示embedding模型向量化后的维度，-t <chip_type>表示芯片类型，如果无法确定具体的npu_type，则可以通过npu-smi info命令进行查询,取"Name"对应的字段。

    export MX_INDEX_MODELPATH=/home/HwHiAiUser/Ascend/modelpath
    cd /home/HwHiAiUser/Ascend/mxIndex/tools/ && python3 aicpu_generate_model.py -t <chip_type> && python3 flat_generate_model.py -d <dim> -t <chip_type> && cp op_models/* /home/HwHiAiUser/Ascend/modelpath 

6.安装gradio

    pip3 install gradio==4.0.0

## demo运行

1.将app.py文件放至指定目录下

2.调用示例

    python3 app.py  --llm_url "http://127.0.0.1:1025/v1/chat/completions" --port 8080

可通过以下命令查看，并完善其他参数的传入

    python3 app.py  --help

3.运行demo打开前端网页

    ![demo.png](images%2Fdemo.png)
    

说明：此demo适配POC版本的mxrag软件包,如果使用了网络代理启动框架前先关闭代理。如果遇到pydantic.errors.PydanticSchemaGenerationError类错误，请将gradio版本切换至3.50.2。




