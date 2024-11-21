# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from abc import ABC
import time

from langchain.prompts import PromptTemplate

from .base_agent import AgentRunResult
from .tool_less_agent import ToollessAgent


INTENT_PROMPT = """
给定用户问题, 请根据用户问题代表的意图进行分类，可分类为 {intents}.

每种分类的含义如下:
{intent_meanings}
请使用一个单词回答.

用户问题：
{query}

分类结果:"""

INTENT_AGENT_PROMPT = PromptTemplate(
    input_variables=["intents", "intent_meanings", "query"],
    template=INTENT_PROMPT
)


class RouterAgent(ToollessAgent, ABC):
    def __init__(self, llm, intents: dict, **kwargs):
        super().__init__(llm, INTENT_AGENT_PROMPT, **kwargs)
        self.intents = intents
        self.query = ""

    def _build_agent_prompt(self, **kwargs):
        intent_str, intents_meaning_str = "", ""
        index = 1
        for intent_key, intent_des in self.intents.items():
            intent_str = intent_str + intent_key + ','
            intents_meaning_str = intents_meaning_str + \
                f"{index}, " + intent_key + ": " + intent_des + "\n"
            index += 1

        intent_str = intent_str.strip(",")
        return self.prompt.format(
            intents=intent_str,
            intent_meanings=intents_meaning_str,
            query=self.query
        )

    # def _prompt_agent(self, llm, **kwargs) -> str:
    #     result = ""
    #     for _ in range(0, self.max_retries):
    #         try:
    #             prompt = self._build_agent_prompt()
    #             llm_response = self._format_step(
    #                 llm(prompt, temperature=0.1, stop=self.stop_list))
    #             return llm_response
    #         except Exception as e:
    #             result = str(e)
    #             time.sleep(5)
    #     return f"send request to llm failed: {result}"
