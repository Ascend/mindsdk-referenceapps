# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import json
import os
import stat
import re
import time
from datetime import datetime, timezone
from loguru import logger

from agent_sdk.agentchain.base_agent import BaseAgent, AgentRunResult
from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from agent_sdk.prompts.pre_prompt import single_action_agent_prompt, single_action_final_prompt


class SingleActionAgent(BaseAgent):
    MISSING_ACTION_ERROR = "Invalid Format: Missing 'Action:' after 'Thought:'"
    MISSING_ACTION_INPUT_ERROR = "Invalid Format: Missing 'Action Input:' after 'Action:'"

    def __init__(self,
                 llm,
                 tool_list,
                 prompt=single_action_agent_prompt,
                 final_prompt=single_action_final_prompt,
                 **kwargs
                 ) -> None:

        if tool_list is None:
            tool_list = [SingleFinish]
        else:
            tool_list.append(SingleFinish)

        super().__init__(llm, prompt, tool_list, **kwargs)
        self.stop_list = ["\nObservation"]
        self.final_prompt = final_prompt
        self.tool_output = ""

    def run(self, query, stream=False, *args, **kwargs):
        logger.info(f"run query: {query}")
        self.query = query

        for key, value in kwargs.items():
            setattr(self, key, value)
        self.finished = False

        while not self.finished and self.curr_step < self.max_steps:
            self.step()
            self.curr_step += 1

        prompt = self._build_final_prompt(self.tool_output)
        if prompt is None:
            self.answer = self.tool_output
        elif isinstance(prompt, str):
            self.answer = self.llm(
                prompt, temperature=0.1, stop=[], stream=stream)
            logger.info(f"Summarize={self.answer}")
        else:
            self.answer = self.llm(prompt, temperature=0.1, stop=[
            ], ismessage=True, stream=stream)

        if stream:
            return self.answer
        else:
            return AgentRunResult(query=self.query, answer=self.answer, scratchpad=self.scratchpad,
                                  finished=self.finished)

    def step(self) -> None:
        llm_response = self._prompt_agent(self.llm)
        self.scratchpad += llm_response
        action_type, argument = self._parse_action(llm_response)
        if action_type == "ParserException":
            result = argument
        else:
            if self.is_valid_tool(action_type):
                tool_response = self.tool_manager.api_call(action_type, argument, llm=self.llm)
                output_str = json.dumps(tool_response.output, ensure_ascii=False, indent=4)
                self.tool_output = output_str
                if tool_response.success:
                    self.finished = True
                result = output_str

            else:
                result = f"{action_type} 不是一个有效的工具，可以使用工具的列表为[{self.tool_names}]"
        logger.info(f"Observation:\n{result}")
        self.scratchpad += f"\nObservation: {result}\n"

    def save_agent_status(self, file_path):
        try:
            instruction = self.prompt.format(
                tools=self.tools,
                tools_name=self.tool_names,
                query=self.query,
                scratchpad=""
            )

            traj = self.scratchpad.strip()
            save_dict = {
                "instruction": instruction,
                "input": "",
                "output": traj,
                "final answer": self.answer,
                "status": self.finished
            }
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info("create log directory")
            flag = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            mode = stat.S_IWUSR | stat.S_IRUSR
            with os.fdopen(os.open(file_path, flags=flag, mode=mode), "a") as fout:
                # json.dump(save_dict, fout, ensure_ascii=False)
                # fout.write("\n")
                fout.write("****************TASK START*******************\n")
                fout.write(f"task: {self.query}\n")
                fout.write(f"trajectory: {traj}\n")
                fout.write(f"status: {self.finished}\n")
                fout.write(f"created_at {str(datetime.now(tz=timezone.utc))}\n")
                fout.write("*****************TASK END*******************\n\n\n")
        except Exception as e:
            logger.error(f"agent_prompt = {self.prompt}")
            logger.error(e)

    def _build_agent_prompt(self, **kwargs):
        return self.prompt.format(
            tools=self.tools,
            tools_name=self.tool_names,
            query=self.query,
            scratchpad=self.scratchpad
        )

    def _build_final_prompt(self, tool_output, **kwargs):
        return self.final_prompt.format(
            query=self.query,
            answer=tool_output
        )

    def _prompt_agent(self, llm, **kwargs):
        result = ""
        for _ in range(0, self.max_retries):
            try:
                prompt = self._build_agent_prompt()
                llm_response = self._format_step(
                    llm(prompt, temperature=0.1, stop=self.stop_list))
                return llm_response
            except Exception as e:
                result = str(e)
                logger.error(e)
                time.sleep(5)
        return f"send request to llm failed: {result}"

    def _parse_action(self, text: str):
        action_match = re.search(r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)", text,
                                 re.DOTALL)

        if action_match:
            action = action_match.group(1).strip()
            action_input = action_match.group(2)
            tool_input = action_input.strip(" ")
            tool_input = tool_input.strip('"')
            return action, tool_input

        if not re.search(r"Action\s*\d*\s*:[\s]*(.*?)", text, re.DOTALL):
            return "ParserException", self.MISSING_ACTION_ERROR
        elif not re.search(r"[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)", text, re.DOTALL):
            return "ParserException", self.MISSING_ACTION_INPUT_ERROR
        else:
            raise Exception(f"Could not parse LLM output: {text}")


@ToolManager.register_tool()
class SingleFinish(API):
    description = "在无法使用其它工具完成任务请求，如'工具'段落没有合适的工具或用户请求无足够信息提取参数等情况，可以使用本工具结束任务."
    input_parameters = {
        'answer': {'type': 'str', 'description': "结束任务的答案"}
    }

    output_parameters = {}

    example = (
        """
        {
            "answer": "Indicate the final answer for the task."
        }"""
    )

    def __init__(self) -> None:
        super().__init__()

    def gen_few_shot(self, thought: str, param: str, idx) -> str:
        return (f"Thought: {thought}\n"
                f"Action: {self.__class__.__name__}\n"
                f"Action Input: {param}\n")

    def check_api_call_correctness(self, response, groundtruth) -> bool:
        ex = response.get("exception")

        if ex is not None:
            return False
        else:
            return True

    def call(self, input_parameter: dict, **kwargs) -> dict:
        answer = input_parameter.get('answer', "")
        return self.make_response(input_parameter, answer, True, True)
