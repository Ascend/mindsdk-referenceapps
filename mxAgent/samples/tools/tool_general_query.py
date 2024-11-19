# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import json

from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from loguru import logger
from samples.tools.web_summary_api import WebSummary


@ToolManager.register_tool()
class GeneralQuery(API):
    name = "GeneralQuery"
    description = "This api can collect information or answer about the travel related query from internet."
    input_parameters = {
        "keywords": {'type': 'str',
                     "description": "the keys words related to travel plan included in the user's query"},

    }

    output_parameters = {
        'reply': {'type': 'str', 'description': 'the replay from internet to the query'},
    }

    example = (
        """
        {
            "keywords": "北京,美食"
        }
        """)

    def __init__(self):
        pass

    def check_api_call_correctness(self, response, groundtruth=None) -> bool:

        if response['exception'] is None:
            return True
        else:
            return False

    def call(self, input_parameter: dict, **kwargs):
        keywords = input_parameter.get('keywords')
        try:
            if keywords is None or len(keywords) == 0:
                return self.make_response(input_parameter, results="", exception="")
            prompt = """你是一个擅长文字处理和信息总结的智能助手，你的任务是将提供的网页信息进行总结，并以精简的文本的形式进行返回，
            请添加适当的词语，使得语句内容连贯，通顺，但不要自行杜撰，保证内容总结的客观性。
            下面是网页的输入：
            {input}
            请生成总结段落：
            """
            webs = WebSummary.web_summary(
                keys=keywords, search_num=3, summary_num=3, summary_prompt=prompt)

            if len(webs) == 0:
                content = ""
            else:
                content = json.dumps(webs, ensure_ascii=False)
            logger.info(content)
            res = {
                'reply': content
            }

        except Exception as e:
            logger.error(e)
            e = str(e)
            return self.make_response(input_parameter, results=e, success=False, exception=e)
        else:
            return self.make_response(input_parameter, results=content, exception="")


if __name__ == '__main__':
    accommodationSearch = GeneralQuery()
    tes = {
        "keywords": "[北京,天气]"
    }
    test = accommodationSearch.call(tes)
