# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


import json
import os
import re
from typing import Tuple
from agent_sdk.toolmngt.tool_manager import ToolManager

import numpy as np
import pandas as pd
from agent_sdk.toolmngt.api import API, APIResponse
from loguru import logger


@ToolManager.register_tool()
class QueryGoogleDistanceMatrix(API):
    name = "QueryGoogleDistanceMatrix"
    input_parameters = {
        'origin': {'type': 'str', 'description': "The departure city of your journey."},
        'destination': {'type': 'str', 'description': "The destination city of your journey."},
        'mode': {'type': 'str',
                 'description': "The method of transportation. Choices include 'self-driving' and 'taxi'."}
    }

    output_parameters = {
        'origin': {'type': 'str', 'description': 'The origin city of the flight.'},
        'destination': {'type': 'str', 'description': 'The destination city of your flight.'},
        'cost': {'type': 'str', 'description': 'The cost of the flight.'},
        'duration': {'type': 'str', 'description': 'The duration of the flight. Format: X hours Y minutes.'},
        'distance': {'type': 'str', 'description': 'The distance of the flight. Format: Z km.'},
    }

    usage = f"""{name}[origin, destination, mode]:
    Description: This api can retrieve the distance, time and cost between two cities.
    Parameter:
        origin: The departure city of your journey.
        destination: The destination city of your journey.
        mode: The method of transportation. Choices include 'self-driving' and 'taxi'.
    Example: {name}[origin: Paris, destination: Lyon, mode: self-driving] would provide driving distance, time and cost between Paris and Lyon.
    """

    example = (
        """
         {
            "origin": "Paris",
            "destination": "Lyon",
            "mode": "self-driving"
         }""")

    def __init__(self) -> None:
        logger.info("QueryGoogleDistanceMatrix API loaded.")

    def check_api_call_correctness(self, response, groundtruth) -> bool:
        if response['exception'] is None:
            return True
        else:
            return False

    def call(self, input_parameter: dict, **kwargs):
        origin = input_parameter.get('origin', "")
        destination = input_parameter.get('destination', "")
        mode = input_parameter.get('mode', "")
        return self.make_response(input_parameter, f"success to get {mode}, from {origin} to {destination}")
