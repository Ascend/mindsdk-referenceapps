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

from typing import Optional


class MemoryConfig:
    """
    内存配置存储类

    用于存储敏感配置（如 LLM API KEY），这些配置不会被持久化到磁盘。

    Attributes:
        _llm_api_key: LLM API 密钥（内存存储）
    """

    # 内存中存储的敏感信息（如 LLM API Key）
    _llm_api_key: Optional[str] = None

    @classmethod
    def set_llm_api_key(cls, api_key: Optional[str]) -> None:
        """
        设置 LLM API 密钥

        Args:
            api_key: API 密钥，None 表示清除
        """
        cls._llm_api_key = api_key

    @classmethod
    def get_llm_api_key(cls) -> Optional[str]:
        """
        获取 LLM API 密钥

        Returns:
            Optional[str]: API 密钥，如果未设置则返回 None
        """
        return cls._llm_api_key

    @classmethod
    def clear(cls) -> None:
        """
        清除所有内存配置
        """
        cls._llm_api_key = None
