# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


from typing import List, Dict, Optional
from openai import OpenAI


class OpenAICompatibleLLM:
    def __init__(self, base_url, api_key, llm_name):
        self.base_url = base_url
        self.api_key = api_key
        self.llm_name = llm_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def run(self, prompt, ismessage=False, **kwargs):
        temperature = kwargs.pop("temperature", 0.1)
        stop = kwargs.pop("stop", None)
        max_tokens = kwargs.pop("max_tokens", 4096)
        stream = kwargs.pop("stream", False)

        messages = prompt if ismessage else [{"role": "user", "content": prompt}]
        if stream:
            res = self._chat_stream(messages, temperature, max_tokens, stop=stop, **kwargs)
        else:
            res = self._chat_no_stream(messages, temperature, max_tokens, stop=stop, **kwargs)

        return res

    def _chat_stream(self,
                     messages: List[Dict],
                     temperature: float,
                     max_tokens: int,
                     stop: Optional[List[str]] = None,
                     **kwargs):
        response = self.client.chat.completions.create(
            model=self.llm_name,
            messages=messages,
            stop=stop,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs)
        for chunk in response:
            if hasattr(chunk.choices[0].delta,
                       'content') and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _chat_no_stream(self,
                        messages: List[Dict],
                        temperature: float,
                        max_tokens: int,
                        stop: Optional[List[str]] = None,
                        **kwargs):
        response = self.client.chat.completions.create(
            model=self.llm_name,
            messages=messages,
            stop=stop,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs)
        return response.choices[0].message.content





