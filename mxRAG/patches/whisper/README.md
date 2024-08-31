# 安装openai-whisper补丁说明

## 安装环境准备

参考：https://gitee.com/ascend/ModelZoo-PyTorch/tree/master/MindIE/MindIE-Torch/built-in/audio/Whisper

| 配套     | 版本要求  |
|---------|---------|
| CANN    | 8.0.RC2 |
| MindIE  | 1.0.RC2 |
| Python  | 3.10.X  |
| PyTorch | 2.1.0   |
| ffmpeg  | 4.2.7   |
| onnx    | 1.16.1  |


1.安装MindIE前需要先source toolkit的环境变量，然后直接安装，以默认安装路径/usr/local/Ascend为例：
```sh
source /usr/local/Ascend/ascend-toolkit/set_env.sh
bash Ascend-mindie_*.run --install
```
2.ubuntu下可通过apt-get install ffmpeg命令安装ffmpeg

## 安装补丁步骤
1.进入patches/whisper目录，下载zh.wav音频文件。
```sh
wget https://paddlespeech.bj.bcebos.com/PaddleAudio/zh.wav
```
2.在patches/whisper目录下进行补丁操作。
```sh
bash whisper_patch.sh
```

## 模型推理
1.命令行调用
```sh
whisper zh.wav --model tiny
```
2.Python调用

```python
from whisper import load_model
from whisper.transcribe import transcribe
# 模型加载
model = load_model('tiny')
result = transcribe(model, audio="zh.wav", verbose=False, beam_size=5, temperature=0)
```
## 注意事项
1.如需更换模型，设备以及device直接修改whisper_patch.sh中参数后再执行补丁操作。
