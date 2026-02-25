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

from typing import Dict, List, Optional, Type

from rllm.agents.system_prompts import TOOL_SYSTEM_PROMPT
from rllm.agents.tool_agent import ToolAgent as _ToolAgent
from rllm.tools.tool_base import Tool
from rllm.agents.agent import Trajectory

class MathAgent(_ToolAgent):
    """
    Math-enabled Agent with trajectory tracking for Reinforcement Learning.

    Extends the base ToolAgent with enhanced trajectory management and
    proper state reset functionality.
    """
    def __init__(
        self,
        system_prompt: str = TOOL_SYSTEM_PROMPT,
        parser_name: str = "qwen",
        tools: Optional[List[str]] = None,
        tool_map: Optional[Dict[str, Type[Tool]]] = None,
    ) -> None:
        """
        Initialize the math agent.

        Args:
            system_prompt (str): The system prompt for the agent.
            parser_name (str): The name of the parser to use.
            tools (Optional[List[str]]): List of tool names available to the agent.
            tool_map (Optional[Dict[str, Type[Tool]]]): Mapping of tool names to tool classes.

        Raises:
            ValueError / TypeError: If any argument is invalid.
        """
        if not system_prompt or not isinstance(system_prompt, str):
            raise TypeError("system_prompt must be a non-empty string")
        if not parser_name or not isinstance(parser_name, str):
            raise TypeError("parser_name must be a non-empty string")
        if tools is not None and not isinstance(tools, list):
            raise TypeError("tools must be a list of strings if not None")
        if not all(isinstance(tool, str) for tool in tools or []):
            raise ValueError("Each tool in tools must be a string")
        if tool_map is not None and not isinstance(tool_map, dict):
            raise TypeError("tool_map must be a dictionary if not None")
        if not all(isinstance(key, str) and issubclass(value, Tool) for key, value in (tool_map or {}).items()):
            raise ValueError("tool_map must map strings to Tool subclasses")
        
        super().__init__(system_prompt=system_prompt, parser_name=parser_name,
                            tools=tools, tool_map=tool_map)
        
    def reset(self) -> None:
        """Reset the agent's internal state."""
        self._trajectory = Trajectory()
        self.messages = [
            {"role": "system", "content": self.system_prompt + (self.tools_prompt or "")}
        ]
