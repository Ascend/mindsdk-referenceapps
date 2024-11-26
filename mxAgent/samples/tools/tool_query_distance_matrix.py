from loguru import logger

from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
@ToolManager.register_tool()
class QueryGoogleDistanceMatrix(API):
    name = "QueryGoogleDistanceMatrix"
    input_parameters = {
        'origin': {'type': 'str', 'description': "The departure city of your journey."},
        'destination': {'type': 'str', 'description': "The destination city of your journey."},
        'mode': {'type': 'str',
                 'description': "The method of transportation. Choices include 'self-driving', 'flight' and 'taxi'."}
    }

    output_parameters = {
        'origin': {'type': 'str', 'description': 'The origin city of the journey.'},
        'destination': {'type': 'str', 'description': 'The destination city of your journey.'},
        'cost': {'type': 'str', 'description': 'The cost of the journey.'},
        'duration': {'type': 'str', 'description': 'The duration of the journey. Format: X hours Y minutes.'},
        'distance': {'type': 'str', 'description': 'The distance of the journey. Format: Z km.'},
    }

    example = (
        """
         {
            "origin": "Paris",
            "destination": "Lyon",
            "mode": "self-driving"
         }""")

    def __init__(self) -> None:
        logger.info("QueryGoogleDistanceMatrix API loaded.")

    def call(self, input_parameter: dict, **kwargs):
        origin = input_parameter.get('origin', "")
        destination = input_parameter.get('destination', "")
        mode = input_parameter.get('mode', "")
        return self.make_response(input_parameter, f"success to get {mode}, from {origin} to {destination}")
