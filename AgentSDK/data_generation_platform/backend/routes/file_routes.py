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
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, Response

from backend.config.config import Config
from backend.utils.logger import init_logger
from backend.utils.response_utils import (
    success_response,
    server_error_response,
)
from backend.models.constants import (
    DEFAULT_CONFIG_PATH,
    BYTES_PER_KB,
    BYTES_PER_MB,
    BYTES_PER_GB,
)

file_bp = Blueprint('file', __name__)

logger = init_logger(__name__)


@file_bp.route('/list_files')
def list_files() -> Tuple[Response, int]:
    """文件列表路由"""
    # 增量注释：读取配置并列出数据目录结构
    try:
        config = Config.load(DEFAULT_CONFIG_PATH)
        # 归一化路径，处理 Windows 风格相对路径（如 .\data）在 Linux 上的问题
        data_dir = os.path.normpath(config.data_dir)

        directory_tree = get_directory_tree(data_dir)
        # 记录日志，返回目录树结果
        logger.debug(f"list_files path : {data_dir}, count: {len(directory_tree or [])}")
        return success_response(data=directory_tree)
    except Exception as e:
        logger.error("Failed to list files from directory", exc_info=False)
        return server_error_response(str(e))


def get_directory_tree(path: str, rel_path: str = '') -> Optional[Dict[str, Any]]:
    """
    生成目录树结构

    Args:
        path: 目录路径
        rel_path: 相对路径

    Returns:
        Optional[Dict[str, Any]]: 目录树字典
    """
    # 核心逻辑：如果路径不存在，返回 None
    # 入口注释：如果路径不存在，直接返回 None
    if not os.path.exists(path):
        return None

    tree = _create_directory_node(path, rel_path)
    _populate_directory_children(path, rel_path, tree)

    return tree


def _create_directory_node(path: str, rel_path: str) -> Dict[str, Any]:
    """
    创建目录节点

    Args:
        path: 目录路径
        rel_path: 相对路径

    Returns:
        Dict[str, Any]: 目录节点字典
    """
    return {
        'name': os.path.basename(path) if rel_path else 'root',
        'type': 'directory',
        'children': [],
        'path': rel_path,
        'modified': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
    }


def _populate_directory_children(
    path: str,
    rel_path: str,
    tree: Dict[str, Any]
) -> None:
    """
    填充目录子节点

    Args:
        path: 目录路径
        rel_path: 相对路径
        tree: 目录树字典
    """
    # 核心逻辑：遍历当前目录，递归构建子节点
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            rel_item_path = os.path.join(rel_path, item) if rel_path else item

            if os.path.isdir(item_path):
                child_tree = get_directory_tree(item_path, rel_item_path)
                tree['children'].append(child_tree)
            else:
                file_node = _create_file_node(item, item_path, rel_item_path)
                tree['children'].append(file_node)
    except Exception as e:
        tree['error'] = str(e)


def _create_file_node(
    name: str,
    item_path: str,
    rel_item_path: str
) -> Dict[str, Any]:
    """
    创建文件节点

    Args:
        name: 文件名
        item_path: 文件完整路径
        rel_item_path: 相对路径

    Returns:
        Dict[str, Any]: 文件节点字典
    """
    # 核心逻辑：读取文件信息并格式化输出
    try:
        modified_time = datetime.fromtimestamp(
            os.path.getmtime(item_path)
        ).strftime('%Y-%m-%d %H:%M:%S')
        file_size = os.path.getsize(item_path)
        size_str = _format_file_size(file_size)

        return {
            'name': name,
            'type': 'file',
            'size': file_size,
            'size_str': size_str,
            'modified': modified_time,
            'path': rel_item_path
        }
    except Exception as e:
        return {
            'name': name,
            'type': 'file',
            'error': str(e),
            'path': rel_item_path
        }


def _format_file_size(file_size: int) -> str:
    """
    格式化文件大小

    Args:
        file_size: 文件大小（字节）

    Returns:
        str: 格式化后的大小字符串
    """
    if file_size < BYTES_PER_KB:
        return f"{file_size} B"
    elif file_size < BYTES_PER_MB:
        return f"{file_size / BYTES_PER_KB:.1f} KB"
    elif file_size < BYTES_PER_GB:
        return f"{file_size / BYTES_PER_MB:.1f} MB"
    else:
        return f"{file_size / BYTES_PER_GB:.1f} GB"
