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

from typing import Any

from langchain_core.messages import AIMessage
from rllm.agents.agent import Action, Step

from examples.agents.websearcher.websearcher_tool_parser import WebSearcherToolParser
from examples.agents.websearcher.websearcher_tools import websearcher_tools
from examples.agents.websearcher.websearcher_agent import WebSearcherAgent
from agentic_rl.base.log.loggers import Loggers

logger = Loggers(__name__)


class LangGraphWebSearchAgent(WebSearcherAgent):
    def __init__(self, memory_config: dict = None):
        super().__init__(memory_config)

    def update_from_env(self, observation: Any, reward: float, done: bool, info: dict):
        """
        Updates the agent's internal state based on environment feedback.

        Args:
            observation (Any): The observation received from the environment.
            reward (float): The reward received from the environment.
            done (bool): Whether the episode is done.
            info (dict): Additional information from the environment.
        """
        messages = []
        if isinstance(observation, dict) and "problem" in observation:
            messages.append({"role": "user", "content": observation["problem"]})
        elif observation is not None:
            messages.append({"role": "user", "content": str(observation)})
        else:
            raise ValueError("Empty observation received.")
        self.memory.add_message(messages, metadata=[{"reward": reward}])
        self._current_observation = observation
