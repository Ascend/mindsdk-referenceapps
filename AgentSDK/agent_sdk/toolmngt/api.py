import json
from abc import ABC
from dataclasses import dataclass, field
from typing import Union, Tuple

from agent_sdk.common.constant import THOUGHT, ACTION, OBSERVATION, ACTION_INPUT
from loguru import logger


@dataclass
class APIResponse:
    api_name: str
    input: dict
    output: dict
    success: bool = field(default=True)
    finished: bool = field(default=False)
    exception: str = field(default=None)


class API(ABC):
    description: str = field(default=None)
    input_parameters: field(default_factory=dict)
    output_parameters: field(default_factory=dict)
    example: str = field(default=None)

    @classmethod
    def build_tool_description_for_prompt(cls) -> str:
        parameter_desc = "\n\t".join(
            f"{x}: {cls.input_parameters[x]['description']}" for x in cls.input_parameters.keys())
        parameter_type_desc = ', '.join(f"{x}: {cls.input_parameters[x]['type']}" for x in cls.input_parameters.keys())
        desc = f"{cls.__name__}({parameter_type_desc}) - {cls.description}\nParameters - {parameter_desc}\nExample - '\
            {cls.__name__} {cls.example}"
        return desc

    @classmethod
    def build_tool_description_for_recipe(cls) -> str:
        parameter_desc = "\n".join(
            f"{x}: {cls.input_parameters[x]['description']}" for x in cls.input_parameters.keys())
        output_parameter_desc = "\n".join(
            f"{x}: {cls.output_parameters[x]['description']}" for x in cls.output_parameters.keys())
        parameter_type_desc = ', '.join(f"{x}: {cls.input_parameters[x]['type']}" for x in cls.input_parameters.keys())
        desc = (f"{cls.__name__}({parameter_type_desc}) - {cls.description}\nInputs: - {parameter_desc}\nOutput - " + 
                f"{output_parameter_desc}\nExample - {cls.__name__} {cls.example}")
        return desc

    def gen_few_shot(self, thought: str, param: str, idx: int) -> str:
        p = self.format_tool_input_parameter(param)
        output = self.call(p).output
        try:
            output_json = json.loads(output)
            output = json.dumps(list(output_json[:1]))
        except Exception as e:
            logger.error(e)

        return (f"{THOUGHT}: {thought}\n"
                f"{ACTION}: {self.__class__.__name__}\n"
                f"{ACTION_INPUT}: {param}\n"
                f"{OBSERVATION}{idx}: {output}\n\n")

    def format_tool_input_parameters(self, text) -> Union[dict, str]:
        logger.debug(f"{self.__class__.__name__} parse param start")
        try:
            tool_input = json.loads(text, strict=False)
            return tool_input
        except Exception as e:
            logger.error(f"{self.__class__.__name__} parse param failed {str(e)}")
            return (
                f'Invalid "Action Input" parameter format".\nPlease strictly follow the tool usage example '
                f'format: \n{self.build_tool_description_for_prompt()}\n'
                f'Requirement:\n'
                f'1.Invalid JSON format should only contain key-value pairs; do not add comments or description text "\
                    within the JSON.\n'
                f'2.Please extract the values strictly based on the information provides in the query to ensure that"\
                      the "Action Input" values are accurate and reliable, and do not fabricate them.\n'
                f'3.All parameter key-value pairs should be integrated into a single JSON format; do not use multiple"\
                      JSON objects.')

    def check_api_call_correctness(self, response, groundtruth) -> bool:
        return response.exception is not None

    def call(self, input_parameter: dict, **kwargs):
        raise NotImplementedError

    def make_response(self, parameters, results, success=True, finished=False, exception=""):
        api_name = self.__class__.__name__
        return APIResponse(api_name=api_name,
                           input=parameters,
                           output=results,
                           success=success,
                           finished=finished,
                           exception=exception)

    def make_failed_tip(self, data, key):
        return f"{self.__class__.__name__} failed, available {key}: {', '.join(data[key].unique())}"
