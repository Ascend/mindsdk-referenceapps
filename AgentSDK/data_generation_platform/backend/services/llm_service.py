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

import re
import requests
from typing import Optional, List

from backend.models.param_config import (
    LLMProviderConfig,
    LLMGenerationConfig,
    LLMPromptConfig,
)
from backend.models.constants import (
    DEFAULT_LLM_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_NUM_QUESTIONS,
    DEFAULT_LOCAL_API_URL,
    HTTP_OK,
    HTTP_REQUEST_CONNECT_TIMEOUT,
    HTTP_REQUEST_READ_TIMEOUT,
)
from backend.utils.logger import init_logger

logger = init_logger(__name__)

# ==================== API URL常量 ====================
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# ==================== 提供商常量 ====================
PROVIDER_OPENAI = "openai"
PROVIDER_OLLAMA = "ollama"

# ==================== 默认提示词常量 ====================
DEFAULT_SYSTEM_PROMPT = "Generate questions based on the content"
DEFAULT_ANSWER_PROMPT = "Answer the question based on the given context"
DEFAULT_COT_PROMPT = "Think step by step and show your reasoning process before answering:"

# ==================== 问题解析正则模式 ====================
NUMBERED_LIST_PATTERN = r'^\s*\d+\.\s*'
PARENTHESIS_NUMBER_PATTERN = r'^\s*\(\d+\)\s*'
Q_PREFIX_PATTERN = r'^\s*Q\d+:\s*'


class LLMService:
    """
    语言模型提供商类，支持多种大语言模型提供商

    Attributes:
        provider_config: LLM提供商配置
        generation_config: LLM生成配置
        prompt_config: LLM提示词配置
    """

    def __init__(
        self,
        provider_config: Optional[LLMProviderConfig] = None,
        generation_config: Optional[LLMGenerationConfig] = None,
        prompt_config: Optional[LLMPromptConfig] = None,
    ):
        """
        初始化语言模型提供商

        Args:
            provider_config: LLM提供商配置
            generation_config: LLM生成配置
            prompt_config: LLM提示词配置
        """
        provider_config = provider_config or LLMProviderConfig()
        generation_config = generation_config or LLMGenerationConfig()
        prompt_config = prompt_config or LLMPromptConfig()

        self.provider = provider_config.provider
        self.api_key = provider_config.api_key
        self.model_name = provider_config.model_name
        self.llm_api = provider_config.llm_api
        self.max_tokens = generation_config.max_tokens
        self.temperature = generation_config.temperature
        self.system_prompt = prompt_config.system_prompt
        self.answer_prompt = prompt_config.answer_prompt
        self.chain_of_thought_prompt = prompt_config.chain_of_thought_prompt


    @staticmethod
    def _clean_question_line(line: str) -> str:
        """
        清理问题行，移除编号前缀

        Args:
            line: 原始行文本

        Returns:
            str: 清理后的文本
        """
        # 移除 "1. ", "2. " 等格式
        cleaned = re.sub(NUMBERED_LIST_PATTERN, '', line)
        # 移除 "(1)", "(2)" 等格式
        cleaned = re.sub(PARENTHESIS_NUMBER_PATTERN, '', cleaned)
        # 移除 "Q1:", "Q2:" 等格式
        cleaned = re.sub(Q_PREFIX_PATTERN, '', cleaned)
        # 移除行首的破折号和空格
        cleaned = cleaned.strip('- ')
        return cleaned

    def generate_questions(
        self,
        text: str,
        num_questions: int = DEFAULT_NUM_QUESTIONS,
        system_prompt: Optional[str] = None,
    ) -> List[str]:
        """
        生成问题列表

        Args:
            text: 要分析的文本
            num_questions: 生成的问题数量 (默认3)
            system_prompt: 自定义系统提示词 (默认None)

        Returns:
            List[str]: 生成的问题列表
        """
        # 使用系统提示词，或自定义提示词来引导问题生成
        prompt = system_prompt or self.system_prompt
        # 在提示词中明确指定要生成的问题数量
        full_prompt = f"{prompt} text: \\n\\n{text}\n\n请生成{num_questions}个相关问题:"

        response = self._call_llm(full_prompt)
        return self._parse_questions(response, num_questions)

    def generate_answer(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        生成回答

        Args:
            question: 要回答的问题
            context: 相关上下文
            system_prompt: 自定义回答提示词 (默认None)

        Returns:
            str: 生成的回答
        """
        # 构造回答所需的提示词
        prompt = system_prompt or self.answer_prompt
        full_prompt = (
            f"{prompt}\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:"
        )
        return self._call_llm(full_prompt)

    def generate_chain_of_thought(
        self,
        question: str,
        answer: str,
        context: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        生成思维链

        Args:
            question: 问题
            answer: 答案
            context: 相关上下文
            system_prompt: 自定义思维链提示词 (默认None)

        Returns:
            str: 生成的思维链
        """
        prompt = system_prompt or self.chain_of_thought_prompt
        full_prompt = (
            f"{prompt}\n\nContext: {context}\n\n"
            f"Question: {question}\n\nAnswer: {answer}\n\nChain of thought:"
        )
        return self._call_llm(full_prompt)

    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM获取响应

        Args:
            prompt: 发送给LLM的提示词

        Returns:
            str: LLM生成的响应文本

        Raises:
            Exception: API调用失败时抛出
            ValueError: 不支持的提供商时抛出
        """
        # 根据提供商选择调用实现
        if self.provider == PROVIDER_OPENAI:
            return self._call_openai(prompt)
        elif self.provider == PROVIDER_OLLAMA:
            return self._call_ollama(prompt)
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

    def _call_openai(self, prompt: str) -> str:
        """
        调用OpenAI API

        Args:
            prompt: 提示词

        Returns:
            str: 响应文本

        Raises:
            Exception: API调用失败时抛出
        """
        # 调用OpenAI接口的请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        url = self.llm_api or OPENAI_API_URL
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=(HTTP_REQUEST_CONNECT_TIMEOUT, HTTP_REQUEST_READ_TIMEOUT)
        )

        if response.status_code != HTTP_OK:
            raise Exception(
                f"OpenAI API请求失败，状态码: {response.status_code}, "
                f"响应: {response.text}"
            )

        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()

    def _call_ollama(self, prompt: str) -> str:
        """
        调用Ollama API

        Args:
            prompt: 提示词

        Returns:
            str: 响应文本

        Raises:
            Exception: API调用失败时抛出
        """
        # Ollama API 请求头
        headers = {"Content-Type": "application/json"}

        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        url = self.llm_api or DEFAULT_LOCAL_API_URL
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=(HTTP_REQUEST_CONNECT_TIMEOUT, HTTP_REQUEST_READ_TIMEOUT)
        )

        if response.status_code != HTTP_OK:
            raise Exception(
                f"Ollama API请求失败，状态码: {response.status_code}, "
                f"响应: {response.text}"
            )

        response_data = response.json()
        return response_data["message"]["content"].strip()

    def _parse_questions(self, response: str, num_questions: int) -> List[str]:
        """
        解析问题列表

        Args:
            response: LLM返回的原始响应
            num_questions: 期望的问题数量

        Returns:
            List[str]: 清理后的问题列表，最多包含num_questions个问题
        """
        # 解析LLM返回的多行文本为独立问题
        lines = response.splitlines()
        questions = []

        for line in lines:
            if not line.strip():
                continue

            cleaned_line = self._clean_question_line(line)
            if cleaned_line:
                questions.append(cleaned_line)
                # 达到指定数量时停止解析
                if len(questions) >= num_questions:
                    break

        return questions
