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

import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from flask import Request

from backend.models.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PAGINATION_WINDOW_SIZE,
    PAGINATION_EDGE_THRESHOLD,
    ID_PATTERN,
    MAX_ID_LENGTH,
    SAFE_FIELDS,
    SENSITIVE_KEYWORDS,
)


# ==================== 项目名称校验常量 ====================
PROJECT_NAME_MIN_LENGTH = 1
PROJECT_NAME_MAX_LENGTH = 256
# 项目名称允许的字符：字母、数字、下划线、连字符、中文（Unicode范围）
PROJECT_NAME_PATTERN = re.compile(r'^[\w\-\u4e00-\u9fff]+$')


def validate_required_params(
    data: Dict[str, Any],
    required_params: List[str],
) -> Optional[str]:
    """验证必需参数是否存在

    Args:
        data: 包含参数的字典
        required_params: 必需参数名列表

    Returns:
        Optional[str]: 如果缺少参数，返回缺少的参数名；否则返回None
    """
    for param in required_params:
        if not data.get(param):
            return param
    return None


def get_pagination_params(request: Request) -> Tuple[int, int, Optional[int]]:
    """从请求中获取分页参数

    添加边界验证，防止参数滥用导致的 DoS 攻击。

    Returns: (page, per_page, status_filter)
    """
    page = request.args.get('page', DEFAULT_PAGE_NUMBER, type=int)
    per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE, type=int)
    status_filter = request.args.get('status', type=int)

    page = max(1, page)
    per_page = max(1, min(per_page, MAX_PAGE_SIZE))

    return page, per_page, status_filter


def calculate_pagination_info(total_items: int, page: int, per_page: int) -> Dict[str, Any]:
    """计算分页信息"""
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    page_numbers = generate_page_numbers(page, total_pages)
    return {
        'page': page,
        'per_page': per_page,
        'total': total_items,
        'pages': total_pages,
        'pageNumbers': page_numbers,
    }


def generate_page_numbers(current_page: int, total_pages: int) -> List[int]:
    """生成页码数组"""
    if total_pages <= PAGINATION_WINDOW_SIZE:
        return list(range(1, total_pages + 1))
    if current_page <= PAGINATION_EDGE_THRESHOLD:
        return list(range(1, PAGINATION_WINDOW_SIZE + 1))
    if current_page + 1 >= total_pages:
        return list(range(total_pages - PAGINATION_WINDOW_SIZE + 1, total_pages + 1))
    half_window = PAGINATION_WINDOW_SIZE // 2
    return list(range(current_page - half_window, current_page + half_window + 1))


def paginate_list(items: List[Any], page: int, per_page: int) -> List[Any]:
    """对列表进行分页"""
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    return items[start_index:end_index]


def filter_sensitive_fields(data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
    """过滤敏感字段，防止敏感信息泄露"""
    safe_data = data.copy()
    for field_name in list(safe_data.keys()):
        if field_name in SAFE_FIELDS:
            continue
        if field_name in sensitive_fields:
            safe_data[field_name] = '[FILTERED]'
        elif any(keyword in field_name.lower() for keyword in SENSITIVE_KEYWORDS):
            safe_data[field_name] = '[FILTERED]'
    return safe_data


def contains_sensitive_keyword(text: str, sensitive_keywords: Optional[List[str]] = None) -> bool:
    """检查文本是否包含敏感关键词"""
    if sensitive_keywords is None:
        sensitive_keywords = ['key', 'token', 'password', 'secret', 'auth']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in sensitive_keywords)


def validate_id_format(value: str, param_name: str = "ID") -> Optional[str]:
    """校验 ID 格式，返回错误消息或 None"""
    if not value or not isinstance(value, str):
        return f"{param_name} 不能为空"
    if len(value) > MAX_ID_LENGTH:
        return f"{param_name} 长度超过限制({MAX_ID_LENGTH})"
    if not ID_PATTERN.match(value):
        return f"{param_name} 格式无效，仅允许字母、数字、下划线和连字符，且不能包含空格"
    return None


def validate_string_length(value, max_length: int, param_name: str = "参数") -> Optional[str]:
    """校验字符串长度，返回错误消息或 None"""
    if value is not None and isinstance(value, str) and len(value) > max_length:
        return f"{param_name} 长度超出限制({max_length})"
    return None


def validate_json_body(request) -> Tuple[Optional[dict], Optional[str]]:
    """安全获取 JSON body，返回 (data, error_msg)"""
    if not request.is_json:
        return None, "Content-Type 必须为 application/json"
    data = request.get_json(silent=True)
    if data is None:
        return None, "无效的 JSON 数据"
    return data, None


def validate_in_set(value, allowed: set, param_name: str = "参数") -> Optional[str]:
    """校验值是否在允许集合中"""
    if value not in allowed:
        return f"{param_name} 值无效，允许的值: {', '.join(str(v) for v in sorted(allowed))}"
    return None


def validate_numeric_range(value, min_val, max_val, param_name: str = "参数") -> Optional[str]:
    """校验数值是否在范围内"""
    if value < min_val or value > max_val:
        return f"{param_name} 超出范围 [{min_val}, {max_val}]"
    return None


def validate_project_name(name: Any, param_name: str = "项目名称") -> Optional[str]:
    """校验项目名称

    Args:
        name: 待校验的项目名称
        param_name: 参数名称（用于错误消息）

    Returns:
        Optional[str]: 校验失败返回错误消息，成功返回None
    """
    # 类型校验
    if not isinstance(name, str):
        return f"{param_name} 类型必须为字符串"

    # 非空校验
    if not name or not name.strip():
        return f"{param_name} 不能为空"

    trimmed_name = name.strip()

    # 长度校验
    if len(trimmed_name) < PROJECT_NAME_MIN_LENGTH:
        return f"{param_name} 长度不能少于 {PROJECT_NAME_MIN_LENGTH} 个字符"
    if len(trimmed_name) > PROJECT_NAME_MAX_LENGTH:
        return f"{param_name} 长度不能超过 {PROJECT_NAME_MAX_LENGTH} 个字符"

    # 字符校验
    if not PROJECT_NAME_PATTERN.match(trimmed_name):
        return f"{param_name} 包含非法字符，仅允许字母、数字、下划线、连字符和中文"

    return None


def convert_form_types(
    data: Dict[str, str],
    boolean_fields: List[str],
    numeric_fields: List[str]
) -> Dict[str, Any]:
    """转换表单数据类型"""
    result: Dict[str, Any] = dict(data)
    for field in boolean_fields:
        if field in result:
            result[field] = str(result[field]).lower() == "true"
    for field in numeric_fields:
        if field in result:
            try:
                value = str(result[field])
                num_value = float(value) if '.' in value else int(value)
                if isinstance(num_value, float) and (math.isnan(num_value) or math.isinf(num_value)):
                    raise ValueError(f"字段 '{field}' 的值无效: {value}")
                result[field] = num_value
            except ValueError:
                result[field] = 0
    return result
