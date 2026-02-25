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
"""

import numpy as np

def compute_trajectory_reward(trajectory):
    """
    Add trajectory reward to the dict of each interaction.

    Args:
        trajectory: List of dictionaries representing each step in the trajectory.

    Returns:
        The updated trajectory with trajectory_reward added to each step.
    """
    if not trajectory:
        return trajectory

    toolcall_rewards = [d.reward for d in trajectory.steps if not d.done]
    toolcall_reward = np.mean(toolcall_rewards) if toolcall_rewards else 0

    res_rewards = [d.reward for d in trajectory.steps if d.done]
    if res_rewards:
        res_reward = res_rewards[-1]
    else:
        res_reward = -2

    trajectory.toolcall_reward = toolcall_reward
    trajectory.res_reward = res_reward
    trajectory.reward = toolcall_reward + res_reward
    return trajectory