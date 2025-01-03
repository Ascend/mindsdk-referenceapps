# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


import re

from loguru import logger

from agent_sdk.executor.common import ErrorType, ERROR_MAP
from .parser import Node


class SopHandler:
    def __init__(self, tool_manager) -> None:
        self.tool_manager = tool_manager
        self.error_info = ErrorInfo()
        self.opt_map = {}

    async def async_invoke(self, action: Node):
        tool_name = action.toolname
        args = action.input
        res = self.tool_manager.executor_call(tool_name, args)
        return res

    def invoke(self, action: Node, llm):
        tool_name = action.toolname
        args = action.input
        res = self.tool_manager.executor_call(tool_name, args, llm=llm)
        # 统一为api call
        # res = self.tool_manager.api_call(tool_name, args)
        return res

    def check_valid_sop(self, sop_dict):
        res = self.check_func_param(sop_dict)
        err_str = ""
        cnt = 1
        for key, value in res.items():
            err_str = err_str + \
                f"{cnt}. 步骤{str(key)}的生成存在以下几个问题：\n" + "\n".join(value) + "\n"
            cnt += 1
        if len(err_str) > 0:
            logger.error(err_str)
        return err_str

    def invalid_input(self, operation_name, key, tool_name):
        api = self.tool_manager.get_api_by_name(tool_name)
        if api is None:
            message = ERROR_MAP[ErrorType.INVALID_TOOL_ERROR].format(
                toolname=tool_name)
            logger.error(message)
            self.error_info.add(operation_name, message)
            return False
        input_parameters = self.tool_manager.get_api_by_name(tool_name)[
            'input_parameters']
        if key not in input_parameters:
            # 输入多余参数
            message = ERROR_MAP[ErrorType.INVALID_INPUT_PARAM].format(
                params=key, tool=tool_name)
            logger.error(message)
            self.error_info.add(operation_name, message)
        return True

    def invalid_output(self, operation_name, key, tool_name):
        api = self.tool_manager.get_api_by_name(tool_name)
        if api is None:
            return False
        output_parameters = self.tool_manager.get_api_by_name(tool_name)[
            'output_parameters']
        if key not in output_parameters:
            message = ERROR_MAP[ErrorType.INVALID_OUPUT_PARAM].format(
                params=key, tool=tool_name)
            self.error_info.add(operation_name, message)
            logger.error(message)
        return True

    def check_func_param(self, operations):
        self.opt_map = {}
        for operation in operations:
            self.init_operation_dict(operation)

        for operation in operations:
            self.check_operation_args(operation)
        return self.error_info.store

    def check_operation_args(self, operation):
        operation_name = operation['name']
        inputs = operation.get('input', {})
        tool_name = operation.get('toolname', '')
        dependency = operation.get('dependency', [])
        self.check_invalid_dependency(operation_name, dependency)
        if isinstance(inputs, dict):
            for key, param in inputs.items():
                if param is None:
                    continue
                if not self.invalid_input(operation_name, key, tool_name):
                    break
                holders = re.findall(r'\$\{([^}]*)\}', str(param))
                self.check_invalid_placeholder(
                    operation_name, holders, dependency)

    def init_operation_dict(self, operation):
        required_keys = {'name', 'toolname'}
        # 检查字典中是否包含所有必要的键, 没看懂
        necessary = True
        name = operation['name']
        for key in required_keys:
            if key not in operation:
                necessary = False
                message = ERROR_MAP[ErrorType.NO_NAME_ERROR]
                self.error_info.add(operation.get('name', 'None'), message)
                logger.error(message)

        if name in self.opt_map.keys():
            message = ERROR_MAP[ErrorType.NODE_CONFILCT_ERROR].format(
                name=name)
            self.error_info.add(name, message)
            logger.error(message)
            necessary = False
        if not necessary:
            return
        self.opt_map[name] = operation

    def check_invalid_dependency(self, operation_name, dependency):
        for dep in dependency:
            if dep is None:
                continue
            if len(dep) == 0:
                continue
            if dep not in self.opt_map.keys():
                message = ERROR_MAP[ErrorType.INVALID_DEPENDENCY].format(
                    node=dep)
                self.error_info.add(operation_name, message)
                logger.error(message)

    def check_invalid_placeholder(self, operation_name, holders, dependency):
        for _, holder in enumerate(holders):
            keys = holder.split('.')
            holder_name = keys[0]
            key_name = keys[1]
            opt = self.opt_map.get(holder_name)
            if holder_name not in dependency:
                message = ERROR_MAP[ErrorType.NODE_NOT_DEPENDENT].format(
                    node=holder_name)
                self.error_info.add(operation_name, message)
                logger.error(message)
                self.invalid_output(operation_name, key_name, opt['toolname'])


class ErrorInfo:
    def __init__(self) -> None:
        self.store = {}

    def add(self, operation, error):
        err_list = self.store.get(operation, [])
        err_list.append(error)
        self.store[operation] = err_list
