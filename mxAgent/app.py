import os
from threading import Thread
from typing import Iterator, List, Tuple

import gradio as gr
import torch
from openmind import AutoModelForCausalLM, AutoTokenizer
from transformers import TextIteratorStreamer

MAX_MAX_NEW_TOKENS = 2048
DEFAULT_MAX_NEW_TOKENS = 1024
MAX_INPUT_TOKEN_LENGTH = 4096
MAX_HISTORY_LENGTH = 5  # 限制历史对话的长度

DESCRIPTION = """\
# Qwen 中文对话模型
这个space使用模型 [OpenSource/Qwen2-0.5B-Instruct](https://modelers.cn/models/OpenSource/Qwen2-0.5B-Instruct)运行在cpu上的一个demo
"""

device = torch.device('npu') 
model_name = 'KunLun/Qwen1.5-32B-chat'
model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True).to(device)
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)


def generate(
    user_message: str,
    chat_history: List[Tuple[str, str]],
    system_prompt: str = "",
    max_new_tokens: int = 1024,
    temperature: float = 0.6,
    top_p: float = 0.9,
    top_k: int = 50,
    repetition_penalty: float = 1.2,
    stream: bool = False
) -> Iterator[str]:
    # 限制历史记录的长度
    print(user_message)
    if len(chat_history) > MAX_HISTORY_LENGTH:
        chat_history = chat_history[-MAX_HISTORY_LENGTH:]

    conversation = []
    if system_prompt:
        conversation.append({"role": "system", "content": system_prompt})
    conversation.append({"role": "user", "content": user_message})


    input_ids = tokenizer.apply_chat_template(conversation, return_tensors="pt")
    if input_ids.shape[1] > MAX_INPUT_TOKEN_LENGTH:
        input_ids = input_ids[:, -MAX_INPUT_TOKEN_LENGTH:]
        gr.Warning(f"Trimmed input from conversation as it was longer than {MAX_INPUT_TOKEN_LENGTH} tokens.")
    input_ids = input_ids.to(model.device)
    generate_kwargs = dict(
        {"input_ids": input_ids},
        max_new_tokens=max_new_tokens,
        do_sample=True, 
        top_p=top_p,
        top_k=top_k,
        temperature=temperature,
        num_beams=1,
        repetition_penalty=repetition_penalty,
    )
    if stream:
        return stream_generate(generate_kwargs)
    
    output_ids = model.generate(generate_kwargs)
    output_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(input_ids, output_ids)
    ]
    return tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]

def stream_generate(generate_kwargs):
    streamer = TextIteratorStreamer(tokenizer, timeout=10.0, skip_prompt=True, skip_special_tokens=True)
    generate_kwargs['streamer'] = streamer
    t = Thread(target=model.generate, kwargs=generate_kwargs)
    t.start()

    outputs = []
    for text in streamer:
        outputs.append(text)
        yield "".join(outputs)


chat_interface = gr.ChatInterface(
    fn=generate,
    stop_btn=None,
    type="messages"
    examples=[
        ["作为程序员该如何防止脱发？"],
        ["请给我简短的介绍一下python语言的历史?"],
        ["写一篇关于'如何参与到开源贡献社区'的博客"],
        ["给我一份自驾游西藏的攻略"],
        ["写一篇赞美老师的诗词"],
    ],
    cache_examples=False,
)

css = """
h1 {
  text-align: center;
  display: block;
}

#duplicate-button {
  margin: auto;
  color: white;
  background: #1565c0;
  border-radius: 100vh;
}

.contain {
  max-width: 900px;
  margin: auto;
  padding-top: 1.5rem;
}
"""

with gr.Blocks(css=css, fill_height=True) as demo:
    gr.Markdown(DESCRIPTION)
    chat_interface.render()

if __name__ == "__main__":
    demo.queue(max_size=20).launch()