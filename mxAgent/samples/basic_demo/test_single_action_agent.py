# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import json
import os
import warnings
import argparse
from typing import Callable, List
from tqdm import tqdm
from loguru import logger
from langchain._api import LangChainDeprecationWarning

from agent_sdk.agentchain.base_agent import BaseAgent
from agent_sdk.agentchain.single_action_agent import SingleActionAgent
from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from samples.tools import QueryAccommodations, QueryAttractions, QueryRestaurants, \
    QueryTransports, QueryGoogleDistanceMatrix

os.environ["WORKING_DIR"] = os.path.dirname(
    os.path.dirname(os.path.realpath(__file__)))

warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=LangChainDeprecationWarning)


class TrajectoryGenerator:

    @staticmethod
    def generate(output_path: str, agent: BaseAgent, load_dataset: Callable[[], List[str]], **kwargs):
        questions = load_dataset()
        for q in tqdm(questions):
            try:
                agent.run(q, **kwargs)
                agent.save_agent_status(output_path)
                agent.reset()

            except Exception as err:
                logger.warning(f"generate traj failed, query: {q}, agent: {agent.name}, err: {err}")
                continue

    @staticmethod
    def _check_data_format(data):
        if not isinstance(data, list):
            raise ValueError("Data should be a list of dict")

        if len(data) == 0:
            raise ValueError("Data should not be empty")

        if not isinstance(data[0], dict):
            raise ValueError("Data item should be a dict")

        alpaca_format_keys = ["instruction", "input", "output", "status"]
        data_keys_set = set(data[0].keys())

        if not all([key in data_keys_set for key in alpaca_format_keys]):
            raise ValueError("need alpaca data format")

    def _load_data_from_file(self, data_path):
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"File not found: {data_path}")

        if data_path.endswith(".jsonl"):
            data = [json.loads(line) for line in open(data_path, "r")]
        else:
            raise ValueError("Unknown file format")

        self._check_data_format(data)
        return data


def get_single_action_agent(api_base, api_key, llm_name):
    tool_list = [
        QueryAccommodations, QueryAttractions, QueryRestaurants,
        QueryTransports, QueryGoogleDistanceMatrix
    ]
    llm = get_llm_backend(BACKEND_OPENAI_COMPATIBLE,
                          api_base, api_key, llm_name).run
    return SingleActionAgent(llm=llm, tool_list=tool_list, max_steps=5)


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
    single_agent = get_single_action_agent(API_BASE, API_KEY, LLM_NAME)
    queries = [
        "Write a review of the hotel \"The Beach House\" in Charlotte Amalie.",
        "Book a flight from Evansville to Sacramento for April 10th.",
        "Create a list of top 5 attractions in Hilo for a solo traveler.",
        "Compare the prices of hotels in Newark for a 3-night stay.",
        "Book a hotel room in Paducah for April 12th.",
        "Write a travel blog post about visiting the Golden Gate Bridge in San Francisco.",
        "Recommend the best mode of transportation from Flagstaff to Phoenix.",
        "Determine the best time to visit the Statue of Liberty.",
        "Compare the prices of car rentals in Seattle.",
        "What are the top - rated museums in Harrisburg?"
    ]
    generator = TrajectoryGenerator()
    generator.generate(output_path="./single_action_execution.jsonl", agent=single_agent,
                       load_dataset=lambda: queries)
