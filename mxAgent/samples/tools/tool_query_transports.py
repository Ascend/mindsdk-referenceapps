# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


import json

import tiktoken
from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from loguru import logger
from samples.tools.web_summary_api import WebSummary


@ToolManager.register_tool()
class QueryTransports(API):
    name = "QueryTransports"
    description = "This API is used to query relevant travel traffic information from the \
        networkAccording to the user's input question,"
    input_parameters = {
        "departure_city": {'type': 'str', 'description': "The city you'll be flying out from."},
        "destination_city": {'type': 'str', 'description': 'The city user aim to reach.'},
        "travel_mode": {'type': 'str', 'description': 'The mode of travel appointed by the user'},
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

    def check_api_call_correctness(self, response, groundtruth=None) -> bool:
        ex = response.exception
        if ex is not None:
            return False
        else:
            return True

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
            filtered = []
            for val in keys:
                if val is None or len(val) == 0:
                    continue
                if '无' in val or '未' in val or '没' in val or '否' in val:
                    continue
                filtered.append(val)
            if len(filtered) == 0:
                return self.make_response(input_parameter, results="", exception="")
            filtered.append("购票")
            logger.debug(f"search transport key words: {','.join(filtered)}")

            prompt = """你的任务是将提供的网页信息进行总结，并以精简的文本的形式进行返回，
            请添加适当的词语，使得语句内容连贯，通顺。输入是为用户查询的航班、高铁等交通数据，请将这些信息总结
            请总结网页信息，要求从以下几个方面考虑：
            总结出航班或者高铁的价格区间、需要时长区间、并给出2-3例子，介绍车次、时间、时长、价格等
            下面是网页的输入：
            {input}
            请生成总结：
            """
            webs = WebSummary.web_summary(
                filtered, search_num=2, summary_num=2, summary_prompt=prompt, llm=llm)
            if len(webs) == 0:
                content = ""
            else:
                content = json.dumps(webs, ensure_ascii=False)
            logger.info(f"search:{webs}")
            res = {
                'transport': content
            }
        except Exception as e:
            logger.error(e)
            e = str(e)
            return self.make_response(input_parameter, results=e, success=False, exception=e)
        else:
            return self.make_response(input_parameter, results=res, exception="")
