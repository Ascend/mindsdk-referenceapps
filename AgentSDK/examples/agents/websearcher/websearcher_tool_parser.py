"""
Copyright 2026 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json

from rllm.tools.tool_base import ToolCall
from rllm.parser.tool_parser.qwen_tool_parser import QwenToolParser


class WebSearcherKeyword(enumerate):
    PARSE_DONE = "done"
    PARSE_TOOL_ERROR = "error occurred while parsing tool call"
    ANSWER_PATTERN = r'\\boxed\{(.*?)\}'

    ZH_COLON = "："
    EN_COLON = ":"
    ZH_COMMA = "，"
    EN_COMMA = ","


class WebSearcherToolParser(QwenToolParser):
    def parse(self, model_response: str) -> list[ToolCall]:
        """Parse tool calls from model output.

        Args:
            model_output (str): Text containing tool calls

        Returns:
            ToolInputs: Parsed tool calls
        """
        tool_call = self.parse_qwen_tool_calls(model_response)
        if tool_call:
            return ToolCall(name=tool_call["name"], arguments=tool_call["arguments"])
        else:
            return None

    def parse_qwen_tool_calls(self, text: str):
        try:
            if not (self.tool_call_begin in text and self.tool_call_end in text):
                return {}
            
            start_pos = text.find(self.tool_call_begin) + len(self.tool_call_begin)
            end_pos = text.find(self.tool_call_end)
            content = text[start_pos: end_pos].strip()

            json_start = content.find('{')
            if json_start == -1:
                raise Exception
            
            json_str = content[json_start:]
            decoder = json.JSONDecoder()
            tool_call, _ = decoder.raw_decode(json_str)
            tool = tool_call.get('name', '')
            query = tool_call.get('arguments', {})
            if not isinstance(tool, str):
                tool = ''
            if not isinstance(query, dict):
                query = {}
            return {"name": tool, "arguments": query}
        except Exception:
            return {"name": "error_tool", "arguments": {"response": WebSearcherKeyword.PARSE_TOOL_ERROR}}
        
    def get_tool_prompt(self, tools_schema: str):

        return """You are a helpful AI assistant that must strictly follow all rules below.

====================
Reasoning
====================
- All internal reasoning MUST be enclosed within <think>...</think>.
- The content inside <think> is internal and not part of the final answer.
- The Assistant MUST NOT reveal or summarize its internal reasoning.
- If no reasoning is needed, the Assistant MAY output an empty <think></think>.

====================
Search Tool Usage
====================
- The Assistant MAY use the search tool ONLY when the question cannot be answered using general knowledge.
- The Assistant MUST NOT assume, fabricate, or hallucinate search results.
- The Assistant MUST issue a search request by emitting a <tool_call> JSON.
- Search results are PROVIDED BY THE SYSTEM after a <tool_call>.
- The Assistant MUST NOT generate <tool_response> tags or their contents under any circumstances.
- The Assistant SHOULD minimize the number of search calls.
- The Assistant MUST NOT issue repeated or semantically equivalent search queries.

====================
Available Tools
====================
<tools>
%s
</tools>

====================
Tool Call Format
====================
<tool_call>
{"name": "search", "arguments": {"query": ["query1", "query2"]}}
</tool_call>

====================
Answering Rules
====================
- After zero or more search calls, the Assistant MUST provide the final answer.
- The final answer MUST be enclosed within \\boxed{}.
- If there are multiple answers, they MUST be enclosed in a single \\boxed{}, separated by commas.
  Example: \\boxed{answer 1, answer 2}
- If the question is invalid or cannot be answered with the available information, reply with:
  \\boxed{the question is invalid.}

====================
Output Constraints
====================
- The Assistant MUST NOT output anything outside <think>, <tool_call>, or \\boxed{}.
- Any output that violates the above rules is considered incorrect.
""" % tools_schema