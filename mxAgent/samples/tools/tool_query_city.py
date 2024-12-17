# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import os
from typing import Union

from agent_sdk.toolmngt.api import API
from loguru import logger
from agent_sdk.toolmngt.tool_manager import ToolManager

current_file_path = os.path.abspath(__file__)
current_folder_path = os.path.dirname(current_file_path)
parent_folder_path = os.path.dirname(current_folder_path)


@ToolManager.register_tool()
class CitySearch(API):
    name = "CitySearch"
    input_parameters = {
        'state': {'type': 'str', 'description': "the name of the state"}
    }

    output_parameters = {
        "state": {'type': 'str', 'description': "the name of the state"},
        "city": {'type': 'str', 'description': "the name of the city in the state"}
    }

    example = (
        """
         {
            "state": "New York"
         }""")

    def __init__(self, path="database/background"):
        self.states_path = os.path.join(parent_folder_path, path, "stateSet.txt")
        self.states_cities_path = os.path.join(parent_folder_path, path, "citySet_with_states.txt")
        self.states = []
        self.cities_in_state = {}

        with open(self.states_path, "r") as f:
            content = f.read()
            content.split('\n')
            for state in content:
                self.states.append(state.strip())

        with open(self.states_cities_path, "r") as f:
            context = f.read()
            context = context.split("\n")

            for city_state in context:
                city_state = city_state.split('\t')
                city = city_state[0].strip()
                state = city_state[1].strip()

                if state in self.cities_in_state.keys():
                    self.cities_in_state[state].append(city)
                else:
                    self.cities_in_state[state] = [city]

        logger.info("cities and states loaded.")

    def format_tool_input_parameters(self, text) -> Union[dict, str]:
        return text

    def call(self, input_parameter: dict, **kwargs):
        state = input_parameter.get('state', '')

        if state in self.cities_in_state.keys():
            results = self.cities_in_state[state]
            results = ", ".join(results)
            results = f"{state} has {results}"

            logger.info("search the cities in state successfully, results:")
            logger.info(results)

            return self.make_response(input_parameter, results)
        else:
            return self.make_response(input_parameter, "Failed to search the cities in state",
                                      exception='cant find state')
