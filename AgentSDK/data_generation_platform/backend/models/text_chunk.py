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
from typing import Optional, Any, Dict, Union

from backend.models.constants import (
    FIELD_ID,
    FIELD_DOCUMENT_ID,
    FIELD_CONTENT,
    FIELD_POSITION,
    FIELD_SUMMARY,
)


class TextChunk:
    """
    文本块类，用于表示和管理文本内容块

    Attributes:
        id: 内容片段唯一标识符
        document_id: 所属文档ID
        content: 内容片段文本
        position: 在文档中的位置信息
        summary: 内容摘要
    """

    def __init__(
        self,
        id: Optional[Union[int, str]] = None,
        document_id: Optional[Union[int, str]] = None,
        content: Optional[str] = None,
        position: Optional[int] = None,
        summary: Optional[str] = None,
    ):
        """
        初始化内容片段实例

        Args:
            id: 内容片段唯一标识符
            document_id: 所属文档ID
            content: 内容片段文本
            position: 在文档中的位置信息
            summary: 内容摘要
        """
        # 核心字段：唯一标识、所属文档、文本内容、位置信息、摘要
        self.id = id
        self.document_id = document_id  # 所属文档ID
        self.content = content  # 文本块内容
        self.position = position  # 在文档中的相对位置/顺序
        self.summary = summary  # 内容摘要

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextChunk':
        """
        从数据字典创建 TextChunk 实例

        Args:
            data: 包含内容片段数据的字典

        Returns:
            TextChunk: 创建的内容片段实例
        """
        return cls(
            id=data.get(FIELD_ID),
            document_id=data.get(FIELD_DOCUMENT_ID),
            content=data.get(FIELD_CONTENT),
            position=data.get(FIELD_POSITION),
            summary=data.get(FIELD_SUMMARY),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        将实例导出为数据字典

        Returns:
            Dict[str, Any]: 包含所有属性的数据字典
        """
        return {
            FIELD_ID: self.id,
            FIELD_DOCUMENT_ID: self.document_id,
            FIELD_CONTENT: self.content,
            FIELD_POSITION: self.position,
            FIELD_SUMMARY: self.summary,
        }
