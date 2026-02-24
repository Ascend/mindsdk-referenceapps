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

from typing import Any, Dict, List, Optional, Tuple

from flask import jsonify, Response

from backend.models.constants import (
    HTTP_OK,
    HTTP_MULTI_STATUS,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    HTTP_UNSUPPORTED_MEDIA_TYPE,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_GATEWAY_TIMEOUT,
)


def success_response(
    message: str = "success",
    data: Optional[Any] = None,
    **kwargs: Any
) -> Tuple[Response, int]:
    """
    构建成功响应

    Args:
        message: 成功消息
        data: 响应数据
        **kwargs: 额外的响应字段

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码
    """
    # 构建响应主体
    response_body: Dict[str, Any] = {"status": "success", "message": message}
    if data is not None:
        response_body["data"] = data
    response_body.update(kwargs)
    return jsonify(response_body), HTTP_OK


def error_response(
    message: str,
    status_code: int = HTTP_BAD_REQUEST,
    **kwargs: Any
) -> Tuple[Response, int]:
    """
    构建错误响应

    Args:
        message: 错误消息
        status_code: HTTP状态码，默认400
        **kwargs: 额外的响应字段

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码
    """
    response_body: Dict[str, Any] = {"status": "error", "message": message}
    response_body.update(kwargs)
    return jsonify(response_body), status_code


def partial_success_response(
    message: str,
    success_count: int,
    errors: Optional[List[str]] = None,
    **kwargs: Any
) -> Tuple[Response, int]:
    """
    构建部分成功响应

    Args:
        message: 响应消息
        success_count: 成功处理的数量
        errors: 错误列表
        **kwargs: 额外的响应字段

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码
    """
    response_body: Dict[str, Any] = {
        "status": "partial_success",
        "message": message,
        "deleted_count": success_count,
    }
    if errors:
        response_body["errors"] = errors
    response_body.update(kwargs)
    return jsonify(response_body), HTTP_MULTI_STATUS


def not_found_response(
    message: str = "Resource not found"
) -> Tuple[Response, int]:
    """
    构建404未找到响应

    Args:
        message: 错误消息

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码
    """
    return error_response(message, HTTP_NOT_FOUND)


def server_error_response(
    message: str = "Internal server error"
) -> Tuple[Response, int]:
    """
    构建500服务器错误响应

    Args:
        message: 错误消息

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码
    """
    return error_response(message, HTTP_INTERNAL_SERVER_ERROR)


def missing_param_response(param_name: str) -> Tuple[Response, int]:
    """
    构建缺少参数响应

    Args:
        param_name: 缺少的参数名

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码
    """
    return error_response(f"Missing required parameter: {param_name}")


def access_denied_response(
    message: str = "Access denied"
) -> Tuple[Response, int]:
    """
    构建访问拒绝响应

    Args:
        message: 拒绝消息

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码 (403)
    """
    return error_response(message, 403)


def unsupported_media_type_response(
    message: str = "Unsupported media type"
) -> Tuple[Response, int]:
    """
    构建415不支持的媒体类型响应

    Args:
        message: 错误消息

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码 (415)
    """
    return error_response(message, HTTP_UNSUPPORTED_MEDIA_TYPE)


def gateway_timeout_response(
    message: str = "Gateway timeout"
) -> Tuple[Response, int]:
    """
    构建504网关超时响应

    Args:
        message: 错误消息

    Returns:
        Tuple[Response, int]: JSON响应和HTTP状态码 (504)
    """
    return error_response(message, HTTP_GATEWAY_TIMEOUT)
