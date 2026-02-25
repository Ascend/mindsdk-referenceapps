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
from pathlib import Path
from typing import Optional, Union, Dict, Any

import json

from backend.models.constants import (
    ENCODING_UTF8,
    JSON_INDENT,
    MAX_FILENAME_LENGTH,
    TEXT_FILE_EXTENSIONS,
    JSON_FILE_EXTENSION,
    YAML_FILE_EXTENSIONS,
    DOCX_FILE_EXTENSION,
    PDF_FILE_EXTENSION,
)


MAX_PATH_LEN = 1024

def _read_text_file(file_path: str) -> str:
    """读取文本文件"""
    with open(file_path, 'r', encoding=ENCODING_UTF8) as f:
        return f.read()

def _read_json_file(file_path: str) -> Dict[Any, Any]:
    """读取JSON文件"""
    with open(file_path, 'r', encoding=ENCODING_UTF8) as f:
        return json.load(f)

def _read_yaml_file(file_path: str) -> Dict[Any, Any]:
    """读取YAML文件"""
    try:
        import yaml
    except ImportError as e:
        raise ImportError(
            f"处理YAML文件需要安装PyYAML: pip install PyYAML (文件: {file_path}). {e}"
        ) from e
    with open(file_path, 'r', encoding=ENCODING_UTF8) as f:
        return yaml.safe_load(f)

def _read_docx_file(file_path: str) -> str:
    """读取DOCX文件，提取文本段落"""
    try:
        from docx import Document
    except ImportError as e:
        raise ImportError(
            f"处理DOCX文件需要安装python-docx: pip install python-docx (文件: {file_path}). {e}"
        ) from e
    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs]
    return '\n'.join(paragraphs)

def _read_pdf_file(file_path: str) -> str:
    """读取PDF文件，提取文本内容"""
    try:
        import PyPDF2
    except ImportError as e:
        raise ImportError(
            f"处理PDF文件需要安装PyPDF2: pip install PyPDF2 (文件: {file_path}). {e}"
        ) from e
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        pages_text = [reader.pages[i].extract_text() for i in range(len(reader.pages))]
        return ''.join(pages_text)

def _get_file_extension(file_path: str) -> str:
    """获取文件扩展名（不含点号，小写）"""
    return os.path.splitext(file_path)[1][1:].lower()

def read_file(file_path: str, file_type: Optional[str] = None) -> Union[str, Dict[Any, Any]]:
    """根据扩展名/指定类型读取文件内容：支持文本/JSON/YAML/DOCX/PDF"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if file_type is None:
        file_type = _get_file_extension(file_path)

    if file_type in TEXT_FILE_EXTENSIONS:
        return _read_text_file(file_path)
    elif file_type == JSON_FILE_EXTENSION:
        return _read_json_file(file_path)
    elif file_type in YAML_FILE_EXTENSIONS:
        return _read_yaml_file(file_path)
    elif file_type in DOCX_FILE_EXTENSION:
        return _read_docx_file(file_path)
    elif file_type == PDF_FILE_EXTENSION:
        return _read_pdf_file(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type} (文件: {file_path})")

def _save_json_file(file_path: str, content: Dict[Any, Any]) -> None:
    """保存JSON文件"""
    with open(file_path, 'w', encoding=ENCODING_UTF8) as f:
        json.dump(content, f, ensure_ascii=False, indent=JSON_INDENT)

def _save_text_file(file_path: str, content: Union[str, Dict[Any, Any]]) -> None:
    """保存文本文件"""
    if isinstance(content, dict):
        content = str(content)
    with open(file_path, 'w', encoding=ENCODING_UTF8) as f:
        f.write(content)

def save_file(file_path: str, content: Union[Dict[Any, Any], str], base_dir: Optional[str] = None) -> None:
    """写入文件：根据扩展名自动选择保存策略"""
    if base_dir:
        abs_path = os.path.abspath(file_path)
        abs_base = os.path.abspath(base_dir)
        if not abs_path.startswith(abs_base + os.sep) and abs_path != abs_base:
            raise ValueError(f"File path outside allowed directory: {base_dir}")
    file_ext = _get_file_extension(file_path)
    directory = os.path.dirname(file_path)
    if directory:
        ensure_dir_exists(directory)
    if file_ext == JSON_FILE_EXTENSION:
        _save_json_file(file_path, content)  # type: ignore
    elif file_ext in TEXT_FILE_EXTENSIONS + YAML_FILE_EXTENSIONS:
        _save_text_file(file_path, content)
    else:
        raise ValueError(f"不支持的文件类型: {file_ext} (文件: {file_path})")

def ensure_dir_exists(directory: Optional[str]) -> None:
    """确保目录存在，如果不存在则创建"""
    if directory is None or directory.strip() == "":
        return
    path = Path(directory)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def secure_filename(filename: str) -> str:
    """
    安全的文件名处理函数，支持中文文件名

    与 werkzeug.utils.secure_filename 不同，此函数保留中文字符，
    只移除或替换真正危险的字符

    Args:
        filename: 原始文件名

    Returns:
        str: 处理后的安全文件名
    """
    if not filename:
        return ''

    import unicodedata

    # 保留中文字符、字母、数字、下划线、连字符、点和空格
    # 移除路径分隔符和其他危险字符
    # 允许的字符: 中文(\u4e00-\u9fff)、字母、数字、._-

    # 首先规范化Unicode字符
    filename = unicodedata.normalize('NFC', filename)

    # 移除路径遍历相关字符
    filename = filename.replace('..', '_')
    filename = filename.replace('/', '_')
    filename = filename.replace('\\', '_')

    # 移除控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32)

    # 替换其他危险字符为下划线
    # 保留: 中文、字母、数字、空格、点、连字符、下划线
    safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ._-')
    result = []
    for char in filename:
        if (char in safe_chars or '\u4e00' <= char <= '\u9fff' or
                '\u3000' <= char <= '\u303f' or '\uff00' <= char <= '\uffef'):
            result.append(char)
        else:
            result.append('_')

    filename = ''.join(result)

    # 去除首尾空格和点
    filename = filename.strip(' .')

    # 如果文件名为空，返回默认名称
    if not filename:
        return 'unnamed_file'

    # 限制文件名长度（保留扩展名）
    max_len = MAX_FILENAME_LENGTH
    if len(filename) > max_len:
        name, ext = os.path.splitext(filename)
        if ext:
            name = name[:max_len - len(ext)] + ext
        else:
            name = name[:max_len]
        filename = name

    return filename
