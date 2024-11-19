# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from loguru import logger

from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from agent_sdk.agentchain.router_agent import RouterAgent

llm = get_llm_backend(backend=BACKEND_OPENAI_COMPATIBLE,
                      api_base="http://10.44.115.108:1055/v1", api_key="EMPTY", llm_name="Qwen1.5-32B-Chat").run

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

agent = RouterAgent(llm=llm, intents=INTENT)

for query in querys:
    response = agent.run(query)
    agent.reset()
    logger.info(f"query: {query}, intent: {response.answer}")
