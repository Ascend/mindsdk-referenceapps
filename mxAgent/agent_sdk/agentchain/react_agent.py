# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import copy
import json 
import os
import stat
import re 
from abc import ABC
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List
from langchain.prompts import PromptTemplate
from loguru import logger

from agent_sdk.agentchain.base_agent import BaseAgent, AgentRunResult
from agent_sdk.prompts.pre_prompt import travel_agent_prompt, reflect_prompt_value, \
    react_reflect_planner_agent_prompt, REFLECTION_HEADER
from agent_sdk.toolmngt.api import APIResponse


class ReflexionStrategy(Enum):
    REFLEXION = "reflextion"


class APIResponseCache(ABC):
    def __init__(self, max_size=1024) -> None:
        self._max_size = max_size
        self._response: dict = {}

    @property
    def response(self):
        return self._response
    
    @property
    def max_size(self):
        return self._max_size
    
    def add(self, res: APIResponse, action: str, action_input: str):
        if not res.success:
            logger.warning("skip failed response")
            return
        if len(self._response.keys()) > self.max_size:
            raise Exception("too many keys")
        if self._response.get(res.api_name, None) is None:
            logger.info(f"add cache {res}")
        else:
            logger.warning(f"update cache {res}")
        cache = {"name":res.api_name, "Short Description": f"{action}({action_input})", "obj":copy.deepcopy(res)}
        self._response[res.api_name] = cache

    def reset(self):
        self._response = {}
    
    def get_tools_response(self) -> list[APIResponse]:
        return list(self._response.values())


class ReactAgent(BaseAgent, ABC):
    FINAL_ANSWER_ACTION = "Finish"
    MISSING_ACTION_AFTER_THOUGHT_ERROR_MESSAGE = "invalid format: missing 'Action:' after 'Thought:'"
    MISSING_ACTION_INPUT_AFTER_ACTION_ERROR_MESSAGE = "invalid format: missing 'Action Input:' after 'Action:'"
    FINAL_ANSWER_AND_PARSABLE_ACTION_ERROR_MESSAGE = (
        "Parsing LLM output produced both a final answer and a parse-able action"
    )

    class ReactStep(Enum):
        Thought = 1
        Action = 2
        Observation = 3

    @dataclass
    class ActionResult:
        action: str
        action_input: str
        raw_response: str

    def __init__(self, llm, example="", prompt: PromptTemplate = travel_agent_prompt,
                 **kwargs) -> None:
        super().__init__(llm, prompt, **kwargs)
        self.stop_list = ["\nObservation"]
        self.example = example
        self.api_response_cache = APIResponseCache()

    @staticmethod
    def _parse_action(text) -> ActionResult:
        regex = r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"

        action_match = re.search(regex, text, re.DOTALL)
        if action_match:
            action = action_match.group(1).strip()
            action_input = action_match.group(2)
            tool_input = action_input.strip(" ")
            tool_input = tool_input.strip('"')
            return ReactAgent.ActionResult(action=action, action_input=tool_input, raw_response=text)

        if not re.search(r"Action\s*\d*\s*:[\s]*(.*?)", text, re.DOTALL):
            return ReactAgent.ActionResult(action="ParserException",
                                           action_input=ReactAgent.MISSING_ACTION_AFTER_THOUGHT_ERROR_MESSAGE,
                                           raw_response=text)
        elif not re.search(r"[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)", text, re.DOTALL):
            return ReactAgent.ActionResult(action="ParserException",
                                           action_input=ReactAgent.MISSING_ACTION_INPUT_AFTER_ACTION_ERROR_MESSAGE,
                                           raw_response=text)
        else:
            raise Exception(f"Could not parse LLM output: `{text}`")

    def reset(self):
        super().reset()
        self.api_response_cache.reset()

    def save_agent_status(self, file_path: str):
        try:
            instruction = self.prompt.format(
                tools=self.tools,
                times=self.max_steps - 1,
                tools_name=self.tool_names,
                query=self.query,
                example=self.example,
                scratchpad="")
            traj = self.scratchpad.strip()

            save_dict = {
                "instruction": instruction, "input": "", "output": traj,
                "status": self.finished, "created_at": str(datetime.now(tz=timezone.utc)),
                "task": self.query
            }
            save_dict = {
                "task": self.query,
                "trajectory": traj,
                "created_at": str(datetime.now(tz=timezone.utc)),
            }

            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info("create log directory")
            flag = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            mode = stat.S_IWUSR | stat.S_IRUSR
            with os.fdopen(os.open(file_path, flags=flag, mode=mode), "a") as fout:
                fout.write("***************TASK START********************\n")
                fout.write(f"task: {self.query}\n")
                fout.write(f"trajectory: {traj}\n")
                fout.write(f"status: {self.finished}\n")
                fout.write(f"created_at {str(datetime.now(tz=timezone.utc))}\n")
                fout.write("*****************TASK END*******************\n\n\n")
            logger.success(f"save {self.__class__.__name__} status done")
        except Exception as e:
            logger.error(f"prompt = {self.prompt}")
            logger.error(e)
        
    def _add_scratchpad(self, step: ReactStep, message: str):
        if self.scratchpad != "":
            self.scratchpad += "\n"

        if step == ReactAgent.ReactStep.Observation:
            message = f"Observation{self.curr_step + 1}: " + message

        message_lines = message.splitlines()
        for idx, message_line in enumerate(message_lines):
            if message_line.startswith(step.name):
                self.scratchpad += "\n".join(x for x in message_lines[idx:])
                logger.debug(f"self.scratchpad = {self.scratchpad}")
                return 
        self.scratchpad += step.name + ": " + message

    def _parse_response(self, response) -> str:
        self._add_scratchpad(ReactAgent.ReactStep.Thought, response)

        action_rst = self._parse_action(response)
        if action_rst.action == ReactAgent.FINAL_ANSWER_ACTION:
            self.finished = True
            return action_rst.action_input
        if action_rst.action == "ParserException":
            logger.info(f"Observation {self.curr_step}: {action_rst.action_input}")
            self._add_scratchpad(ReactAgent.ReactStep.Observation, action_rst.action_input)
            return action_rst.action_input
        if self.is_valid_tool(action_rst.action):
            resp = self.tool_manager.api_call(action_rst.action, action_rst.action_input, llm=self.llm)
            self.api_response_cache.add(resp, action=action_rst.action, action_input=action_rst.action_input)
            output_str = json.dumps(resp.output, ensure_ascii=False, indent=4)
            result = output_str
            if resp.finished:
                self.answer = output_str
                self.finished = resp.finished
        else:
            result = f"{action_rst.action} is not a valid tool, try one of [{self.tool_names}]."
        self._add_scratchpad(ReactAgent.ReactStep.Observation, result)
        return result
    
    def _build_agent_prompt(self, **kwargs):
        pad = self.scratchpad
        if pad.startswith("Thought: "):
            pad = pad[len("Thought: "):]
        return self.prompt.format(
            tools=self.tools,
            times=self.max_steps - 1,
            tools_name=self.tool_names,
            query=self.query,
            example=self.example,
            scratchpad=pad + "\nThought:" if pad != "" else pad)


class ReactReflectAgent(ReactAgent, ABC):
    def __init__(self, reflect_llm, react_llm, example="", reflect_prompt: PromptTemplate = reflect_prompt_value,
                 prompt: PromptTemplate = react_reflect_planner_agent_prompt,
                 **kwargs) -> None:
        super().__init__(llm=react_llm, example=example, prompt=prompt, **kwargs)
        self.reflect_llm = reflect_llm
        self.reflect_prompt = reflect_prompt
        self.reflections: List[str] = []
        self.reflections_str: str = ''

    def run(self, query: str, **kwargs) -> AgentRunResult:
        logger.debug(f"run query {query}")
        self.query = query
        for key, value in kwargs.items():
            setattr(self, key, value)

        while not (self._is_halted() or self.finished):
            self._step()
            self.curr_step += 1
            if not self.finished:
                self._reflect(ReflexionStrategy.REFLEXION)

        return AgentRunResult(query=self.query, answer=self.answer, scratchpad=self.scratchpad, finished=self.finished)

    def _reflect(self, strategy: ReflexionStrategy) -> None:
        if strategy == ReflexionStrategy.REFLEXION:
            self.reflections += [self._prompt_agent(self.reflect_llm, type="reflect")]
            self.reflections_str = self._format_reflections(self.reflections)
        else:
            raise NotImplementedError(f'Unknown reflection strategy: {strategy}')
        logger.debug(self.reflections_str)

    def _build_agent_prompt(self, **kwargs) -> str:
        if kwargs.get('type') == "reflect":
            return self.reflect_prompt.format(
                query=self.query,
                text=self.text,
                tools=self.tools,
                scratchpad=self.scratchpad)

        return self.prompt.format(
            query=self.query,
            tools=self.tools,
            times=self.max_steps - 1,
            example=self.example,
            scratchpad=self.scratchpad,
            reflections=self.reflections_str)

    def _format_reflections(self, reflections: List[str],
                            header: str = REFLECTION_HEADER) -> str:
        if not reflections:
            return ''
        else:
            return header + 'Reflections:\n- ' + '\n- '.join([r.strip() for r in reflections])