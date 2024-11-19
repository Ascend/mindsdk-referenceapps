# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import tiktoken
import yaml
from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from loguru import logger
from samples.tools.web_summary_api import WebSummary


@ToolManager.register_tool()
class QueryAttractions(API):
    name = "QueryAttractions"
    description = "This api can be used to Search for tourist attractions from websites that '\
        users expect and summarize them."
    input_parameters = {
        'destination': {'type': 'str', 'description': "The destination where the user wants to travel."},
        'scene': {'type': 'str', 'description': 'The specific scenic spot mentioned by the user'},
        'type': {'type': 'str',
                 'description': 'The specific type of scenic spot mentioned by the user, eg museum, park'},
        'requirement': {'type': 'str', 'description': 'The requirement of scenic spot mentioned by the user'},

    }

    output_parameters = {
        'attractions': {
            'type': 'str',
            'description': 'Contains local attractions address, contact information, website, latitude "\
                and longitude and other information'
        }
    }

    example = (
        """
         {
            "destination": "Paris",
            "scene": "The Louvre Museum",
            "type": "Museum",
            "requirement": "historical"
         }""")

    def __init__(self):
        self.encoding = tiktoken.get_encoding("gpt2")

    def check_api_call_correctness(self, response, groundtruth) -> bool:
        ex = response.exception
        if ex is not None:
            return False
        else:
            return True

    def call(self, input_parameter: dict, **kwargs):
        destination = input_parameter.get('destination')
        scene = input_parameter.get('scene')
        scene_type = input_parameter.get('type')
        requirement = input_parameter.get('requirement')
        llm = kwargs.get("llm", None)
        keyword = []
        keys = [destination, scene, scene_type, requirement]
        for val in keys:
            if val is None or len(val) == 0:
                continue
            if '无' in val or '未' in val or '没' in val or '否' in val:
                continue
            if isinstance(val, list):
                it = flatten(val)
                keyword.append(it)
            keyword.append(val)
        if len(keyword) == 0:
            return self.make_response(input_parameter, results="",
                                      exception="failed to obtain search keyword")

        keyword.append('景点')
        logger.debug(f"search attraction key words: {','.join(keyword)}")

        summary_prompt = """你是一个擅长于网页信息总结的智能助手，提供的网页是关于旅游规划的信息，现在已经从网页中获取到了相关的文字内容信息，你需要从网页中找到与**景区**介绍相关的内容，并进行提取，
        你务必保证提取的内容都来自所提供的文本，保证结果的客观性，真实性。
        网页中可能包含多个景点的介绍，你需要以YAML文件的格式返回，每个景点的返回的参数和格式如下：
        **输出格式**：
        - name: xx
        introduction: xx
        **参数介绍**：
        name：景点名称
        introduction：精简的景区介绍，可以从以下这些方面阐述：景点的基本情况、历史文化等信息、景区门票信息、景区开放时间、景区的联系方式、预约方式以及链接，景区对游客的要求等。
        **注意**
        请注意：不要添加任何解释或注释，且严格遵循YAML格式
        下面是提供的网页文本信息：
        {input}
        请开始生成：
        """

        web_output = WebSummary.web_summary(
            keyword, search_num=3, summary_num=3, summary_prompt=summary_prompt, llm=llm)

        if len(web_output) == 0:
            yaml_str = ""
        else:
            yaml_str = yaml.dump(web_output, allow_unicode=True)

        responses = {
            'attractions': yaml_str
        }

        return self.make_response(input_parameter, results=responses, exception="")


def flatten(nested_list):
    """递归地扁平化列表"""
    for item in nested_list:
        if isinstance(item, list):
            return flatten(item)
        else:
            return item
