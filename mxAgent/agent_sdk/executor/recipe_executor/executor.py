# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from typing import Dict
import asyncio
import time
import re
import traceback
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
from loguru import logger

from agent_sdk.executor.recipe_executor.state import ExecutorState, WorkSpace
from agent_sdk.executor.recipe_executor.parser import Node, Parser, ActionGraph
from agent_sdk.executor.recipe_executor.sop import SopHandler
from agent_sdk.executor.common import ERROR_MAP, ErrorType, PlanStrategyType

ALL_PLAN_STRATEGIES = {
    PlanStrategyType.SOP.value: "sop"
}


class AgentExecutor():
    tasks_done: Dict[str, asyncio.Event]

    def __init__(
        self,
        tool_manager,
        plan_strategy_type: PlanStrategyType = None,
    ):
        self.plan_strategy_type = plan_strategy_type or PlanStrategyType.SOP
        self.plan_strategy = ALL_PLAN_STRATEGIES.get(
            self.plan_strategy_type.value)
        self.parser = Parser()
        self.tool_manager = tool_manager
        self.operation_handler = SopHandler(tool_manager)
        self.lock = threading.Lock()
    
    @staticmethod
    def parser_output(output, cur_operation):
        content = output
        if isinstance(output, str):
            try:
                content = json.loads(output)
            except json.JSONDecodeError:
                content = output
        else:
            content = output
        cur_operation.output = content
        history = {
            "operation_name": cur_operation.name,
            "dependecy": cur_operation.dependency,
            "input": cur_operation.input,
            "output": content,
            "activate": cur_operation.activate,  # 激活该分支的条件
            "interaction_history": "",  # discuss
            "variable_space": ""  # discuss
        }
        cur_operation.history = history
        return content, history

    @staticmethod
    def update_history(result, executor_state):
        name = result['action']
        parsed_out = result['output']
        history = result['history']
        executor_state.workspace.variable_space[name] = parsed_out
        executor_state.workspace.update(history)
        # 执行完毕，从set中移除
        executor_state.remaining_tasks.remove(name)
        executor_state.activated_tasks.remove(name)
        executor_state.done_tasks.add(name)
        executor_state.workspace.update_last_operation(name)

    @staticmethod
    def process_action_args(action: Node, executor_state):
        # 处理参数依赖的替换
        history_names = [history["operation_name"]
                         for history in executor_state.workspace.operation_history]
        # if any of a node's previous actions has no input
        # ie. this node's previous operation name not in history, this node cannot execute, so pass
        if not set(action.dependency).issubset(set(history_names)):
            raise Exception("dependency action hasn't executed")
        node = action
        if node.activate:
            # 用表达引擎,执行看是否满足准入要求
            node.activate = sub_placeholder(
                node.activate, executor_state.workspace)
            bool_activate = expression_engine(node.activate)

            if not bool_activate:
                raise Exception("action hasn't activate")

        if action.input:
            for key, value in action.input.items():
                if value is None:
                    logger.warning('the value of [%s] is None', key)
                else:
                    value = sub_placeholder(value, executor_state.workspace)
                action.input[key] = value
        return action
    
    def get_executable_actions(self, executor_state):
        done_actions = executor_state.done_tasks
        graph = executor_state.sop_graph.actions
        activated = executor_state.activated_tasks
        independent_actions = [
            task_name
            for task_name in executor_state.remaining_tasks
            if all(
                d in done_actions for d in graph[task_name].dependency
            )
        ]
        executable_actions = []
        pending_actions = []
        for action in independent_actions:
            node = graph[action]
            if node.activate:
                node.activate = sub_placeholder(
                    node.activate, executor_state.workspace)
                if not node.activate:
                    break
                bool_activate = expression_engine(node.activate)

                if not bool_activate:
                    executor_state.remaining_tasks.remove(action)
                    executor_state.done_tasks.add(action)
                    continue
            executable_actions.append(action)

            if action in activated:
                continue
            try:
                node = self.process_action_args(node, executor_state,)
            except Exception as e:
                continue
            if node is not None:
                pending_actions.append(node)
            else:
                continue
        return pending_actions

    def run_task(self, action, executor_state, llm):
        graph = executor_state.sop_graph.actions
        sop_handler = self.operation_handler
        mommt = time.time()
        logger.debug(f'{action.name} start:{mommt}')
        output = sop_handler.invoke(action, llm=llm)

        parsed_out, history = self.parser_output(output, action)
        graph[action.name].output = parsed_out

        res = {
            "action": action.name,
            "output": parsed_out,
            "history": history
        }

        mommt = time.time()
        logger.debug(f'step {action.step}. action: {action.name} has finished')
        return res



    def async_run(self, content, llm):
        executor_state = self.init_state(content)
        executor = ThreadPoolExecutor(max_workers=5)
        with ThreadPoolExecutor(max_workers=5) as executor:
            while executor_state.remaining_tasks:  # 活跃的
                executable_tasks = self.get_executable_actions(executor_state)
                thread_list = []
                for task in executable_tasks:
                    th = executor.submit(self.run_task, task, executor_state, llm)
                    thread_list.append(th)
                    executor_state.activated_tasks.add(task.name)
                    # todo 某个task执行失败，会被保留，循环
                for future in as_completed(thread_list):
                    with self.lock:
                        self.update_history(future.result(), executor_state)
        return executor_state.workspace.get_last_result()

    # 而此处的写法不关注next，关注dependency
    def run(self, content):
        executor_state = self.init_state(content)

        sop_handler = self.operation_handler
        activate_actions = self.get_executable_actions(executor_state)
        executor_state.activate_actions = activate_actions
        while executor_state.activate_actions:  # 活跃的

            cur_operation = executor_state.activate_actions.pop(
                0)  # starts from right
            mommt = time.time()
            logger.error("start run step %d, action [%s]", cur_operation.step, cur_operation.name)
            output = sop_handler.invoke(cur_operation)
            parsed_out, history = self.parser_output(output, cur_operation)
            executor_state.workspace.update(history)
            # 保存结果
            executor_state.workspace.variable_space[cur_operation.name] = parsed_out
            executor_state.workspace.update_last_operation(
                cur_operation.name)  
            # 更新状态
            executor_state.remaining_tasks.remove(cur_operation.name)
            executor_state.done_tasks.add(cur_operation.name)
            executable_actions = self.get_executable_actions(executor_state)
            executor_state.activate_actions = (executable_actions)

        return executor_state.workspace.get_last_result()

    def check_valid(self, content):
        if not isinstance(content, str):
            return False, ERROR_MAP[ErrorType.INPUT_NOT_STR]
        absolute_path = os.getcwd()
        if os.path.isfile(os.path.join(absolute_path, content)):
            raw_dict, err = fetch_file_content(content)
        else:
            raw_dict, err = fetch_str_content(content)
        if len(err) > 0:
            return False, err
        err = self.operation_handler.check_valid_sop(raw_dict)
        return len(err) == 0, err

    def init_state(self, content):
        if not isinstance(content, str):
            raise TypeError("Invalid arguements type: the content need a str")
        absolute_path = os.getcwd()
        if os.path.isfile(os.path.join(absolute_path, content)):
            raw_dict, err = fetch_file_content(content)
        else:
            raw_dict, err = fetch_str_content(content)

        filter_opt = []
        for operation in raw_dict:
            operation_name = operation['toolname']
            api = self.tool_manager.get_api_by_name(operation_name)
            if api is not None:
                filter_opt.append(operation)
        operations = self.parser.parse(raw_dict=filter_opt)

        execute_state = ExecutorState()
        workspace = WorkSpace(operation_history=[], variable_space={})
        graph = ActionGraph(operations)

        execute_state.workspace = workspace
        execute_state.sop_graph = graph
        execute_state.remaining_tasks = {k for k, _ in graph.actions.items()}
        return execute_state


def fetch_str_content(content):
    start_identify = "```yaml"
    end_identify = "```"
    start = content.find(start_identify)
    end = content.rfind(end_identify)
    if start != -1 and end != -1:
        content = content[start + len(start_identify): end]
    try:
        code_seg = content.strip("\n").split("\n")
        while code_seg[0] == start_identify:
            code_seg.pop(0)
        while code_seg[-1] == end_identify:
            code_seg.pop()
        data = yaml.safe_load("\n".join(code_seg))
    except yaml.YAMLError as e:
        logger.error(f"生成yaml代码块错误：{str(e)}")
        return [], ERROR_MAP[ErrorType.YAML_LOAD_ERROR]
    return data, ''


def fetch_file_content(file_path):
    # 获取文件扩展名
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.yaml':
        try:
            with open(file_path, 'r') as file:
                yaml_content = yaml.safe_load(file)
            return yaml_content, ''
        except Exception as e:
            msg = ERROR_MAP[ErrorType.FILE_READ_ERROR].format(
                filename=file_path, error=e)
            logger.error(msg)
            return [], msg
    elif file_extension == '.json':
        try:
            with open(file_path, 'r') as file:
                json_content = json.load(file)
            return json_content, ''
        except Exception as e:
            msg = ERROR_MAP[ErrorType.FILE_READ_ERROR].format(
                filename=file_path, error=e)
            logger.error(msg)
            return [], msg
    else:
        msg = ERROR_MAP[ErrorType.FILE_TYPE_ERROR].format(filename=file_path)
        logger.error(msg)
        return [], msg


def sub_placeholder(expression, workspace, output=None):
    # 考虑输入参数可能是数字
    expression = str(expression)

    def replace(match):
        keys = match.group(1).split('.')
        operation_name = keys[0]
        key_name = keys[1]

        if output:
            return str(output.get(keys, keys))
        else:
            history = workspace.variable_space.get(operation_name)
            if isinstance(history, dict):
                val = str(history.get(key_name, ''))
                return val
            # todo  容易down
            return "no value"

    def valid_checking(result, expression):
        result = str(result)
        if result == expression.replace("{", "").replace("}", "") and "{" in expression and "}" in expression:
            return True
        return False

    try:
        # 匹配exp中占位的子串，并作为参数，传入replace，进行替换
        result = re.sub(r'\$\{([^{^}]*)\}', replace, expression)
        if valid_checking(result, expression):
            result += "\n [提示]：系统分析您的问题失败，原因可能是: \n①plugin调用不成功" \
                "\n②LLM参数解析失败，\n③SOP字段配置错误。\n您可以尝试再次输入或者调整您的问题"
        return result
    except TypeError as e:
        logger.error(e)
        return ""


def expression_engine(expression):
    '''
    输入文字表达，返回boolean表达
    '''
    expression = expression.replace("\n", '')
    if " 属于 " in expression:
        expression = expression.replace(" 属于 ", ".issubset(") + ')'
    else:  # TODO：更多规则
        pass
    res = True
    try:
        res = bool(eval(expression))
    except Exception:
        res = False

    return res


async def arun_and_time(func, *args, **kwargs):
    """helper function to run and time a function.
    Since function can error, we catch the error and return "ERROR" as the result
    """
    start = time.time()
    try:
        result = await func(*args, **kwargs)
    except Exception as e:
        logger.error(e)
        traceback.print_exc()
        result = "ERROR"
    end = time.time()
    return result, end - start
