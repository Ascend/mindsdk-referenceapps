# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import re
import time
from abc import ABC
from typing import Union, Generator
from loguru import logger
from pydantic import BaseModel


from agent_sdk.toolmngt.tool_manager import ToolManager


class AgentRunResult(BaseModel):
    query: str
    answer: str
    scratchpad: str
    finished: bool = False


class BaseAgent(ABC):
    def __init__(self, llm, prompt, tool_list=None, max_steps=15, max_token_number=4096,
                 max_context_len=14000, max_retries=3, **kwargs):
        if tool_list is None:
            tool_list = []
        self.llm = llm
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.prompt = prompt
        self.query = ""
        self.answer = ""
        self.curr_step = 0
        self.max_steps = max_steps
        self.max_context_len = max_context_len
        self.max_token_number = max_token_number
        self.scratchpad = ""
        self.max_retries = max_retries
        self.tool_manager = ToolManager()
        self.stop_list = ["\n"]
        self.tools = ""
        self.tool_names = ""
        self.tool_desc_for_agent = ""
        self.finished = False
        self._init_tools(tool_list)

    def reset(self):
        self.query = ""
        self.answer = ""
        self.curr_step = 0
        self.finished = False
        self.scratchpad = ""

    def run(self, query: str, **kwargs):
        logger.info(f"run query: {query}")
        self.query = query
        for key, value in kwargs.items():
            setattr(self, key, value)

        while not (self._is_halted() or self.finished):
            self._step()
            self.curr_step += 1
        return AgentRunResult(query=self.query, answer=self.answer, scratchpad=self.scratchpad)

    def save_agent_status(self, file_path):
        pass

    def is_valid_tool(self, name: str):
        tool_list = self.tool_names.split(", ")
        return True if name in tool_list else False

    def _build_agent_prompt(self, **kwargs):
        raise NotImplementedError

    def _init_tools(self, tool_list):
        self.tool_names = ", ".join([tool.__name__ for tool in tool_list])
        for idx, tool in enumerate(tool_list):
            tool_cls = tool
            usage = tool_cls.build_tool_description_for_prompt()
            agent_tool_desc = tool_cls.build_tool_description_for_recipe()
            self.tools += f"({idx + 1}) {usage}\n"
            self.tool_desc_for_agent += f"({idx + 1}) {agent_tool_desc}\n"

    def _parse_response(self, response) -> Union[str, Generator]:
        return response

    def _step(self):
        logger.info(f"current step {self.curr_step}")
        llm_response = self._prompt_agent(self.llm)
        self.answer = self._parse_response(llm_response)

    def _prompt_agent(self, llm, stream=False, **kwargs) -> Union[str, Generator]:
        result = ""
        for _ in range(0, self.max_retries):
            try:
                prompt = self._build_agent_prompt(**kwargs)
                if isinstance(prompt, str):
                    llm_response = llm(
                        prompt, stop=self.stop_list, stream=stream)
                else:
                    llm_response = llm(
                        prompt, stop=self.stop_list, ismessage=True, stream=stream)
                if not stream:
                    llm_response = self._format_step(llm_response)
                return llm_response
            except Exception as e:
                result = str(e)
                logger.error(e)
                time.sleep(5)
        return f"send request to llm failed: {result}"

    def _is_halted(self) -> bool:
        logger.debug(f"curr_step={self.curr_step}, max_steps={self.max_steps}, finished={self.finished}")
        return self.curr_step >= self.max_steps

    def _format_step(self, text):
        return re.sub(r'\n+', '\n', text).strip()

    def _is_correct(self):
        pass