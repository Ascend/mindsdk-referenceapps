# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


import argparse
from loguru import logger
from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from agent_sdk.agentchain.router_agent import RouterAgent

INTENT = {
    "query_flight": "用户期望查询航班信息", 
    "query_attraction": "用户期望查询旅游景点信息", 
    "query_hotel": "用户期望查询酒店和住宿信息", 
    "plan_attraction": "用户期望给出旅行规划建议",
    "whimsical": "异想天开",
    "other": "其他不符合上述意图的描述"
}

querys = [
    "帮我查一下从北京去深圳的机票", 
    "帮我查一下北京的旅游景点", 
    "我想去北京旅游", 
    "去北京旅游可以住在哪里呢，推荐一下", 
    "帮我去书城买本书", "我想上天"
]




def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("--model_name", type=str, default="Qwen1.5-32B-Chat", help="OpenAI客户端模型名")
    parse.add_argument("--base_url", type=str, default="http://10.44.115.108:1055/v1", help="OpenAI客户端模型地址")
    parse.add_argument("--api_key", type=str, default="EMPTY", help="OpenAI客户端api key")
    return parse.parse_args().__dict__

if __name__ == "__main__":
    args = get_args()
    API_BASE = args.pop("base_url")
    API_KEY = args.pop("api_key")
    LLM_NAME = args.pop("model_name")
    llm = get_llm_backend(backend=BACKEND_OPENAI_COMPATIBLE,
                        base_url=API_BASE, api_key=API_KEY, llm_name=LLM_NAME).run
    agent = RouterAgent(llm=llm, intents=INTENT)
    for query in querys:
        response = agent.run(query)
        agent.reset()
        logger.info(f"query: {query}, intent: {response.answer}")
