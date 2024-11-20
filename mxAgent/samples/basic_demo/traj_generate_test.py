# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import json
import os
import warnings
from typing import Callable, List
from tqdm import tqdm
from loguru import logger
from langchain._api import LangChainDeprecationWarning

from agent_sdk.agentchain.base_agent import BaseAgent
from agent_sdk.agentchain.single_action_agent import SingleActionAgent
from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from samples.tools import QueryAccommodations, QueryAttractions, QueryRestaurants, \
    QueryTransports, QueryGoogleDistanceMatrix


API_BASE = "http://10.44.115.98:8006/v1"
API_KEY = "EMPTY"
MODEL_NAME = "Qwen2-7b-Instruct"

os.environ["OPENAI_API_BASE"] = API_BASE
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["MODEL_NAME"] = MODEL_NAME
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
            traj_data = [json.loads(l) for l in open(data_path, "r")]
        else:
            raise ValueError("Unknown file format")

        self._check_data_format(traj_data)
        return traj_data


def get_single_action_agent(api_base, api_key, llm_name):
    tool_list = [
        QueryAccommodations, QueryAttractions, QueryRestaurants,
        QueryTransports, QueryGoogleDistanceMatrix
    ]
    llm = get_llm_backend(BACKEND_OPENAI_COMPATIBLE,
                          api_base, api_key, llm_name).run
    return SingleActionAgent(llm=llm, tool_list=tool_list, max_steps=5)


if __name__ == '__main__':
    single_agent = get_single_action_agent(API_BASE, API_KEY, MODEL_NAME)
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
    generator.generate(output_path="./save_instructions.jsonl", agent=single_agent,
                       load_dataset=lambda: queries)
