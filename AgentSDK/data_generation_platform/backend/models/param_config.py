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

Parameter configuration classes for reducing function parameter counts.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


# ==================== LLM Service 参数封装 ====================

@dataclass
class LLMProviderConfig:
    """
    LLM提供商配置参数

    Attributes:
        provider: 语言模型提供商 (openai/ollama)
        api_key: API密钥
        model_name: 模型名称
        llm_api: 自定义API地址
    """
    provider: str = "openai"
    api_key: Optional[str] = None
    model_name: str = "gpt-3.5-turbo"
    llm_api: Optional[str] = None


@dataclass
class LLMGenerationConfig:
    """
    LLM生成配置参数

    Attributes:
        max_tokens: 最大生成token数
        temperature: 生成温度参数
    """
    max_tokens: int = 8192
    temperature: float = 0.0


@dataclass
class LLMPromptConfig:
    """
    LLM提示词配置参数

    Attributes:
        system_prompt: 系统提示词
        answer_prompt: 答案生成提示词
        chain_of_thought_prompt: 思维链生成提示词
    """
    system_prompt: str = "Generate questions based on the content"
    answer_prompt: str = "Answer the question based on the given context"
    chain_of_thought_prompt: str = "Think step by step and show your reasoning process before answering:"


# ==================== Dataset Service 参数封装 ====================

@dataclass
class DatasetDirectoryConfig:
    """
    数据集目录配置参数

    Attributes:
        project_dir: 项目根目录
        datasets_dir: 数据集存储目录
        questions_dir: 问题存储目录
    """
    project_dir: str
    datasets_dir: str = "datasets"
    questions_dir: str = "questions"


@dataclass
class DatasetServiceConfig:
    """
    数据集服务配置参数

    Attributes:
        llm_service: 语言模型服务实例
        config: 配置字典
        system_prompt: 系统提示词
    """
    llm_service: Optional[Any] = None
    config: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None


@dataclass
class QuestionGenerationConfig:
    """
    问题生成配置参数

    Attributes:
        num_questions: 每个块生成的问题数量
        with_chain_of_thought: 是否生成思维链
        output_format: 输出格式
        system_prompt: 自定义系统提示词
    """
    num_questions: int = 3
    with_chain_of_thought: bool = False
    output_format: str = "alpaca"
    system_prompt: Optional[str] = None


@dataclass
class DatasetExportConfig:
    """
    数据集导出配置参数

    Attributes:
        format: 数据集格式
        file_type: 文件类型
        include_chain_of_thought: 是否包含思维链
        system_prompt: 系统提示词
    """
    format: str = "alpaca"
    file_type: str = "json"
    include_chain_of_thought: bool = False
    system_prompt: Optional[str] = None


@dataclass
class QuestionImportConfig:
    """
    问题导入配置参数

    Attributes:
        xlsx_file_path: XLSX文件路径
        document_id: 关联文档ID
        chunk_id: 关联文本块ID
    """
    xlsx_file_path: str
    document_id: Any
    chunk_id: Any


@dataclass
class DatasetCreateConfig:
    """
    数据集创建配置参数

    Attributes:
        project_id: 项目ID
        name: 数据集名称
        format: 数据格式
        file_type: 文件类型
        system_prompt: 系统提示词
    """
    project_id: Any
    name: str
    format: str = "alpaca"
    file_type: str = "json"
    system_prompt: Optional[str] = None


@dataclass
class DocumentCreateConfig:
    """
    文档创建配置参数

    Attributes:
        project_id: 项目ID
        file_path: 文件路径
        file_name: 文件名称
        file_type: 文件类型
    """
    project_id: Any
    file_path: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None


@dataclass
class TextSplitConfig:
    """
    文本分割配置参数

    Attributes:
        split_method: 分割方法
        chunk_size: 块大小
        chunk_overlap: 重叠大小
    """
    split_method: str = "sentence"
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class LLMCallConfig:
    """
    LLM调用配置参数

    Attributes:
        prompt: 提示词
        max_tokens: 最大token数
        temperature: 温度参数
    """
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
