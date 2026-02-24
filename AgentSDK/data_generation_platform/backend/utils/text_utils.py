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
from typing import List

from backend.models.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)

# ==================== 分割方法常量 ====================
SPLIT_METHOD_CHAR = "char"
SPLIT_METHOD_SENTENCE = "sentence"
SPLIT_METHOD_PARAGRAPH = "paragraph"
SPLIT_METHOD_MARKDOWN = "markdown"

# ==================== 正则表达式模式 ====================
SENTENCE_SPLIT_PATTERN = r"(?<=[.!?])\s+"
MARKDOWN_HEADER_PATTERN = r"^#{1,6}\s+[^\r\n]+$"


def split_text(
    text: str,
    method: str = SPLIT_METHOD_SENTENCE,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    # 将文本按指定方法分割成文本块
    """
    将文本按指定方法分割成多个块

    Args:
        text: 要分割的原始文本
        method: 分割方法，可选值：
            - "char": 按字符数分割
            - "sentence": 按句子分割（默认）
            - "paragraph": 按段落分割
            - "markdown": 按Markdown结构分割
        chunk_size: 每个块的目标大小（字符数），默认500
        overlap: 块之间的重叠字符数，默认100

    Returns:
        List[str]: 分割后的文本块列表

    Raises:
        ValueError: 不支持的分割方法
    """
    if not text:
        return []

    method_handlers = {
        SPLIT_METHOD_CHAR: _partition_by_char,
        SPLIT_METHOD_SENTENCE: _partition_by_sentence,
        SPLIT_METHOD_PARAGRAPH: _partition_by_paragraph,
        SPLIT_METHOD_MARKDOWN: _partition_by_markdown,
    }

    handler = method_handlers.get(method)
    if handler is None:
        raise ValueError(f"不支持的分割方法: {method}")

    return handler(text, chunk_size, overlap)


def _partition_by_char(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    按字符数分割文本

    Args:
        text: 要分割的文本
        chunk_size: 每个块的大小
        overlap: 块之间的重叠量

    Returns:
        List[str]: 分割后的文本块列表
    """
    if len(text) <= chunk_size:
        return [text]

    if overlap >= chunk_size:
        return [text]

    chunks = []
    start = 0
    end = 0
    while end < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def _add_sentence_to_chunk(
    current_chunk: str, sentence: str, overlap: int
) -> str:
    """
    将句子添加到当前块，处理重叠逻辑

    Args:
        current_chunk: 当前块内容
        sentence: 要添加的句子
        overlap: 重叠字符数

    Returns:
        str: 新的块内容
    """
    if overlap > 0 and current_chunk:
        prev_chunk_end = current_chunk[-overlap:]
        return prev_chunk_end + sentence
    return sentence


def _partition_by_sentence(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    按句子分割文本

    Args:
        text: 要分割的文本
        chunk_size: 每个块的目标大小
        overlap: 块之间的重叠量

    Returns:
        List[str]: 分割后的文本块列表
    """
    sentences = re.split(SENTENCE_SPLIT_PATTERN, text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        would_exceed_limit = (
            len(current_chunk) + len(sentence) > chunk_size and current_chunk
        )

        if would_exceed_limit:
            chunks.append(current_chunk)
            current_chunk = _add_sentence_to_chunk(current_chunk, sentence, overlap)
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _add_paragraph_to_chunk(
    current_chunk: str, paragraph: str, overlap: int
) -> str:
    """
    将段落添加到当前块，处理重叠逻辑

    Args:
        current_chunk: 当前块内容
        paragraph: 要添加的段落
        overlap: 重叠字符数

    Returns:
        str: 新的块内容
    """
    if overlap > 0 and current_chunk:
        prev_chunk_end = current_chunk[-overlap:]
        return prev_chunk_end + "\n\n" + paragraph
    return paragraph


def _partition_by_paragraph(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    按段落分割文本

    Args:
        text: 要分割的文本
        chunk_size: 每个块的目标大小
        overlap: 块之间的重叠量

    Returns:
        List[str]: 分割后的文本块列表
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        would_exceed_limit = (
            len(current_chunk) + len(paragraph) > chunk_size and current_chunk
        )

        if would_exceed_limit:
            chunks.append(current_chunk)
            current_chunk = _add_paragraph_to_chunk(current_chunk, paragraph, overlap)
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _find_markdown_headers(lines: List[str]) -> List[int]:
    """
    查找Markdown标题的行索引

    Args:
        lines: 文本行列表

    Returns:
        List[int]: 标题行的索引列表
    """
    header_indices = []
    for i, line in enumerate(lines):
        if re.match(MARKDOWN_HEADER_PATTERN, line):
            header_indices.append(i)
    return header_indices


def _split_sections(
    lines: List[str], header_indices: List[int], chunk_size: int, overlap: int
) -> List[str]:
    """
    根据标题位置分割文本为多个章节

    Args:
        lines: 文本行列表
        header_indices: 标题行索引列表
        chunk_size: 每个块的目标大小
        overlap: 块之间的重叠量

    Returns:
        List[str]: 分割后的章节列表
    """
    chunks = []
    start_idx = 0

    section_boundaries = header_indices[1:] + [len(lines)]

    for header_idx in section_boundaries:
        section_lines = lines[start_idx:header_idx]
        section_text = "\n".join(section_lines)

        if len(section_text) > chunk_size:
            sub_chunks = _partition_by_paragraph(section_text, chunk_size, overlap)
            chunks.extend(sub_chunks)
        else:
            chunks.append(section_text)

        start_idx = header_idx

    return chunks


def _post_process_chunks(
    chunks: List[str], chunk_size: int, overlap: int
) -> List[str]:
    """
    后处理：过滤空块并处理超大块

    Args:
        chunks: 原始块列表
        chunk_size: 目标块大小
        overlap: 重叠量

    Returns:
        List[str]: 处理后的块列表
    """
    filtered_chunks = [chunk for chunk in chunks if chunk.strip()]
    final_chunks = []

    for chunk in filtered_chunks:
        if len(chunk) > chunk_size:
            sub_chunks = _partition_by_paragraph(chunk, chunk_size, overlap)
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(chunk)

    return final_chunks


def _partition_by_markdown(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    按Markdown结构分割文本

    首先按标题分割，如果某个章节太长则继续按段落分割

    Args:
        text: 要分割的文本
        chunk_size: 每个块的目标大小
        overlap: 块之间的重叠量

    Returns:
        List[str]: 分割后的文本块列表
    """
    lines = text.splitlines()
    header_indices = _find_markdown_headers(lines)

    if not header_indices:
        return _partition_by_paragraph(text, chunk_size, overlap)

    chunks = _split_sections(lines, header_indices, chunk_size, overlap)
    return _post_process_chunks(chunks, chunk_size, overlap)
