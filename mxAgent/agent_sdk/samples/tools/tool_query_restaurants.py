# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from loguru import logger

from agent_sdk.toolmngt.api import API, APIResponse
from agent_sdk.toolmngt.tool_manager import ToolManager


@ToolManager.register_tool()
class QueryRestaurants(API):
    description = 'Explore dining options in a city of your choice.'
    input_parameters = {
        'City': {'type': 'str', 'description': "The name of the city where you're seeking restaurants."}
    }

    output_parameters = {
        'restaurant_name': {'type': 'str', 'description': 'The name of the restaurant.'},
        'city': {'type': 'str', 'description': 'The city where the restaurant is located.'},
        'cuisines': {'type': 'str', 'description': 'The cuisines offered by the restaurant.'},
        'average_cost': {'type': 'int', 'description': 'The average cost for a meal at the restaurant.'},
        'aggregate_rating': {'type': 'float', 'description': 'The aggregate rating of the restaurant.'}
    }

    example = (
        """
         {
            "City": "Tokyo"
         }""")

    def __init__(self):
        super().__init__()
        logger.info("Restaurants loaded.")

    def call(self, input_parameter, **kwargs):
        city = input_parameter.get('City', "")
        return self.make_response(input_parameter, f"success to get restaurant in {city}")

    def check_api_call_correctness(self, response, ground_truth=None) -> bool:
        return True
