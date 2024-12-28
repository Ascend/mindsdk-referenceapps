# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


import json
from loguru import logger
import tiktoken

from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from samples.tools.common import filter_website_keywords
from samples.tools.web_summary_api import WebSummary


@ToolManager.register_tool()
class QueryTransports(API):
    name = "QueryTransports"
    description = "This API can query relevant travel traffic information from network, including flight number, \
        travel time, distance, price, constraints an so on."
    input_parameters = {
        "departure_city": {'type': 'str', 'description': "The city you'll be flying out from."},
        "destination_city": {'type': 'str', 'description': 'The city user aim to reach.'},
        "travel_mode": {'type': 'str', 'description': "The mode of travel appointed by the user, \
                        Choices include 'self-driving', 'flight', 'train', 'taxi' and so on."},
        "date": {'type': 'str', 'description': 'The date of the user plan to travel'},
        'requirement': {'type': 'str', 'description': 'The more requirement of transportation mentioned by the user'},
    }
    output_parameters = {
        "transport": {'type': 'str',
                      'description': 'the transport information'},
    }

    example = (
        """
        {
            "departure_city": "New York",
            "destination_city": "London",
            "date": "2022-10-01",
            "travel_mode": "flight"
        }
        """)

    def __init__(self):
        self.encoding = tiktoken.get_encoding("gpt2")

    def call(self, input_parameter, **kwargs):
        origin = input_parameter.get('departure_city')
        destination = input_parameter.get('destination_city')
        req = input_parameter.get("requirement")
        travel_mode = input_parameter.get("travel_mode")
        llm = kwargs.get("llm", None)
        try:
            prefix = f"从{origin}出发" if origin else ""
            prefix += f"前往{destination}" if destination else ""
            keys = [prefix, req, travel_mode]

            prompt = """你的任务是将提供的网页信息进行总结，并以精简的文本的形式进行返回，
                请添加适当的词语，使得语句内容连贯，通顺。输入是为用户查询的航班、高铁等交通数据，请将这些信息总结
                请总结网页信息，要求从以下几个方面考虑：
                总结出航班或者高铁的价格区间、需要时长区间、并给出2-3例子，介绍车次、时间、时长、价格等
                下面是网页的输入：
                {input}
                请生成总结：
                """
            filtered = filter_website_keywords(keys)
            webs = WebSummary.web_summary(
                filtered, search_num=3, summary_num=3, summary_prompt=prompt, llm=llm)
            res = {'transport': json.dumps(webs, ensure_ascii=False, indent=4)}
            return self.make_response(input_parameter, results=res, exception="")
        except Exception as e:
            logger.error(e)
            e = str(e)
            return self.make_response(input_parameter, results=e, success=False, exception=e)
