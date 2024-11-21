# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from abc import ABC
from typing import Generator, Union, List
from loguru import logger
import tiktoken

from agent_sdk.executor.recipe_executor.executor import AgentExecutor
from agent_sdk.agentchain.base_agent import BaseAgent, AgentRunResult


class RecipeAgent(BaseAgent, ABC):
    def __init__(self, llm, tool_list=None, recipe: str = "", max_steps=15, final_prompt="",
                 max_token_number=4096, max_context_len=14000, max_retries=3, **kwargs):
        super().__init__(llm, None, tool_list, max_steps,
                         max_token_number, max_context_len, max_retries, **kwargs)
        self.recipe = recipe
        self.reflect = False
        self.reflection_result = ""
        self.recipe_output = ""
        self.final_prompt = final_prompt
        self.encoding = tiktoken.get_encoding("gpt2")
        self.agent_executor = AgentExecutor(tool_manager=self.tool_manager)

    def run(self, query, stream=False, *args, **kwargs):
        self.query = query

        for key, value in kwargs.items():
            setattr(self, key, value)
        cur_step = 1
        self.finished = False
        while not self.finished and cur_step < self.max_steps:
            self.step()
            cur_step += 1
        if len(self.recipe_output) == 0:
            prompt = f"你的角色设定如此：{self.description}，请利用你自己的知识回答用户的问题，用户的问题如下：{query}"
        else:
            try:
                prompt = self._build_final_prompt(self.recipe_output)
            except Exception as e:
                logger.error(e)
                self.answer = self.recipe_output
            else:
                # prompt 是str类型
                self.answer = self.llm(
                    prompt, temperature=0.1, stop=[], stream=stream)
        if stream:
            return self.answer
        else:
            return AgentRunResult(query=self.query, answer=self.answer, scratchpad=self.scratchpad)

    def step(self):
        tools_usage = self.get_tool_usage()
        if not self.reflect:
            prompt = INIT_PROMPT.format(
                tools_usage=tools_usage, suggestion=SUGGESTION, pesuede_code=self.recipe, question=self.query)
            translation_result = self.llm(prompt=prompt, temperature=0.1, stop=[], max_tokens=self.max_token_number)
        else:
            prompt = INIT_PROMPT.format(tools_usage=tools_usage,
                                        suggestion=SUGGESTION,
                                        translation_result=translation_result,
                                        reflection=self.reflection_result,
                                        pesuede_code=self.recipe,
                                        question=self.query)
            translation_result = self.llm(prompt=prompt, temperature=0.1, stop=[
            ], max_tokens=self.max_token_number)

        valid, _ = self.agent_executor.check_valid(translation_result)
        if not valid:
            self.finished = True
            self.recipe_output = ""
            self.answer = ""
            return ""
        else:
            result = self._execute_recipe(translation_result, self.llm)
            self.finished = True
            self.recipe_output = result
            self.answer = result
            return result

    def get_tool_usage(self):
        return self.tool_desc_for_agent

    def _build_final_prompt(self, text, **kwargs) -> Union[List, str]:
        if self.final_prompt is None:
            raise Exception("final prompt is None error")
        else:
            max_input_token_num = self.max_token_number
            input_token_len = len(self.encoding.encode(text))
            prompt_len = len(self.encoding.encode(self.final_prompt))
            clip_text_index = int(
                len(text) * (max_input_token_num - prompt_len) / input_token_len)
            clip_text = text[:clip_text_index]
            pmt = self.final_prompt.format(text=clip_text)
            return pmt

    def _execute_recipe(self, recipefile, llm):
        answer = self.agent_executor.async_run(recipefile, llm)
        return answer

    def _build_agent_prompt(self, **kwargs):
        return self.prompt.format(query=self.query, text=self.text)

    def _parse_response(self, response) -> str | Generator:
        return response


INIT_PROMPT = """你是一个精通伪代码和YAML格式的高级程序员，擅长将一段文字描述的伪代码翻译成一个以YAML格式表示的有向无环图，有向无环图中的节点代表伪代码中的一个动作，
你只能选择**工具**段落中的工具，有向无环图的边代表动作之间的依赖关系。
伪代码位于**伪代码**段落，可以使用的工具位于**工具**段落。
你的任务是仔细阅读**伪代码**段落，将其翻译成一个以YAML格式表示的有向无环图，每一个步骤只能对应一个工具调用
**工具**
{tools_usage}
**伪代码**
{pesuede_code}

**输出格式**
【格式】：
- name：query_flight
step：1
description：XX
toolname: XX
input: {{}}
dependency: []
- name：XX
step：2，
description：XX
toolname: XX
input:
  flight_number: ${{query_flight.flight_number}}
dependency: 
  - query_flight
...

【参数】：
name：步骤名称，应该简洁明了，以英文输出，如有多个单词，单词间以'_'连接
step：步骤序号
description：步骤行为描述，清晰的描述本节点的功能，以中文输出
toolname：该步骤使用的工具名称，来源于**工具**段落中的工具的名称，你只能使用**工具**中提供的工具名，不允许自行添加工具
input: 本步骤对应工具的输入参数列表，每个参数由本工具的参数名称和输入值组成，输入值优先使用依赖节点的输出参数，需要满足二者参数含义的一致性，请不要自行给输入赋值
dependency: 改步骤依赖其他哪些步骤，字段内容为list，list中每个元素是依赖步骤的step值

在你翻译时，重点关注满足如下几个方面要求:
{suggestion}

用户输入的问题：
{question}

请注意：翻译结果不要通过//或者 /**/ 添加任何解释或注释，且严格遵循YAML格式
请开始："""

REFLECT_PROMPT = """你是一个精通伪代码和YAML格式的高级程序员，擅长将一段文字描述的伪代码，翻译成一个以YAML格式表示的有向无环图，有向无环图中的节点代表伪代码中的一个动作，
尽量使用**工具**段落中的工具，有向无环图的边代表动作之间的依赖关系。
伪代码位于**伪代码**段落，可以使用的工具位于**工具**段落。
你的任务是仔细分析**伪代码**段落，以及一个已经翻译出来的YAML格式表示的位于**翻译结果**段落的有向无环图，然后给出结构化的，严肃的，有价值的改进建议，
使得翻译更加准确的代表伪代码的逻辑。
**工具**
{tools_usage}
**伪代码**
{pesuede_code}
**翻译结果**
{translation}
在你写改进建议时，重点关注是否有可能改进如下几个方面:
{suggestion}
请按列表方式写出明确的、有价值的、结构化的改进建议. 每条建议应该写清楚属于哪个节点，哪个属性字段。仅写出改进建议，不用写出其他额外的逻辑或者解释性的内容。

用户输入的问题:
{question}

请开始：
"""

IMPROVE_PROMPT = """你是一个精通伪代码和YAML格式的高级程序员，擅长将一段文字描述的伪代码，翻译成一个以YAML格式表示的有向无环图，有向无环图中的节点代表伪代码中的一个动作，
尽量使用**工具**段落中的工具，有向无环图的边代表动作之间的依赖关系。
伪代码位于**伪代码**段落，可以使用的工具位于**工具**段落。
你的任务是仔细分析**伪代码**段落，以及一个已经翻译出来的YAML格式表示的位于**翻译结果**段落的有向无环图，根据**改进建议**段落的改进意见，编辑翻译结果，
使得翻译更加准确匹配伪代码的逻辑。
**工具**
{tools_usage}
**伪代码**
{pesuede_code}
**翻译结果**
{translation}
**改进建议**
{reflection}
在你改写翻译结果时，重点关注是否有可能改进如下几个方面:
{suggestion}
仅写出最新的翻译结果，不用写出其他额外的逻辑或者解释性的内容。
用户输入的问题:
{question}

请开始：
"""

SUGGESTION = """1. 翻译结果请严格按照YAML格式输出，不要添加任何注释
2. 翻译出的节点数量是否严格匹配伪代码中的步骤数量，每个步骤只能匹配一个能完成其需求的工具，
3. 不能将伪代码中的一个步骤划分翻译成多个节点，例如不要出现1.1,1.2等step
4. 每个节点的toolname字段必须准确，且是在**工具**段落中存在的
5. 每个节点的dependency字段必须准确，能匹配伪代码中的依赖关系逻辑，dependency的节点必须是存在的节点
6. 每个节点的input字段必须有参数，每个节点的input字段名务必准确，必须是工具有的参数名，input字段中的每个参数输入值必须且只能是具体值或者依赖节点的工具输出参数，
不要使用python代码或者其他表达式，
7. 每个节点的input字段的每个参数值，优先使用依赖节点的工具输出参数，若无法通过依赖得到可以问题中提取，若存在多个答案，请使用加号+隔开，
8. 【伪代码】的步骤：一个步骤只能翻译成一个对应的节点
9. 生成的内容请严格遵循YAML的语法和格式
"""
