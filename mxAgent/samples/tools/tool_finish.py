# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from typing import Union

from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager


@ToolManager.register_tool()
class Finish(API):
    description = "Provide a final answer to the given task."

    input_parameters = {
        'answer': {'type': 'str', 'description': "the final result"}
    }

    output_parameters = {}

    example = (
        """
        {
            "plan details": "The final answer the task."
        }
        """)

    def __init__(self) -> None:
        super().__init__()

    def format_tool_input_parameters(self, text) -> Union[dict, str]:
        input_parameter = {"answer": text}
        return input_parameter

    def gen_few_shot(self, thought: str, param: str, idx: int) -> str:
        return (f"Thought: {thought}\n"
                f"Action: {self.__class__.__name__}\n"
                f"Action Input: {param}\n")

    def call(self, input_parameter: dict, **kwargs):
        answer = input_parameter.get('answer', "")
        return self.make_response(input_parameter, answer)
