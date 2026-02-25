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

from typing import Any, Dict, List, Optional, Type

from rllm.environments.tools.tool_env import ToolEnvironment as _ToolEnvironment
from rllm.rewards.reward_fn import RewardFunction
from rllm.tools.tool_base import Tool

class MathEnvironment(_ToolEnvironment):
    """Custom Math Environment for Math Agents."""
    def __init__(
        self,
        task: Dict[str, Any],
        tools: Optional[List[str]] = None,
        tool_map: Optional[Dict[str, Type[Tool]]] = None,
        reward_fn: Optional[RewardFunction] = None,
        max_steps: int = 10,
    ) -> None:
        """
        Initialize the ToolEnvironment.

        Args:
            task (Dict[str, Any]): The task configuration.
            tools (Optional[List[str]]): List of tool names available in the environment.
            tool_map (Optional[Dict[str, Type[Tool]]]): Mapping of tool names to tool classes.
            reward_fn (Optional[Any]): Custom reward function for the environment.
            max_steps (int): Maximum number of steps per episode.

        Raises:
            ValueError / TypeError: If any argument is invalid.
        """
        if not isinstance(task, dict):
            raise TypeError("task must be a dictionary")
        if not all(isinstance(key, str) for key in task.keys()):
            raise ValueError("All keys in task must be strings")
        if tools is not None and not isinstance(tools, list):
            raise TypeError("tools must be a list of strings if not None")
        if not all(isinstance(tool, str) for tool in tools or []):
            raise ValueError("Each tool in tools must be a string")
        if tool_map is not None and not isinstance(tool_map, dict):
            raise TypeError("tool_map must be a dictionary if not None")
        if not all(isinstance(key, str) and issubclass(value, Tool) for key, value in (tool_map or {}).items()):
            raise ValueError("tool_map must map strings to Tool subclasses")
        if not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError("max_steps must be a positive integer")
        
        super().__init__(task=task, tools=tools, tool_map=tool_map,
                         reward_fn=reward_fn, max_steps=max_steps)
        
    @staticmethod
    def from_dict(env_args: dict) -> "MathEnvironment":
        """Create a MathEnvironment from a dictionary of arguments."""
        task = env_args.pop("task", {})
        tools = env_args.pop("tools", None)
        tool_map = env_args.pop("tool_map", None)
        reward_fn = env_args.pop("reward_fn", None)
        max_steps = env_args.pop("max_steps", 10)
        return MathEnvironment(task=task, tools=tools, tool_map=tool_map,
                               reward_fn=reward_fn, max_steps=max_steps)
    