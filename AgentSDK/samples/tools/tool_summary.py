# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager


@ToolManager.register_tool()
class PlanSummary(API):
    name = "PlanSummary"
    description = "this api uesed to summary all the travel plan."
    input_parameters = {
        'attractions': {'type': 'str', 'description': "the planned arrangement of attraction."},
        'accomadation': {'type': 'str', 'description': "the accomodation information"},
        'transport': {'type': 'str', 'description': "the transport information"},
        'weather': {'type': 'str', 'description': "Weather information for the next few days"},
        'duration': {'type': 'str', 'description': "The days of travel"},
    }

    output_parameters = {
        'summary': {'type': 'str', 'description': 'Summary all the plan of this travel'},
    }

    example = "PlanSummary[attractions,hotel,flight] will summary all the plan of travel inculed attractions,'\
        accomadation,and transport information"
    example = (
        """
        {
            "attractions": "London Bridge, any of several successive structures spanning the River Thames between '\
                Borough High Street in Southwark and King William Street.",
            "accomadation": "Park Plaza London Riverbank In the heart of London, with great transport connections, '\
                culture, shopping, and green spaces",
            "transport": "10 hours from Beijing to London cost $1000.",
        }
        """)

    def __init__(self):
        pass

    def format_tool_input_parameters(self, llm_output) -> dict:
        return llm_output if llm_output else {}


    def call(self, input_parameters, **kwargs):
        # 总的只能输入2500个字左右
        attraction = input_parameters.get('attractions')
        hotel = input_parameters.get('accomadation')
        transport = input_parameters.get('transport')
        weather = input_parameters.get("weather")
        duration = input_parameters.get("duration")

        res = ""
        if duration is not None:
            res += f"【用户需要旅行的天数】：{duration}天\n"
        if attraction is not None:
            res = res + f"【景点汇总】：\n{str(attraction)[:1000]}\n"
        if hotel is not None:
            res = res + f"【住宿安排】：\n{str(hotel)[:500]}\n"
        if transport is not None:
            res = res + f"【交通安排】：\n{str(transport)[:500]}\n"
        if weather is not None:
            res = res + f"【未来几天的天气情况】：\n{str(weather)[:500]}\n"
        summary = {
            "summary": res
        }
        return self.make_response(input_parameters, results=summary, exception="")