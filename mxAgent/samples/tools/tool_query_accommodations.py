# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import json

import tiktoken
from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from loguru import logger
from samples.tools.web_summary_api import WebSummary


@ToolManager.register_tool()
class QueryAccommodations(API):
    name = "QueryAccommodations"
    description = "This api can discover accommodations in your desired city."
    input_parameters = {
        "destination_city": {'type': 'str', 'description': 'The city you aim to reach.'},
        "position": {'type': 'str', 'description': 'The geographical position of accomodation appointed by the user'},
        "rank": {'type': 'str', 'description': 'The rank of hotel the user want to query'}
    }

    output_parameters = {
        'accommodation': {
            'type': 'str',
            'description': 'Contain hotel name, price, type, check-in requirements and other information'
        }
    }

    example = (
        """
         {
            "destination_city": "Rome",
            "position": "Central Park",
            "rank": "five stars"
         }""")

    def __init__(self):
        self.encoding = tiktoken.get_encoding("gpt2")

    def check_api_call_correctness(self, response, groundtruth) -> bool:
        ex = response.exception
        if ex is not None:
            return False
        else:
            return True

    def call(self, input_parameter, **kwargs):
        destination = input_parameter.get('destination_city')
        position = input_parameter.get("position")
        rank = input_parameter.get("rank")
        llm = kwargs.get("llm", None)
        keys = [destination, position, rank]
        keyword = []
        logger.debug(f"search accommodation key words: {','.join(keyword)}")
        for val in keys:
            if val is None or len(val) == 0:
                continue
            if '无' in val or '未' in val or '没' in val:
                continue
            if isinstance(val, list):
                it = flatten(val)
                keyword.append(it)
            keyword.append(val)
        if len(keyword) == 0:
            return self.make_response(input_parameter, results="", exception="")
        keyword.append("住宿")
        prompt = """你是一个擅长文字处理和信息总结的智能助手，你的任务是将提供的网页信息进行总结，并以精简的文本的形式进行返回，
            请添加适当的词语，使得语句内容连贯，通顺。提供的信息是为用户推荐的酒店的网页数据，
            请总结网页信息，要求从以下几个方面考虑：
            1. 酒店的地理位置，星级、评分，评价，品牌信息
            2. 不同的户型对应的价格、房间情况，对入住用户的要求等
            并给出一到两个例子介绍这些情况
            若输入的内容没有包含有效的酒店和住宿信息，请统一返回：【无】
            下面是网页的输入：
            {input}
            请生成总结：
            """
        try:
            webs = WebSummary.web_summary(
                keys=keyword, search_num=3, summary_num=3, summary_prompt=prompt, llm=llm)
        except Exception as e:
            logger.error(e)
            return self.make_response(input_parameter, results=e, success=False, exception=e)
        else:
            if len(webs) == 0:
                content = ""
            else:
                content = json.dumps(webs, ensure_ascii=False)
            logger.info(content)
            res = {
                'accommodation': content
            }
            return self.make_response(input_parameter, results=res, exception="")


def flatten(nested_list):
    """递归地扁平化列表"""
    for item in nested_list:
        if isinstance(item, list):
            return flatten(item)
        else:
            return item
