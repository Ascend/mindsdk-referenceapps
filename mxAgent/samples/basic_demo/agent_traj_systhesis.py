# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import os
import warnings

from langchain._api import LangChainDeprecationWarning
from loguru import logger
from tqdm import tqdm

from agent_sdk.agentchain.react_agent import ReactAgent
from agent_sdk.common.enum_type import AgentRunStatus
from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from samples.tools import QueryAttractions, QueryTransports, QueryAccommodations, \
    QueryRestaurants, QueryGoogleDistanceMatrix
from mxAgent.samples.basic_demo.agent_test import EXAMPLE


warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=LangChainDeprecationWarning)

os.environ["WORKNING_DIR"] = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
API_BASE = os.environ.get("OPENAI_API_BASE", "http://10.44.115.98:8006/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "EMPTY")
LLM_NAME = os.environ.get("MODEL_NAME", "Qwen2-7b-Instruct")

MAX_CONTEXT_LEN = 4096


def get_default_react_agent(api_base, api_key, llm_name, max_context_len):
    llm = get_llm_backend(BACKEND_OPENAI_COMPATIBLE, api_base, api_key, llm_name).run
    tool_list = [QueryAttractions, QueryTransports, QueryAccommodations, QueryRestaurants, QueryGoogleDistanceMatrix]
    return ReactAgent(llm=llm, example=EXAMPLE, tool_list=tool_list, max_context_len=max_context_len)


if __name__ == '__main__':
    agent = get_default_react_agent(API_BASE, API_KEY, LLM_NAME, MAX_CONTEXT_LEN)

    queries = [
        "Book a rental car for two people in Salt Lake City from April 15 to April 18, 2022.",
        "Research and list down outdoor activities suitable for adrenaline junkies in Moab \
between April 12 and 14, 2022.",
        "Write a short itinerary for a weekend trip to Nashville, starting on April 15, including live music venues."
    ]

    s = AgentRunStatus()

    for query in tqdm(queries):
        result = agent.run(query)
        s.total_cnt += 1
        if agent.finished:
            s.success_cnt += 1
        agent.save_agent_status("./save_instructions.jsonl")
        agent.reset()
        logger.info("\n")
        logger.info("*" * 150)
        logger.info(f"Question: {query}")
        logger.info("*" * 150)
        logger.info(f"Final answer: {result.answer}")
        logger.info("*" * 150)
        logger.info(f"Trajectory Path: {result.scratchpad}")
        logger.info("*" * 150)

    logger.info(f"success rates: {s}")
    logger.info(f"Total success rates: {s}")
