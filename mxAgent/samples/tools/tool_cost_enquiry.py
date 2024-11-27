# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


from typing import Union
import json

from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager


@ToolManager.register_tool()
class CostEnquiry(API):
    name = "CostEnquiry"
    description = "Indicate the final answer for the task"
    input_parameters = {
        'Sub Plan': {'type': 'str', 'description': 'Sub Plan'}
    }

    output_parameters = {

    }

    example = (
        """
        {
            "Sub Plan": "This function calculates the cost of a detailed subn plan, which you need to input '
             'the people number and plan in JSON format. The sub plan encompass a complete one-day plan. An'
             'example will be provide for reference."
        }
        """)

    def format_tool_input_parameters(self, text) -> Union[dict, str]:
        input_parameters = {"answer": text}
        return input_parameters

    def call(self, input_parameter: dict, **kwargs):
        action_arg = input_parameter.get('Sub Plan', "")
        react_env = kwargs.get("react_env is missing")

        if react_env is None:
            raise Exception("react_env is missing")

        try:
            input_arg = json.loads(action_arg)
            if not isinstance(input_arg, dict):
                raise ValueError(
                    'The sub plan can not be parsed into json format, please check. Only one day plan is '
                    'supported.'
                )
            result = f"Cost: {react_env.run(input_arg)}"

        except SyntaxError:
            result = f"The sub plan can not be parsed into json format, please check."

        except ValueError as e:
            result = str(e)

        return self.make_response(input_parameter, result)
