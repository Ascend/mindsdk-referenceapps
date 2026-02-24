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

from typing import Optional, List, Dict, Any, Union

from backend.models.constants import (
    DEFAULT_QUESTION_STATUS,
    FIELD_ID,
    FIELD_DOCUMENT_ID,
    FIELD_CHUNK_ID,
    FIELD_CONTENT,
    FIELD_ANSWER,
    FIELD_CHAIN_OF_THOUGHT,
    FIELD_STATUS,
    FIELD_LABELS,
)


class Question:
    """
    问题类，用于管理问题配置和状态

    Attributes:
        id: 查询项唯一标识符
        document_id: 关联的文档ID
        chunk_id: 关联的文本块ID
        content: 查询内容
        answer: 答案内容
        chain_of_thought: 推理过程
        status: 查询状态 (0:未回答, 1:已回答, 2:已审核)
        labels: 标签列表
    """

    def __init__(
        self,
        id: Optional[Union[int, str]] = None,
        document_id: Optional[Union[int, str]] = None,
        chunk_id: Optional[Union[int, str]] = None,
        content: Optional[str] = None,
        answer: Optional[str] = None,
        chain_of_thought: Optional[str] = None,
        status: int = DEFAULT_QUESTION_STATUS,
        labels: Optional[List[str]] = None,
    ):
        """
        初始化查询项实例

        Args:
            id: 查询项唯一标识符
            document_id: 关联的文档ID
            chunk_id: 关联的文本块ID
            content: 查询内容
            answer: 答案内容
            chain_of_thought: 推理过程
            status: 查询状态 (0:未回答, 1:已回答, 2:已审核)
            labels: 标签列表
        """
        # 关键字段：问题标识及关联信息
        self.id = id
        self.document_id = document_id  # 关联的文档ID
        self.chunk_id = chunk_id  # 关联的文本块ID
        self.content = content  # 问题文本内容
        self.answer = answer  # 对应的答案文本
        self.chain_of_thought = chain_of_thought  # 推理过程（思路）
        self.status = status  # 状态：未回答/已回答/已审核
        self.labels = labels if labels is not None else []  # 标签集合

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """
        从记录字典创建Question实例

        Args:
            data: 包含查询项数据的字典

        Returns:
            Question: 创建的查询项实例
        """
        return cls(
            id=data.get(FIELD_ID),
            document_id=data.get(FIELD_DOCUMENT_ID),
            chunk_id=data.get(FIELD_CHUNK_ID),
            content=data.get(FIELD_CONTENT),
            answer=data.get(FIELD_ANSWER),
            chain_of_thought=data.get(FIELD_CHAIN_OF_THOUGHT),
            status=data.get(FIELD_STATUS, DEFAULT_QUESTION_STATUS),
            labels=data.get(FIELD_LABELS, []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        将实例导出为记录字典

        Returns:
            Dict[str, Any]: 包含所有属性的记录字典
        """
        return {
            FIELD_ID: self.id,
            FIELD_DOCUMENT_ID: self.document_id,
            FIELD_CHUNK_ID: self.chunk_id,
            FIELD_CONTENT: self.content,
            FIELD_ANSWER: self.answer,
            FIELD_CHAIN_OF_THOUGHT: self.chain_of_thought,
            FIELD_STATUS: self.status,
            FIELD_LABELS: self.labels,
        }
