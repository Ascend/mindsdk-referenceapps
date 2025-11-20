"""
Copyright 2025 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Agent configurations for reinforcement learning agents.

This module defines agent configurations, custom agent classes, and 
validation for different types of reinforcement learning agents.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from rllm.agents.agent import BaseAgent
from rllm.agents.system_prompts import TOOL_SYSTEM_PROMPT
from rllm.agents.tool_agent import ToolAgent as _ToolAgent
from rllm.environments import BaseEnv
from rllm.environments.tools.tool_env import ToolEnvironment as _ToolEnvironment
from rllm.rewards.reward_fn import math_reward_fn
from rllm.tools.tool_base import Tool
from rllm.agents.agent import Trajectory

logger = logging.getLogger(__name__)


class ToolEnvironment(_ToolEnvironment):
    """Custom Tool Environment for Tool Agents."""
    def __init__(
        self,
        task: Dict[str, Any],
        tools: Optional[List[str]] = None,
        tool_map: Optional[Dict[str, Type[Tool]]] = None,
        reward_fn: Optional[Any] = None,
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
    def from_dict(env_args: dict) -> "ToolEnvironment":
        """Create a ToolEnvironment from a dictionary of arguments."""
        task = env_args.pop("task", {})
        tools = env_args.pop("tools", None)
        tool_map = env_args.pop("tool_map", None)
        reward_fn = env_args.pop("reward_fn", None)
        max_steps = env_args.pop("max_steps", 10)
        return ToolEnvironment(task=task, tools=tools, tool_map=tool_map,
                               reward_fn=reward_fn, max_steps=max_steps)
    

class ToolAgent(_ToolAgent):
    """
    Tool-enabled Agent with trajectory tracking for Reinforcement Learning.

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
        Initialize the tool agent.

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


@dataclass(frozen=True)
class AgentConfig:
    """
    Configuration for a reinforcement learning agent and its environment.

    This dataclass holds the complete information needed to instantiate 
    an agent and its corresponding environment.

    Raises:
        TypeError: If any of the provided classes or arguments are of incorrect type.
    """
    agent_class: Type[BaseAgent]
    agent_args: Dict[str, Any]
    env_class: Type[BaseEnv]
    env_args: Dict[str, Any]

    def __post_init__(self) -> None:
        """Validate the configuration after initialization."""
        self._validate_confit()

    def _validate_confit(self) -> None:
        if not issubclass(self.agent_class, BaseAgent):
            raise TypeError(f"agent_class must be a subclass of BaseAgent, got {self.agent_class.__name__}")
        if not issubclass(self.env_class, BaseEnv):
            raise TypeError(f"env_class must be a subclass of BaseEnv, got {self.env_class.__name__}")
        if not isinstance(self.agent_args, dict):
            raise TypeError(f"agent_args must be a dictionary, got {type(self.agent_args).__name__}")
        if not all(isinstance(key, str) for key in self.agent_args.keys()):
            raise ValueError("All keys in agent_args must be strings.")
        if not isinstance(self.env_args, dict):
            raise TypeError(f"env_args must be a dictionary, got {type(self.env_args).__name__}")
        if not all(isinstance(key, str) for key in self.env_args.keys()):
            raise ValueError("All keys in env_args must be strings.")
        
        if "system_prompt" in self.agent_args:
            if not isinstance(self.agent_args["system_prompt"], str):
                raise TypeError(f"system_prompt must be a string, got {type(self.agent_args['system_prompt']).__name__}")
            if not self.agent_args["system_prompt"].strip():
                raise ValueError("system_prompt cannot be an empty string.")

# Sytem prompts with security considerations
MATH_SYSTEM_PROMPT = (
    "You are a math assistant that can write Python code to solve math problems. "
    "When you provide the final answer, ensure it is wrapped in the LaTeX syntax: \\boxed{final_answer}. "
    "For example, if the answer is 42, you should write \\boxed{42}. "
    "Important: Only execute safe, mathematical computations. Do not perform file operations, network requests, "
    "or any other potentially harmful actions."
)

# Predefined math agent configurations
MATH_AGENT_CONFIG = AgentConfig(
    agent_class=ToolAgent,
    agent_args={
        "tools": ["python"],
        "parser_name": "qwen",
        "system_prompt": MATH_SYSTEM_PROMPT,
    },
    env_class=ToolEnvironment,
    env_args={
        "tools": ["python"],
        "reward_fn": math_reward_fn,
    },
)
