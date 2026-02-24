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

import uuid
from typing import Optional

from backend.utils.logger import init_logger

logger = init_logger(__name__)


def safe_error_message(
    operation: str,
    error: Exception,
    user_message: Optional[str] = None
) -> str:
    # 生成对用户安全友好的错误信息，同时在日志中记录详细信息
    """
    生成安全的错误消息

    记录详细错误到日志，返回通用消息给用户，
    通过错误 ID 关联日志条目便于排查。

    Args:
        operation: 操作名称
        error: 异常对象
        user_message: 自定义用户消息

    Returns:
        str: 安全的错误消息（包含错误 ID）
    """
    # 生成错误追踪ID
    error_id = str(uuid.uuid4())[:8]

    # 记录详细错误（仅日志）
    logger.error(
        f"Error [{error_id}] in {operation}: {type(error).__name__}: {str(error)}",
        exc_info=True
    )

    # 返回通用消息给用户
    if user_message:
        return f"{user_message} (错误ID: {error_id})"
    return f"操作失败，请稍后重试 (错误ID: {error_id})"


def log_security_event(
    event_type: str,
    details: str,
    remote_addr: Optional[str] = None
) -> None:
    """
    记录安全相关事件

    Args:
        event_type: 事件类型（如 'path_traversal', 'command_injection'）
        details: 事件详情
        remote_addr: 客户端 IP 地址
    """
    log_msg = f"SECURITY_EVENT [{event_type}]: {details}"
    if remote_addr:
        log_msg += f" | IP: {remote_addr}"
    logger.warning(log_msg)
