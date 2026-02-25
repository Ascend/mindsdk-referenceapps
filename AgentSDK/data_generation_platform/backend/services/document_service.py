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
import hashlib
import os
from typing import Optional, Dict, List, Union

from backend.models.document import Document
from backend.models.text_chunk import TextChunk
from backend.models.constants import (
    DOCUMENT_STATUS_CHUNKED,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_START_INDEX,
    DEFAULT_PREVIEW_LENGTH,
    DEFAULT_SPLIT_METHOD,
    DEFAULT_DOCUMENTS_DIR,
    DEFAULT_CHUNKS_DIR,
)
from backend.utils.file_utils import read_file, save_file
from backend.utils.text_utils import split_text
from backend.utils.logger import init_logger
from backend.utils.validation_utils import validate_required_params
logger = init_logger(__name__)

# ==================== 文件类型到分割方法的映射 ====================
FILE_TYPE_SPLIT_METHODS = {
    'md': 'markdown',
    'markdown': 'markdown',
    'txt': 'paragraph',
    'text': 'paragraph',
}


class DocumentService:
    """
    文档服务类，用于管理文档处理流程

    Attributes:
        project_dir: 项目根目录路径
        documents_dir: 文档存储目录
        chunks_dir: 文本块存储目录
        config: 配置字典
    """

    def __init__(self, project_dir: str, config: Optional[Dict] = None):
        """
        初始化文件处理管理器

        Args:
            project_dir: 项目根目录路径
            config: 配置字典
        """
        self.project_dir = project_dir
        # 初始化：确保文档目录和分块目录存在
        self.documents_dir = os.path.join(project_dir, DEFAULT_DOCUMENTS_DIR)
        self.chunks_dir = os.path.join(self.documents_dir, DEFAULT_CHUNKS_DIR)
        self.config = config or {}

        os.makedirs(self.documents_dir, exist_ok=True)
        os.makedirs(self.chunks_dir, exist_ok=True)

    @staticmethod
    def _extract_document_text(document: Document) -> str:
        """
        从文档对象中提取文本内容

        Args:
            document: 文档对象

        Returns:
            str: 文本内容
        """
        # 如果文档内容是字典，从中提取文本字段
        if isinstance(document.content, dict):
            return document.content.get('text', '')
        return document.content or ""

    @staticmethod
    def _generate_summary(text: str) -> str:
        """
        生成内容摘要

        Args:
            text: 要生成摘要的文本

        Returns:
            str: 生成的摘要
        """
        # 简单摘要：若文本短于阈值，直接返回；否则截断加省略号
        if len(text) <= DEFAULT_PREVIEW_LENGTH:
            return text
        return text[:DEFAULT_PREVIEW_LENGTH] + "..."

    @staticmethod
    def _generate_unique_id(content: str) -> str:
        """
        基于内容生成确定性标识符

        Args:
            content: 文档内容

        Returns:
            str: 基于内容哈希的标识符
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def create_document(
        self,
        project_id: Union[int, str],
        file_path: str,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Document:
        """
        创建文件记录

        Args:
            project_id: 项目ID
            file_path: 文件路径
            file_name: 文件名称（默认从路径提取）
            file_type: 文件类型（默认从扩展名提取）

        Returns:
            Document: 创建的文档对象
        """
        # 使用 validate_required_params 验证必需参数
        params = {'project_id': project_id, 'file_path': file_path}
        missing_param = validate_required_params(params, ['project_id', 'file_path'])
        if missing_param:
            raise ValueError(f'{missing_param} 不能为空')

        if file_name is None:
            file_name = os.path.basename(file_path)
        
        # Determine file type from file name if not provided
        if file_type is None:
            _, ext = os.path.splitext(file_name)
            file_type = ext.lstrip('.').lower()

        content = read_file(file_path, file_type)
        content_str = content if isinstance(content, str) else str(content)
        document_id = self._generate_unique_id(content_str)
        existing_document = self.get_document(document_id)
        if existing_document:
            logger.info(f"文档已存在: {file_name} (ID: {existing_document.id})")
            return existing_document

        # 构建文档实体
        document = Document(
            id=document_id,
            project_id=project_id,
            file_name=file_name,
            file_type=file_type,
            content=content_str,
        )

        doc_file_path = os.path.join(self.documents_dir, f"{document.id}.json")
        save_file(doc_file_path, document.to_dict(), base_dir=self.project_dir)

        return document

    def split_document(self, document: Document) -> List[TextChunk]:
        """
        将文档分割成内容片段

        Args:
            document: 要分割的文档对象

        Returns:
            List[TextChunk]: 生成的内容片段列表
        """
        # 提取文档文本内容作为分割输入
        text = self._extract_document_text(document)
        split_method = self._determine_split_method(document)
        chunk_size = self.config.get('chunk_size', DEFAULT_CHUNK_SIZE)
        chunk_overlap = self.config.get('chunk_overlap', DEFAULT_CHUNK_OVERLAP)

        # 根据指定的分割策略创建块
        chunks = self._create_chunks_with_method(
            document, text, split_method, chunk_size, chunk_overlap
        )

        # 更新文档状态及关联块信息
        self._update_document_after_split(document, chunks)
        return chunks


    def get_documents(
        self, documents_id: Union[int, str]
    ) -> Optional[List[Document]]:
        """
        获取项目文档列表

        Args:
            documents_id: 项目ID

        Returns:
            List[Document]: 文档列表
        """
        documents = []

        if not os.path.exists(self.documents_dir):
            return documents

        # 获取所有符合条件的文件，并按创建时间排序
        json_files = []
        for filename in os.listdir(self.documents_dir):
            if filename.endswith(".json") and not filename.startswith("chunks"):
                file_path = os.path.join(self.documents_dir, filename)
                json_files.append((filename, os.path.getctime(file_path)))

        # 按创建时间排序（升序，最早创建的在前）
        json_files.sort(key=lambda x: x[1])

        # 按排序后的顺序加载文档
        for filename, _ in json_files:
            document = self._load_document_from_file(filename)
            if document:
                documents.append(document)

        return documents

    def get_document(
            self, documents_id: Union[int, str]
    ) -> Optional[Document]:
        """
        获取项目文档

        Args:
            documents_id: 文档ID

        Returns:
            Optional[Document]: 文档对象或None
        """
        document_path = os.path.join(self.documents_dir, f"{documents_id}.json")

        if not os.path.exists(document_path):
            return None

        try:
            doc_data = read_file(document_path, "json")
            return Document.from_dict(doc_data, self)  # type: ignore
        except Exception as e:
            logger.warning(f"读取文档失败 {documents_id}: {e}")
            return None

    def get_chunk(self, chunk_id: Union[int, str]) -> Optional[TextChunk]:
        """
        获取内容片段

        Args:
            chunk_id: 内容片段ID

        Returns:
            Optional[TextChunk]: 找到的内容片段对象或None
        """
        chunk_path = os.path.join(self.chunks_dir, f"{chunk_id}.json")

        if not os.path.exists(chunk_path):
            logger.debug(f"文本块不存在: {chunk_id}")
            return None

        try:
            chunk_data = read_file(chunk_path, "json")
            return TextChunk.from_dict(chunk_data)  # type: ignore
        except Exception as e:
            logger.warning(f"加载文本块失败 {chunk_id}: {e}")
            return None

    def _determine_split_method(self, document: Document) -> str:
        """
        根据文档类型确定分割方法

        Args:
            document: 文档对象

        Returns:
            str: 分割方法名称
        """
        file_type = document.file_type or ''
        default_method = FILE_TYPE_SPLIT_METHODS.get(
            file_type, DEFAULT_SPLIT_METHOD
        )
        return self.config.get('split_method', default_method)

    def _create_chunks_with_method(
        self,
        document: Document,
        text: str,
        split_method: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[TextChunk]:
        """
        使用指定方法创建文本块

        Args:
            document: 文档对象
            text: 文本内容
            split_method: 分割方法
            chunk_size: 块大小
            chunk_overlap: 重叠大小

        Returns:
            List[TextChunk]: 创建的文本块列表
        """
        # 通过文本分块策略创建块
        if split_method in ['sentence', 'paragraph', 'markdown']:
            return self._create_chunks_by_split_text(
                document, text, split_method, chunk_size, chunk_overlap
            )
        return self._create_chunks_by_char(
            document, text, chunk_size, chunk_overlap
        )

    def _create_chunks_by_split_text(
        self,
        document: Document,
        text: str,
        split_method: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[TextChunk]:
        """
        使用split_text工具分割文本

        Args:
            document: 文档对象
            text: 文本内容
            split_method: 分割方法
            chunk_size: 块大小
            chunk_overlap: 重叠大小

        Returns:
            List[TextChunk]: 创建的文本块列表
        """
        # 使用通用文本分割工具进行分块
        chunk_texts = split_text(text, split_method, chunk_size, chunk_overlap)
        chunks = []

        for i, chunk_text in enumerate(chunk_texts):
            chunk = self._create_and_save_chunk(document, chunk_text, i, len(chunks))
            chunks.append(chunk)

        return chunks

    def _create_chunks_by_char(
        self,
        document: Document,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[TextChunk]:
        """
        按字符数分割文本

        Args:
            document: 文档对象
            text: 文本内容
            chunk_size: 块大小
            chunk_overlap: 重叠大小

        Returns:
            List[TextChunk]: 创建的文本块列表
        """
        chunks = []
        start = DEFAULT_START_INDEX
        end = DEFAULT_START_INDEX
        while end < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            # 创建并保存单个文本块
            chunk = self._create_and_save_chunk(document, chunk_text, start, len(chunks))
            chunks.append(chunk)

            start = end - chunk_overlap

        return chunks

    def _create_and_save_chunk(
        self,
        document: Document,
        chunk_text: str,
        position: int,
        chunk_index: int,
    ) -> TextChunk:
        """
        创建并保存单个文本块

        Args:
            document: 文档对象
            chunk_text: 文本内容
            position: 位置信息
            chunk_index: 块索引

        Returns:
            TextChunk: 创建的文本块
        """
        # 构建文本块对象
        chunk = TextChunk(
            id=chunk_index,
            document_id=document.id,
            content=chunk_text,
            position=position,
        )
        # 为文本块生成摘要，便于快速浏览
        chunk.summary = self._generate_summary(chunk_text)

        chunk_path = os.path.join(self.chunks_dir, f"{chunk.id}.json")
        save_file(chunk_path, chunk.to_dict(), base_dir=self.project_dir)

        return chunk

    def _update_document_after_split(
        self, document: Document, chunks: List[TextChunk]
    ) -> None:
        """
        分割后更新文档状态

        Args:
            document: 文档对象
            chunks: 文本块列表
        """
        # 更新文档状态为已经分块，记录所有文本块ID
        document.status = DOCUMENT_STATUS_CHUNKED
        document.chunks = [chunk.id for chunk in chunks]

        document_path = os.path.join(self.documents_dir, f"{document.id}.json")
        save_file(document_path, document.to_dict(), base_dir=self.project_dir)

    def _load_document_from_file(self, filename: str) -> Optional[Document]:
        """
        从文件加载文档

        Args:
            filename: 文件名

        Returns:
            Optional[Document]: 文档对象或None
        """
        document_path = os.path.join(self.documents_dir, filename)
        try:
            doc_data = read_file(document_path, "json")
            return Document.from_dict(doc_data)  # type: ignore
        except Exception as e:
            logger.warning(f"加载文档失败 {filename}: {e}")
            return None
