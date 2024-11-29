# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from abc import ABC
import argparse
from loguru import logger

from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from agent_sdk.agentchain.recipe_agent import RecipeAgent
from agent_sdk.agentchain.router_agent import RouterAgent
from agent_sdk.agentchain.tool_less_agent import ToollessAgent
from agent_sdk.agentchain.base_agent import AgentRunResult

from samples.tools.tool_query_accommodations import QueryAccommodations
from samples.tools.tool_query_transports import QueryTransports
from samples.tools.tool_query_attractions import QueryAttractions
from samples.tools.tool_summary import PlanSummary
from samples.tools.tool_general_query import GeneralQuery
from samples.tools.tool_query_weather import QueryWeather


PESUEDE_CODE = """步骤1：根据用户问题中对景点相关的需求，从网络中搜索相关的景点信息
步骤2：根据用户的问题，从网络中查询相关的出行交通信息。
步骤3：根据用户的问题，从网络中搜索相关的住宿和酒店信息；
步骤4：根据用户的问题，查询用户需要的城市天气情况；
步骤5：总结以上的出行信息、景点游玩、住宿信息等。"""
TRANSPORT_INST = """步骤1：根据用户的输入问题，从网络中查询相关的出行交通信息"""
ATTRACTION_INST = "步骤1：根据用户问题中对景点相关的需求，从网络中搜索相关的景点信息"
HOTEL_INST = """步骤1：根据用户的问题，从网络中搜索相关的住宿和酒店信息，"""
WEATHER_INST = "步骤一：根据用户的问题，查询用户需要的城市天气情况"
OTHER_INST = """步骤1：根据用户的输入，从互联网中查询相关的解答"""


GENERAL_FINAL_PROMPT = """你是一个擅长文字处理和信息总结的智能助手，你的任务是将提供的网页摘要信息进行总结，并以markdown的格式进行返回，
请添加适当的词语，使得语句内容连贯，通顺
请将content和snippet的信息进行综合处理，进行总结，生成一个段落。
涉及到url字段时，使用超链接的格式将网页url链接到网页title上。
参数介绍】：
title：网页标题
url：网页链接
snippet：网页摘要信息
content:网页的内容总结
下面是JSON格式的输入：
{text}  
请生成markdown段落："""

WEATHER_FINAL_PROMPT = """你是一个擅长文字处理和信息总结的智能助手，
当前的工作场景是：天气出行建议；输入的内容是JSON格式的用户所查询城市未来的天气预报，请将这些信息总结为的自然语言展示天气预报的信息，并对用户的出游给除建议，
根据天气的情况，你可以做出一些出行建议，比如是否需要雨具、防晒、保暖等
请添加适当的词语，使得语句内容连贯，通顺，并尽可能保留输入的信息和数据，但不要自行杜撰信息。
提供的信息以JSON的格式进行展示
【参数介绍】：
date：日期
day_weather:白天的天气情况
day_wind_direction：白天风向
day_wind_power： 白天风力
night_weather：夜晚的天气情况
night_wind_direction：夜晚风向
night_wind_power： 夜晚风力
max_degree： 最高温
min_degree：最低温
下面是JSON格式的输入：
{text}
请生成markdown段落：
"""
PLANNER_FINAL_PROMPT = """你是一个擅长规划和文字处理的智能助手，你需要将提供的信息按照下面的步骤撰写一份旅游攻略，输出markdown格式的段落，
你可以添加适当的语句，使得段落通顺，但不要自己杜撰信息。
步骤】
1. 根据【用户需要旅行的天数】，将输入的景点分配到每一天的行程中，每天2-3个景点，并介绍景点的详细情况
2. 叙述输入中推荐的住宿情况，详细介绍酒店的详细情况，和预定链接
3. 叙述输入中查询的交通安排，详细介绍每个出行方案的价格、时间、时长等详细情况，和预定链接
4. 介绍输入中天气预报的情况，根据天气的情况，你可以做出一些出行建议，比如是否需要雨具、防晒、保暖等
【参数介绍】：
title：网页标题
url：网页链接，满足用户需求的酒店筛选结果
content：网页主要内容提取物
snippet：网页摘要信息
输入的信息以JSON格式，下面是的输入：
{text}
请生成markdown段落："""



TRAVEL_PLAN = "TRAVEL_PLAN"
QUERY_ATTRACTION = "QUERY_ATTRACTION"
QUERY_HOTEL = "QUERY_HOTEL"
QUERY_TRANSPORT = "QUERY_TRANSPORT"
QUERY_WEATHER = "QUERY_WEATHER"
OTHERS = "OTHERS"

classifer = [TRAVEL_PLAN, QUERY_ATTRACTION, QUERY_HOTEL, QUERY_TRANSPORT, QUERY_WEATHER, OTHERS]

INST_MAP = {
    TRAVEL_PLAN :PESUEDE_CODE,
    QUERY_ATTRACTION :ATTRACTION_INST,
    QUERY_HOTEL:HOTEL_INST,
    QUERY_TRANSPORT :TRANSPORT_INST,
    QUERY_WEATHER :WEATHER_INST,
    OTHERS:OTHER_INST
}

FINAL_PMT_MAP = {
    TRAVEL_PLAN :PLANNER_FINAL_PROMPT,
    QUERY_ATTRACTION :GENERAL_FINAL_PROMPT,
    QUERY_HOTEL:GENERAL_FINAL_PROMPT,
    QUERY_TRANSPORT :GENERAL_FINAL_PROMPT,
    QUERY_WEATHER :WEATHER_FINAL_PROMPT,
    OTHERS: GENERAL_FINAL_PROMPT

}

TOOL_LIST_MAP = {
    TRAVEL_PLAN :[QueryAccommodations, QueryAttractions, QueryTransports, PlanSummary, QueryWeather],
    QUERY_ATTRACTION :[QueryAttractions],
    QUERY_HOTEL:[QueryAccommodations],
    QUERY_TRANSPORT :[QueryTransports],
    QUERY_WEATHER : [QueryWeather],
    OTHERS:[]
}

intents = {
    TRAVEL_PLAN :"询问旅行规划，问题中要求旅游项目日程安排、交通查询、查询当地住宿等方面的能力",
    QUERY_ATTRACTION :"查询旅游项目、景区、旅游活动",
    QUERY_HOTEL: "仅查询酒店和住宿信息",
    QUERY_TRANSPORT : "与现实中出行、乘坐交通、如高铁、动车、飞机、火车等相关的意图",
    QUERY_WEATHER :"包括气温、湿度、降水等与天气、天气预报相关的意图",
    OTHERS :"与旅游场景不相干的查询"
}



class TalkShowAgent(ToollessAgent, ABC):
    def __init__(self, llm, prompt="你的名字叫昇腾智搜，是一个帮助用户完成旅行规划的助手，你的能力范围包括：'\
                 目的地推荐、行程规划、交通信息查询、酒店住宿推荐、旅行攻略推荐,请利用你的知识回答问题，这是用户的问题:{query}", 
                 **kwargs):
        super().__init__(llm, prompt, **kwargs)
        self.query = ""

    def _build_agent_prompt(self, **kwargs):
        return self.prompt.format(
            query=self.query
        )


class TravelAgent:
    def __init__(self, base_url, api_key, llm_name):
        self.llm = get_llm_backend(backend=BACKEND_OPENAI_COMPATIBLE,
                        base_url=base_url, api_key=api_key, llm_name=llm_name).run
    
    def route_query(self, query):
        router_agent = RouterAgent(llm=self.llm, intents=intents)
        classify = router_agent.run(query).answer
        if classify not in classifer or classify == OTHERS:
            return TalkShowAgent(llm=self.llm)
        return RecipeAgent(name=classify,
                            description="你的名字叫昇腾智搜，是一个帮助用户完成旅行规划的助手，你的能力范围包括：目的地推荐、行程规划、交通信息查询、酒店住宿推荐、旅行攻略推荐",
                            llm=self.llm, 
                            tool_list=TOOL_LIST_MAP[classify],
                            recipe=INST_MAP[classify], 
                            max_steps=3, 
                            max_token_number=4096,
                            final_prompt=FINAL_PMT_MAP[classify])
    
    def run(self, query, stream):   
        agent = self.route_query(query)
        return agent.run(query, stream=stream)


def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("--model_name", type=str, default="Qwen1.5-32B-Chat", help="OpenAI客户端模型名")
    parse.add_argument("--base_url", type=str, default="http://10.44.115.108:1055/v1", help="OpenAI客户端模型地址")
    parse.add_argument("--api_key", type=str, default="EMPTY", help="OpenAI客户端api key")
    return parse.parse_args().__dict__

if __name__ == "__main__":
    args = get_args()
    base_url = args.pop("base_url")
    api_key = args.pop("api_key")
    llm_name = args.pop("model_name")

    llm = get_llm_backend(backend=BACKEND_OPENAI_COMPATIBLE,
                        base_url=base_url, api_key=api_key, llm_name=llm_name).run
    query = "帮我制定一份从北京到上海6天的旅游计划"

    travel_agent = TravelAgent()
    res = travel_agent.run(query, stream=False)
    if isinstance(res, AgentRunResult):
        logger.info("-----------run agent success-------------")
        logger.info(res.answer)
    else:
        for char in res:
            logger.debug(char)
