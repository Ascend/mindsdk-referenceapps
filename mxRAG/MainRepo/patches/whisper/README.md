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
注意事项：
1.参考设计默认的模型为tiny,运行的设备为Atlas300I Duo推理卡,使用的DEVICE为0，如需更换模型、设备类型、device对应修改whisper_patch.sh中MODEL_NAME、SOC_VERSION、DEVICE参数后再执行补丁操作。

## 模型推理
1.命令行调用
```sh
whisper zh.wav --model tiny
```
其中：zh.wav表示待转译的音频文件,支持的音频类型包括M4A、MP3、MP4、MPEG、MPGA、WAV 和 WEBM等;
tiny表示使用的模型,支持tiny、base、small、medium、large模型。

2.Python调用

```python
from whisper import load_model
from whisper.transcribe import transcribe
# 模型加载
model = load_model('tiny')
# 音频转译
result = transcribe(model, audio="zh.wav", verbose=False, beam_size=5, temperature=0)
print(result['text'])
```
3.运行结果
```commandline
"我認爲跑步最重要的事就是給我帶來了身體健康"
```
## 参数说明
whisper接口功能请参考openai-whisper官方接口:https://github.com/openai/whisper

因模型经过npu适配重新编译，使用时需注意以下两点：

1.whisper.load_model为模型加载方法,使用时参数name填写经过本地向量化的模型名称，如需更换模型请重新编译后再使用；参数download_root默认为编译模型的导出路径，使用时无需填写。

2.whisper.transcribe.transcribe为模型转译方法，当temperature使用默认值0时需声明beam_size=5，当temperature使用其他非0值时需声明best_of=5。
