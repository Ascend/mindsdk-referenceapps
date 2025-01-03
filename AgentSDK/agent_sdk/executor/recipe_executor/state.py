# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from typing import List
import json


class Node:
    def __init__(
            self,
            node_id: int,
            in_nodes: List = None,
            out_nodes: List = None,
            is_terminated: bool = False,
            is_finished: bool = False,
            role: str = None,
            thought: str = None,
            function_call: str = None,
            ori_query: str = None
    ):
        self._node_id = node_id
        self._in_nodes = in_nodes if in_nodes else []
        self._out_nodes = out_nodes if out_nodes else []
        self._is_terminated = is_terminated
        self._is_finished = is_finished
        self._role = role
        self._thought = thought
        self._function_call = function_call
        self._ori_query = ori_query


class ExecutorState:

    def __init__(self, query: str = None, functions: List = None,
                 restored_node_list: List = None):
        self._query = query
        self._functions = functions
        self._max_node_id = 0
        self._node_ids = []
        self._start = Node(node_id=self._max_node_id, role="start")
        self._dealing_node = self._start
        self._is_finished = False
        self._report_message = None
        self._chains: dict = dict()
        self._restored_node_list = restored_node_list if restored_node_list else []

        self.remaining_tasks = set()
        self.activated_tasks = set()
        self.done_tasks = set()
        self.activate_actions = []
        self.leaves_tasks = [] # 图中所有的叶子节点
        self.start_node_id = None # 开始节点

        # for sop planning type
        self.init_query = ""
        self.sop_graph = None
        self.workspace = None
        self.smart_selection_target_name = None
        self.wait_user_sop_selection = ""
        self.sop_functions = None
        self.wait_user_input = False
        self.wait_user_input_askuser = False
        self.wait_user_feedback = False
        self.wait_user_feedback_plugin = False
        self.wait_user_plugin_result = False
        self.stop_current_chat = False

        self.plugin_result = None
        self.llm_response = None
        self.validate = None


class WorkSpace:
    def __init__(self,
                 operation_history,
                 variable_space):
        self.operation_history = operation_history
        self.variable_space = variable_space # 记录执行结果，workspace[node_name]的值正常是一个json，由[out_param]指定某一个具体的参数值
        self.last_operation = ""

    def update(self, history):
        self.operation_history.append(history)

    def retrive_variable(self, operations, argument):
        result = [
            self.variable_space[key1][argument]
            for key1 in operations
            if key1 in self.variable_space and argument in self.variable_space[key1]
            ]
        result = result[0] if result else []
        return result

    def map_keys(self, input_dict, mapping):
        mapped_dict = {}
        for key, value in input_dict.items():
            mapped_key = mapping.get(key, key)
            if isinstance(value, dict):
                mapped_dict[mapped_key] = self.map_keys(value, mapping)
            else:
                mapped_dict[mapped_key] = value
        return mapped_dict

    def update_last_operation(self, operation):
        self.last_operation = operation

    def get_last_result(self):
        name = self.last_operation
        result = self.variable_space.get(name, "")
        ans = ""
        if isinstance(result, dict):
            for _, val in result.items():
                if not isinstance(val, str):
                    val = json.dumps(val, ensure_ascii=False)
                if val:
                    ans += val + '\n'
            return ans

        if result is None or len(result) == 0:
            for key, value in self.variable_space.items():
                if value is not None and len(value) > 0:
                    ans += f"{key}: {str(value)}\n"
        return ans
