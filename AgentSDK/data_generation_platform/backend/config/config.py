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

import os
from dataclasses import dataclass
from typing import Optional

import json

from backend.models.constants import (
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    DEFAULT_DATASET_FORMAT,
    DEFAULT_DATASET_FILE_TYPE,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_GENERATE_PROMPT,
    DEFAULT_ANSWER_PROMPT,
    DEFAULT_CHAIN_OF_THOUGHT_PROMPT,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    CUSTOM_QUESTION_KEY,
    CUSTOM_ANSWER_KEY,
    CUSTOM_SYSTEM_KEY,
    ENCODING_UTF8,
    DEFAULT_DATA_DIR,
    DEFAULT_CONFIG_PATH,
)


@dataclass
class Config:
    """
    应用程序配置数据类

    Attributes:
        data_dir: 数据存储目录路径
        llm_provider: LLM服务提供商 (openai/ollama)
        llm_api_key: LLM API密钥
        llm_model: 使用的模型名称
        llm_api: 自定义LLM API地址
        default_dataset_format: 默认数据集格式 (alpaca/sharegpt)
        default_dataset_file_type: 默认数据集文件类型 (json/jsonl) 创建数据集时需选定
        system_prompt: 系统提示词
        generate_prompt: 问题生成提示词
        answer_prompt: 答案生成提示词
        chain_of_thought_prompt: 思维链生成提示词
        chunk_size: 文本分块大小
        chunk_overlap: 分块重叠字符数
        max_tokens: 最大生成token数
        temperature: 生成温度参数
        custom_question_key: 自定义格式中问题字段的键名
        custom_answer_key: 自定义格式中答案字段的键名
        custom_system_key: 自定义格式中系统提示词字段的键名
    """
    data_dir: str
    llm_provider: str = DEFAULT_LLM_PROVIDER
    llm_api_key: Optional[str] = None
    llm_model: str = DEFAULT_LLM_MODEL
    llm_api: Optional[str] = None
    default_dataset_format: str = DEFAULT_DATASET_FORMAT
    default_dataset_file_type: str = DEFAULT_DATASET_FILE_TYPE
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    generate_prompt: str = DEFAULT_GENERATE_PROMPT
    answer_prompt: str = DEFAULT_ANSWER_PROMPT
    chain_of_thought_prompt: str = DEFAULT_CHAIN_OF_THOUGHT_PROMPT
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    custom_question_key: str = CUSTOM_QUESTION_KEY
    custom_answer_key: str = CUSTOM_ANSWER_KEY
    custom_system_key: str = CUSTOM_SYSTEM_KEY

    @classmethod
    def load(cls, config_path: str = DEFAULT_CONFIG_PATH) -> "Config":
        # 从磁盘加载配置，返回 Config 实例
        """
        从配置文件加载配置

        Args:
            config_path: 配置文件路径，默认为 "config.json"

        Returns:
            Config: 加载的配置实例

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, "r", encoding=ENCODING_UTF8) as f:
            config_data = json.load(f)

        return cls._create_from_dict(config_data)

    @classmethod
    def _create_from_dict(cls, config_data: dict) -> "Config":
        """
        从字典创建配置实例

        Args:
            config_data: 配置数据字典

        Returns:
            Config: 创建的配置实例
        """
        return cls(
            data_dir=config_data.get("data_dir", DEFAULT_DATA_DIR),
            llm_provider=config_data.get("llm_provider", DEFAULT_LLM_PROVIDER),
            llm_api_key=config_data.get("llm_api_key"),
            llm_model=config_data.get("llm_model", DEFAULT_LLM_MODEL),
            llm_api=config_data.get("llm_api"),
            default_dataset_format=config_data.get(
                "default_dataset_format", DEFAULT_DATASET_FORMAT
            ),
            default_dataset_file_type=config_data.get(
                "default_dataset_file_type", DEFAULT_DATASET_FILE_TYPE
            ),
            system_prompt=config_data.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
            generate_prompt=config_data.get("generate_prompt", DEFAULT_GENERATE_PROMPT),
            answer_prompt=config_data.get("answer_prompt", DEFAULT_ANSWER_PROMPT),
            chain_of_thought_prompt=config_data.get(
                "chain_of_thought_prompt", DEFAULT_CHAIN_OF_THOUGHT_PROMPT
            ),
            chunk_size=config_data.get("chunk_size", DEFAULT_CHUNK_SIZE),
            chunk_overlap=config_data.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP),
            max_tokens=config_data.get("max_tokens", DEFAULT_MAX_TOKENS),
            temperature=config_data.get("temperature", DEFAULT_TEMPERATURE),
            custom_question_key=config_data.get(
                "custom_question_key", CUSTOM_QUESTION_KEY
            ),
            custom_answer_key=config_data.get("custom_answer_key", CUSTOM_ANSWER_KEY),
            custom_system_key=config_data.get("custom_system_key", CUSTOM_SYSTEM_KEY),
        )
