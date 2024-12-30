# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import os
import warnings
import argparse

from langchain._api import LangChainDeprecationWarning
from loguru import logger
from tqdm import tqdm

from agent_sdk.agentchain.react_agent import ReactAgent
from agent_sdk.common.constant import AgentRunStatus
from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from samples.tools import QueryAttractions, QueryTransports, QueryAccommodations, \
    QueryRestaurants
from samples.basic_demo.test_react_reflect import EXAMPLE


warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=LangChainDeprecationWarning)

os.environ["WORKNING_DIR"] = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

MAX_CONTEXT_LEN = 4096


def get_default_react_agent(api_base, api_key, llm_name, max_context_len):
    llm = get_llm_backend(BACKEND_OPENAI_COMPATIBLE, api_base, api_key, llm_name).run
    tool_list = [QueryAttractions, QueryTransports, QueryAccommodations, QueryRestaurants]
    return ReactAgent(llm=llm, example=EXAMPLE, tool_list=tool_list, max_context_len=max_context_len)


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
    agent = get_default_react_agent(API_BASE, API_KEY, LLM_NAME, MAX_CONTEXT_LEN)

    queries = [
        "Book a rental car for two people in Salt Lake City from April 15 to April 18, 2022.",
        "Research and list down outdoor activities suitable for adrenaline junkies in Moab \
between April 12 and 14, 2022.",
        "Write a short itinerary for a weekend trip to Nashville, starting on April 15, including live music venues."
    ]

    staus = AgentRunStatus()

    for query in tqdm(queries):
        result = agent.run(query)
        staus.total_cnt += 1
        if agent.finished:
            staus.success_cnt += 1
        current_path = os.path.dirname(os.path.realpath(__file__))
        agent.save_agent_status(f"{current_path}/trajs/react_execution_log.txt")
        agent.reset()
        logger.info("\n")
        logger.info("*" * 150)
        logger.info(f"Question: {query}")
        logger.info("*" * 150)
        logger.info(f"Final answer: {result.answer}\n")

    logger.info(f"success rates: {staus}")
