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

from enum import Enum
from dataclasses import dataclass

class WebSearcherRewardStage(Enum):
    """
    Enum representing different stages of the web searcher reward calculation process.
    """
    # Reward stage for tool format check
    TOOLS_FORMAT = "TOOLS_FORMAT"
    
    # Reward stage for tool return check
    TOOLS_RETURN = "TOOLS_RETURN"

    # Reward stage for final reward calculation
    DONE = "DONE"


class WebSearcherResultDocs(Enum):
    """
    Enum representing possible evaluation results for web searcher response.
    
    This enum defines the standard response messages for evaluating the correctness of model responses 
    in the context of web searcher interactions.
    """
    CORRECT = "the model's response is completely correct"
    INCORRECT = "the model's response is incorrect"
    PARTIALLY_CORRECT = "the model's response is partially correct"
    RESPONSE_EMPTY = "the model's response is empty"
    GROUND_TRUTH_EMPTY = "the ground truth is empty"


@dataclass
class WebSearcherRewardFnConfig:
    """
    Configuration for web searcher reward function parameters.
    
    This dataclass holds the reward values used by the reward function
    at different stages of the web searching process.
    """
    # Step reward (used for reward calculation at each step)
    step_reward_i: float = 0.0

    # Intermediate process failure - format error
    format_reward_neg: float = -1.0

    # Intermediate process failure - successfully called but no results found
    format_reward_nofound: float = 0.0

    # Intermediate process failure - service issue or error
    format_reward_err: float = 0.0

    # Intermediate process success - successfully called and results found
    format_reward_pos: float = 1.0

    # Final result correct
    res_correct: float = 4.0

    # Final result incorrect
    res_incorrect: float = -2.0

    # Final result empty or format incorrect (no \boxed{} wrapping)
    res_null: float = -3.0