# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from collections import OrderedDict
import re
from loguru import logger


class Node:
    def __init__(self,
                 name,
                 content,
                 prompt,
                 step,
                 output,
                 activate,
                 strategy,

                 toolname,

                 dependency,
                 ):
        self.step = step
        self.name = name
        self.input = content
        self.prompt = prompt
        self.activate = activate
        self.strategy = strategy
        self.dependency = dependency
        self.output = output
        self.toolname = toolname


class Parser:
    def __init__(self, sop_dict=None):
        self.sop_dict = sop_dict

    @staticmethod
    def construct_graph(nodes):
        graph = OrderedDict()
        for operation in nodes:
            operation = Node(name=operation['name'],
                             step=operation['step'],
                             content=operation['input'],
                             prompt=operation['prompt'],
                             toolname=operation['toolname'],
                             dependency=operation['dependency'],
                             output=operation["output"],
                             strategy=operation["strategy"],
                             activate=operation["activate"])
            graph[operation.name] = operation
        return graph

    def parse(self, raw_dict):
        nodes = []
        for operation in raw_dict:
            node = {
                "step": None,
                "name":  None,
                "goal":  None,
                "input": None,      # 输入
                "prompt": None,     # llm的prompt
                "activate": None,   # 执行引擎，表达式验证规则
                "toolname": None,
                "validation": None,  # 校验结果
                "output": None,     # 执行完成后赋值 dict类型
                "strategy": None,
                "dependency": set(),  # 依赖节点
                "err_msg": None,
                "err_code": None
            }
            for key in operation:
                node[key] = operation[key]
                if key == 'dependency':
                    # 过滤none
                    node[key] = [item for item in operation[key] if item is not None]
            if not node['prompt']:
                node['prompt'] = "当前任务：[{{Operation.name}}]，相关参数信息如下：{{Operation.input}}"
            nodes.append(node)

        operations = self.construct_graph(nodes)  # graph
        return operations

    def walk_strings(self, inputs, output=None):
        if output is None:
            output = set()
        regex = re.compile(r'\$v\{(.+?)\.output')
        if isinstance(inputs, str):
            match = regex.search(inputs)
            if match:
                output.add(match.group(1))
        elif isinstance(inputs, list):
            for element in inputs:
                try:
                    self.walk_strings(element, output)
                except TypeError as e:
                    raise e
        elif isinstance(inputs, dict):
            for value in inputs.values():
                try:
                    self.walk_strings(value, output)
                except TypeError as e:
                    raise e
        else:
            raise TypeError("Invalid inputs type")
        return output

    


class ActionGraph:
    def __init__(self, actions) -> None:
        self.actions = actions
        if len(actions) == 0:
            self.start_node_id = 0
        else:
            self.start_node_id = actions[next(iter(actions))]
