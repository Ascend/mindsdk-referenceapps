# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from .openai_compatible import OpenAICompatibleLLM

BACKEND_OPENAI_COMPATIBLE = 1

def get_llm_backend(backend, api_base, api_key, llm_name):
    if backend == BACKEND_OPENAI_COMPATIBLE:
        return OpenAICompatibleLLM(api_base, api_key, llm_name)
    else:
        raise Exception(f"not support backend: {backend}")