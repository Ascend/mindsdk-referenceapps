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

import regex

def bool_mapping(s: str):
    """
    Maps the string respresentations of boolean values to natural language equivalents.

    Args:
        s (str): The string to be mapped.

    Returns:
        str: "yes" if the input is "True", "no" if the input is "False", otherwise the input string itself.
    """
    if s == "True" or s == "true":
        return "yes"
    elif s == "False" or s == "false":
        return "no"
    else:
        return s
    
def parse_text(text: str):
    """
    Parse mixed-language text to extract meaningful tokens.
    
    Extracts tokens in priority order: number+unit combos, English words, 
    standalone numbers, and Chinese characters. 
    
    Args:
        text: Input to parse.
    
    Returns:
        Set of tokens.
    """
    pattern = r"""
        \d+\.?\d*[a-zA-Z%℃°\u4e00-\u9fff]+      # number+unit
        |
        [a-zA-Z][a-zA-Z0-9_\-]*                  # English words
        |
        \d+\.?\d*                                # standalone numbers
        |
        \p{Han}                                  # Chinese characters
    """
    
    tokens = regex.findall(pattern, text, regex.VERBOSE)
    return set(tokens)

def f1_score(model_response: str, ground_truth: str):
    """
    Calculate F1 score between model response and ground truth.

    Args:
        model_response (str): Model's output string.
        ground_truth (str): Ground truth string.

    Returns:
        float: F1 score between 0 and 1.
    """
    model_response = bool_mapping(model_response)
    ground_truth = bool_mapping(ground_truth)

    pred_tokens = parse_text(model_response)
    gt_tokens = parse_text(ground_truth)

    if not gt_tokens or not pred_tokens:
        return 0

    common_tokens = pred_tokens & gt_tokens
    precision = len(common_tokens) / len(pred_tokens)
    recall = len(common_tokens) / len(gt_tokens)

    f1 = 0
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    print(f"Grount Truth : {ground_truth}")
    print(f"Model Response : {model_response}")
    print(f"F1_score : {f1:.2f}")
    return f1