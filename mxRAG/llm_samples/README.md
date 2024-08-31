# fastchat启动llm说明

## 安装前准备
安装[cann](https://www.hiascend.com/software/cann)<br>
安装[torch_npu](https://gitee.com/ascend/pytorch/releases)<br>
下载[fastchat](https://github.com/lm-sys/FastChat)<br>



## 运行步骤

1.安装fastchat库
```bash
cd /dir/to/fastchat
pip3 install .
```

2.启动服务
```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
python3 fastchat_llm.py --host localhost --port 9001 --model_path /path/to/model --device 0 --ssl --cert_file /path/to/cert --key_file /path/to/key
```

## 注意事项
1. 需要提前下载llm模型权重
2. 如果使用https方式启动，需要自行准备服务证书
3. 如果以localhost启动，需要删除/etc/hosts下的ipv6映射


## 版本依赖
| 配套       | 版本      | 环境准备指导 |
|----------|---------|--------|
| cann | 8.0.RC1| - |
| python   | 3.10.13 | -      |
| torch    | 2.1.0   | -      |
| fastchat | 0.2.36  | -      |