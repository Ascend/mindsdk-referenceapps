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

from collections import OrderedDict
from typing import Any, Dict, List, Tuple, cast

import json
from flask import Blueprint, request, jsonify, Response

from backend.config.memory_config import MemoryConfig
from backend.utils.logger import init_logger
from backend.utils.response_utils import success_response, error_response, server_error_response
from backend.utils.validation_utils import (
    filter_sensitive_fields,
    convert_form_types,
    validate_string_length,
    validate_in_set,
    validate_numeric_range,
)
from backend.models.constants import (
    DEFAULT_CONFIG_PATH,
    ENCODING_UTF8,
    HTTP_OK,
    JSON_INDENT,
    CONFIG_BOOLEAN_FIELDS,
    CONFIG_NUMERIC_FIELDS,
    SENSITIVE_FIELD_NAMES,
    ALLOWED_CONFIG_FIELDS,
    CONFIG_NUMERIC_RANGES,
    MAX_CONFIG_STRING_LENGTH,
    MAX_CONFIG_PROMPT_LENGTH,
    CONFIG_ENUM_FIELDS,
    CONFIG_LLM_API_KEY_FIELD,
    CONFIG_STORED_IN_MEMORY_PLACEHOLDER,
    CONFIG_FILTERED_PLACEHOLDER,
)

config_bp = Blueprint('config', __name__)

logger = init_logger(__name__)


@config_bp.route('/config', methods=['GET', 'POST'])
def config_route() -> Tuple[Response, int]:
    """
    配置管理路由

    GET: 获取当前配置
    POST: 更新配置
    """
    # 配置路由入口：根据请求方法分派处理逻辑
    logger.info(f"Config access requested from IP: {request.remote_addr}, method: {request.method}")

    if request.method == 'GET':
        return _handle_config_get()
    return _handle_config_post()


def _handle_config_get() -> Tuple[Response, int]:
    """
    处理配置读取请求

    Returns:
        Tuple[Response, int]: 配置数据或错误响应
    """
    # 核心步骤：加载配置并过滤敏感字段后返回
    try:
        logger.debug('config_read', 'started', {'config_path': DEFAULT_CONFIG_PATH})

        config_data = _load_config_file()
        safe_config = filter_sensitive_fields(config_data, SENSITIVE_FIELD_NAMES)

        logger.debug(
            'config_read',
            'completed',
            {'config_path': DEFAULT_CONFIG_PATH, 'fields': list(safe_config.keys())}
        )
        # 返回过滤后的配置，避免泄露敏感信息（如 API 密钥）
        return jsonify(safe_config), HTTP_OK
    except Exception:
        logger.error(f"Failed to load config from {DEFAULT_CONFIG_PATH}", exc_info=True)
        return server_error_response("Error loading configuration")


def _handle_config_post() -> Tuple[Response, int]:
    """处理配置更新请求"""
    try:
        # 读取并过滤允许更新的字段
        data = _filter_allowed_fields(request.form.to_dict())

        converted_data, conv_err = _convert_config_data(data)
        if conv_err:
            return conv_err
        # 确保转换结果非空，防止后续处理出现 None 类型错误
        if converted_data is None:
            return error_response('Invalid configuration data after conversion')

        # 校验字段合法性（数值、长度、枚举等）
        validation_err = _validate_config_values(cast(Dict[str, Any], converted_data))
        if validation_err:
            return validation_err

        existing_config = _load_or_create_config()
        updated_fields = _merge_and_log_config(existing_config, cast(Dict[str, Any], converted_data))
        _save_config_file(existing_config)

        # 日志：更新的字段信息，隐藏敏感信息
        logger.debug('config_update', 'completed', {'updated_fields': updated_fields})
        return success_response('Configuration saved successfully')
    except Exception:
        logger.error("Failed to update config", exc_info=True)
        return server_error_response("Error updating configuration")


def _filter_allowed_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """过滤不在白名单中的配置字段"""
    unknown_fields = [k for k in data if k not in ALLOWED_CONFIG_FIELDS]
    if unknown_fields:
        logger.warning(f"Unknown config fields filtered out: {unknown_fields}")
    return {k: v for k, v in data.items() if k in ALLOWED_CONFIG_FIELDS}


def _convert_config_data(data: Dict[str, Any]):
    """转换配置数据类型，返回 (converted_data, error_response 或 None)"""
    try:
        converted = convert_form_types(data, CONFIG_BOOLEAN_FIELDS, CONFIG_NUMERIC_FIELDS)
        return converted, None
    except ValueError as e:
        logger.warning(f"Invalid numeric value in config update: {e}")
        return None, error_response(str(e))


def _validate_config_values(data: Dict[str, Any]):
    """校验配置数值范围、字符串长度和枚举字段，返回 error_response 或 None"""
    for field, (min_val, max_val) in CONFIG_NUMERIC_RANGES.items():
        if field in data:
            err = validate_numeric_range(data[field], min_val, max_val, field)
            if err:
                return error_response(err)

    for key, value in data.items():
        if isinstance(value, str):
            max_config_length = MAX_CONFIG_PROMPT_LENGTH if "prompt" in key else MAX_CONFIG_STRING_LENGTH
            err = validate_string_length(value, max_config_length, key)
            if err:
                return error_response(err)

    for field_name, allowed_values in CONFIG_ENUM_FIELDS.items():
        if field_name in data:
            err = validate_in_set(data[field_name], allowed_values, field_name)
            if err:
                return error_response(err)

    return None


def _load_config_file() -> Dict[str, Any]:
    """
    加载配置文件

    Returns:
        Dict[str, Any]: 配置数据字典
    """
    with open(DEFAULT_CONFIG_PATH, 'r', encoding=ENCODING_UTF8) as f:
        return json.load(f, object_pairs_hook=OrderedDict)


def _load_or_create_config() -> OrderedDict:
    """
    加载现有配置或创建空配置

    Returns:
        OrderedDict: 配置数据
    """
    try:
        with open(DEFAULT_CONFIG_PATH, 'r', encoding=ENCODING_UTF8) as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    except Exception:
        return OrderedDict()


def _merge_and_log_config(
    existing_config: OrderedDict,
    new_data: Dict[str, Any]
) -> List[str]:
    """
    合并配置并记录更新字段

    Args:
        existing_config: 现有配置
        new_data: 新数据

    Returns:
        List[str]: 更新字段列表（敏感信息已过滤）
    """
    updated_fields = []
    for key, value in new_data.items():
        if key == CONFIG_LLM_API_KEY_FIELD:
            MemoryConfig.set_llm_api_key(value if value else None)
            stored = "stored" if value else "cleared"
            logger.info(f"API KEY {stored} in memory")
            updated_fields.append(f"{key}={CONFIG_STORED_IN_MEMORY_PLACEHOLDER}")
            continue
        existing_config[key] = value
        if key in SENSITIVE_FIELD_NAMES:
            updated_fields.append(f"{key}={CONFIG_FILTERED_PLACEHOLDER}")
        else:
            updated_fields.append(f"{key}={value}")
    return updated_fields


def _save_config_file(config_data: OrderedDict) -> None:
    """
    保存配置文件

    Args:
        config_data: 要保存的配置数据
    """
    with open(DEFAULT_CONFIG_PATH, 'w', encoding=ENCODING_UTF8) as f:
        json.dump(config_data, f, ensure_ascii=False, indent=JSON_INDENT)
