import importlib.util
import json
import os

from loguru import logger

from .api import API


class ToolManager:
    apis = {}

    def __init__(self) -> None:
        pass

    @staticmethod
    def remove_extra_parameters(paras, input_parameters) -> dict:
        processed_parameters = {}
        for input_key in paras:
            if input_key not in input_parameters:
                continue
            processed_parameters[input_key] = paras[input_key]
        return processed_parameters

    @staticmethod
    def init_apis(apis_dir):
        all_apis = []
        except_files = ['__init__.py', 'api.py']
        for file in os.listdir(apis_dir):
            if file.endswith('.py') and file not in except_files:
                api_file = file.split('.')[0]
                basename = os.path.basename(apis_dir)
                module = importlib.import_module(f'{basename}.{api_file}')
                classes = [getattr(module, x) for x in dir(module) if isinstance(getattr(module, x), type)]
                for cls in classes:
                    if issubclass(cls, API) and cls is not API:
                        all_apis.append(cls)
        return all_apis

    @classmethod
    def register_tool(cls):
        def wrapper(apicls):
            if issubclass(apicls, API) and apicls is not API:
                name = apicls.__name__
                cls_info = {
                    'name': name,
                    'class': apicls,
                    'description': apicls.description,
                    'input_parameters': apicls.input_parameters,
                    'output_parameters': apicls.output_parameters,
                }
                instance = apicls()
                cls_info["instance"] = instance
                cls.apis[name] = cls_info
            return apicls

        return wrapper

    def get_api_by_name(self, name: str):
        for _name, api in self.apis.items():
            if _name == name:
                return api
        logger.error(f"failed to get_api_by_name={name}")
        return None

    def get_api_description(self, name: str):
        api_info = self.get_api_by_name(name).copy()
        api_info.pop('class')
        if 'init_database' in api_info:
            api_info.pop('init_database')
        return json.dumps(api_info)

    def init_tool(self, tool_name: str, *args, **kwargs):
        tool = self.get_api_by_name(tool_name)['instance']

        # tool = api_class(*args, **kwargs)

        return tool

    def executor_call(self, tool_name: str, paras: dict, llm):
        tool = self.init_tool(tool_name)
        parameter = paras if paras else {}
        input_parameters = self.get_api_by_name(tool_name)['input_parameters']
        processed_parameters = self.remove_extra_parameters(
            parameter, input_parameters)
        response = tool.call(processed_parameters, llm=llm)
        return response.output
        # recipe agent需要使用response
        # 这个地方需要统一为一个 call, 使用output

    def api_call(self, tool_name: str, text: str, **kwargs):
        tool = self.init_tool(tool_name)
        tool_param = tool.format_tool_input_parameters(text)

        if isinstance(tool_param, str):
            return tool.make_response(None, tool_param, False)
        input_parameters = self.get_api_by_name(tool_name)['input_parameters']
        processed_parameters = self.remove_extra_parameters(
            tool_param, input_parameters)

        try:
            response = tool.call(processed_parameters, **kwargs)
        except Exception as e:
            msg = f'failed to invoke {tool_name}'
            logger.error(f'{msg}, error={e}')
            return tool.make_response(processed_parameters, msg, True)

        return response

    def list_all_apis(self):
        return [_name for _name, api in self.apis.items()]
