# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.
# Copyright (c) 2023 Sehoon Kim
from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, List, Optional

from utils.log import LOGGER


@dataclass
class Task:
    idx: int
    name: str
    tool: Callable
    args: Collection[Any]
    dependencies: Collection[int]  # 依赖的任务 idx
    condition: str  # 执行分支条件

    observation: Optional[str] = None
    is_join: bool = False

    async def __call__(self) -> Any:
        LOGGER.info("running task")
        x = await self.tool(*self.args)
        LOGGER.info("done task")
        return x

    def get_though_action_observation(
        self, include_action=True, include_thought=True, include_action_idx=False
    ) -> str:
        thought_action_observation = ""
        if self.thought and include_thought:
            thought_action_observation = f"Thought: {self.thought}\n"
        if include_action:
            idx = str(self.idx) + ". " if include_action_idx else ""
            if self.stringify_rule:
                # If the user has specified a custom stringify rule for the
                # function argument, use it
                thought_action_observation += f"{idx}{self.stringify_rule(self.args)}\n"
            else:
                # Otherwise, we have a default stringify rule
                thought_action_observation += (
                    f"{idx}{self.name}"
                    # f"{_default_stringify_rule_for_arguments(self.args)}\n"
                )
        if self.observation is not None:
            thought_action_observation += f"Observation: {self.observation}\n"
        return thought_action_observation
