# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from abc import ABC
from typing import Generator
from langchain.prompts import PromptTemplate

from agent_sdk.agentchain.base_agent import BaseAgent, AgentRunResult
from agent_sdk.prompts.pre_prompt import planner_agent_prompt


class ToollessAgent(BaseAgent, ABC):
    def __init__(self, llm, prompt: PromptTemplate = planner_agent_prompt, **kwargs):
        super().__init__(llm, prompt, max_steps=1, **kwargs)
        self.stop_list = []

    def run(self, query: str, stream=False, **kwargs):
        self.query = query
        for key, value in kwargs.items():
            setattr(self, key, value)

        llm_response = self._prompt_agent(self.llm, stream=stream)
        self.curr_step += 1
        self.finished = True

        if stream:
            self.answer = llm_response
            return self.answer
        else:
            self.answer = self._parse_response(llm_response)
            return AgentRunResult(query=self.query, answer=self.answer,
                                  scratchpad=self.scratchpad, finished=self.finished)

    def _build_agent_prompt(self, **kwargs):
        return self.prompt.format(
            query=self.query,
            text=self.text
        )

    def _parse_response(self, response) -> str | Generator:
        return response
