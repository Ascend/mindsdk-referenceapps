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

from dataclasses import dataclass
from typing import Any, Dict, Type

from rllm.agents.agent import BaseAgent
from rllm.environments import BaseEnv
from rllm.rewards.reward_fn import math_reward_fn

from examples.agents.math_agent.math_agent import MathAgent
from examples.agents.math_agent.math_env import MathEnvironment
from examples.agents.websearcher.websearcher_agent import WebSearcherAgent
from examples.agents.websearcher.websearcher_env import WebSearcherEnvironment
from examples.agents.websearcher.rewards.reward_fn import websearcher_reward_fn


@dataclass(frozen=True)
class AgentConfig:
    """
    Configuration for a reinforcement learning agent and its environment.

    This dataclass holds the complete information needed to instantiate 
    an agent and its corresponding environment.

    Raises:
        TypeError: If any of the provided classes or arguments are of incorrect type.
    """
    name: str
    agent_class: Type[BaseAgent]
    agent_args: Dict[str, Any]
    env_class: Type[BaseEnv]
    env_args: Dict[str, Any]

    def __post_init__(self) -> None:
        """Validate the configuration after initialization."""
        self._validate_config()

    def _validate_config(self) -> None:
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

# Predefined math agent configurations
MATH_AGENT_CONFIG = AgentConfig(
    name="math",
    agent_class=MathAgent,
    agent_args={
        "tools": ["python"],
        "parser_name": "qwen",
        "system_prompt": "You are a math assistant that can write Python code to solve math problems. "
                         "When you provide the final answer, ensure it is wrapped in the LaTeX syntax: \\boxed{final_answer}. "
                         "For example, if the answer is 42, you should write \\boxed{42}. "
                         "Important: Only execute safe, mathematical computations. Do not perform file operations, network requests, "
                         "or any other potentially harmful actions.",
    },
    env_class=MathEnvironment,
    env_args={
        "tools": ["python"],
        "reward_fn": math_reward_fn,
    },
)

from openai import OpenAI
client = OpenAI(base_url="https://url/v1", api_key="sk-xxxx")
WEBSEARCHER_AGENT_CONFIG = AgentConfig(
    name="websearcher",
    agent_class=WebSearcherAgent,
    agent_args={
        "memory_config": {
            "simplify_thinking": False,
            "use_summary": False,
            "max_summary_length": 1024,
            "max_prompt_length": 8192,
            "before_raw_message": 2,
            "end_raw_message": -2,
            "train_model_tokenizer_path": "/path/to/tokenizer",
            "oai_client": client,
            "oai_model_name": "qwen2.5-7b-instruct",
        }
    },
    env_class=WebSearcherEnvironment,
    env_args={
        "reward_fn": websearcher_reward_fn,
        "max_tool_length": 4096,
        "search_url": "http://127.0.0.1:11101/",
        "tokenizer_path": "/path/to/tokenizer",
        "search_mode": "local",
        "max_step": 128
    },
)
