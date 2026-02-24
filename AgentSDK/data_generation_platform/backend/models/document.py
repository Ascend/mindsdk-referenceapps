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

from typing import Optional, List, Union, Dict, Any, TYPE_CHECKING

from backend.models.text_chunk import TextChunk
from backend.models.constants import (
    DEFAULT_DOCUMENT_STATUS,
    FIELD_ID,
    FIELD_PROJECT_ID,
    FIELD_FILE_NAME,
    FIELD_FILE_TYPE,
    FIELD_CONTENT,
    FIELD_STATUS,
    FIELD_CHUNKS,
)

if TYPE_CHECKING:
    from backend.services.document_service import DocumentService


def _extract_chunk_id(chunk: Union[int, str, 'TextChunk']) -> Union[int, str]:
    """
    从chunk对象中提取ID

    Args:
        chunk: TextChunk对象或ID

    Returns:
        Union[int, str]: chunk的ID
    """
    # 核心：若 chunk 是对象则尽量提取其 id，便于后续引用
    if hasattr(chunk, FIELD_ID) and getattr(chunk, FIELD_ID) is not None:
        return getattr(chunk, FIELD_ID)
    return chunk  # type: ignore


def _extract_chunk_data(chunks: List[Union[int, str, 'TextChunk']]) -> List[Any]:
    """
    从chunks列表中提取数据（ID或原始对象）

    Args:
        chunks: TextChunk对象或ID的列表

    Returns:
        List[Any]: ID列表
    """
    # 将 TextChunk 对象或 ID 统一转换为 ID 列表（用于序列化存储）
    return [_extract_chunk_id(chunk) for chunk in chunks]


def _process_chunks_data(
    chunks_data: List[Any],
    document_service: Optional['DocumentService'] = None,
) -> List[Union[int, str, 'TextChunk']]:
    """
    处理chunks数据，根据是否提供document_service返回相应格式

    Args:
        chunks_data: chunk ID列表
        document_service: 可选的文档服务对象

    Returns:
        List: 处理后的chunks列表（TextChunk 对象或 ID）
    """
    if document_service is None:
        return chunks_data

    actual_chunks = []
    for chunk_id in chunks_data:
        if isinstance(chunk_id, (int, str)):
            chunk_obj = document_service.get_chunk(chunk_id)
            if chunk_obj:
                actual_chunks.append(chunk_obj)
        else:
            actual_chunks.append(chunk_id)
    return actual_chunks


class Document:
    """
    文档类，用于管理文档处理过程

    Attributes:
        id: 文档唯一标识符
        project_id: 所属项目ID
        file_name: 文件名称
        file_type: 文件类型
        content: 文档内容
        status: 文档处理状态 (0:未处理, 1:已分割, 2:已生成问题)
        chunks: 关联的文本块列表
    """

    def __init__(
        self,
        id: Optional[Union[int, str]] = None,
        project_id: Optional[Union[int, str]] = None,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        content: Optional[str] = None,
        status: int = DEFAULT_DOCUMENT_STATUS,
    ):
        """
        初始化文件记录实例

        Args:
            id: 文档唯一标识符
            project_id: 所属项目ID
            file_name: 文件名称
            file_type: 文件类型
            content: 文档内容
            status: 文档处理状态 (0:未处理, 1:已分割, 2:已生成问题)
        """
        # 主要字段：文档标识、所属项目、文件信息等
        self.id = id
        self.project_id = project_id
        self.file_name = file_name
        self.file_type = file_type
        self.content = content
        self.status = status
        # 关联的文本块列表（可以是 TextChunk 对象或其 id）
        self.chunks: List[Union[int, str, TextChunk]] = []

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        document_service: Optional['DocumentService'] = None,
    ) -> 'Document':
        """
        从数据字典创建Document实例

        Args:
            data: 包含文档数据的字典
            document_service: 可选的文档服务对象，用于加载完整的chunk对象

        Returns:
            Document: 创建的实例
        """
        # 从字典创建实例
        instance = cls(
            id=data.get(FIELD_ID),
            project_id=data.get(FIELD_PROJECT_ID),
            file_name=data.get(FIELD_FILE_NAME),
            file_type=data.get(FIELD_FILE_TYPE),
            content=data.get(FIELD_CONTENT),
            status=data.get(FIELD_STATUS, DEFAULT_DOCUMENT_STATUS),
        )

        chunks_data = data.get(FIELD_CHUNKS, [])
        instance.chunks = _process_chunks_data(chunks_data, document_service)

        return instance

    def to_dict(self) -> Dict[str, Any]:
        """
        将实例导出为数据字典

        Returns:
            Dict[str, Any]: 包含所有属性的数据字典
        """
        # 导出为字典，便于序列化存储
        return {
            FIELD_ID: self.id,
            FIELD_PROJECT_ID: self.project_id,
            FIELD_FILE_NAME: self.file_name,
            FIELD_FILE_TYPE: self.file_type,
            FIELD_CONTENT: self.content,
            FIELD_STATUS: self.status,
            FIELD_CHUNKS: _extract_chunk_data(self.chunks),
        }
