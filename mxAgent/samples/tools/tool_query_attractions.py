# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import json
import tiktoken
from loguru import logger

from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from samples.tools.common import filter_website_keywords
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
            "requirement": "free"
         }""")

    def __init__(self):
        self.encoding = tiktoken.get_encoding("gpt2")

    def call(self, input_parameter: dict, **kwargs):
        destination = input_parameter.get('destination')
        scene = input_parameter.get('scene')
        scene_type = input_parameter.get('type')
        requirement = input_parameter.get('requirement')
        llm = kwargs.get("llm", None)

        keys = [destination, scene, scene_type, requirement]
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
        try:
            filtered = filter_website_keywords(keys)
            filtered.append("景点")
            webs = WebSummary.web_summary(
                filtered, search_num=3, summary_num=3, summary_prompt=summary_prompt, llm=llm)
            res = {'attractions': json.dumps(webs, ensure_ascii=False, indent=4)}
            return self.make_response(input_parameter, results=res, exception="")
        except Exception as e:
            logger.error(e)
            return self.make_response(input_parameter, results=e, success=False, exception=e)
