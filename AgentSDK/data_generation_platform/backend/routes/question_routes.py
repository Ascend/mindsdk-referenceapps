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

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, request, jsonify, Response

from backend.config.config import Config
from backend.utils.logger import init_logger
from backend.utils.response_utils import (
    success_response,
    error_response,
    server_error_response,
    not_found_response,
    missing_param_response,
    partial_success_response,
)
from backend.utils.validation_utils import (
    get_pagination_params,
    calculate_pagination_info,
    paginate_list,
    validate_id_format,
    validate_string_length,
    validate_json_body,
    validate_in_set,
)
from backend.models.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_QUESTIONS_DIR,
    ENCODING_UTF8,
    HTTP_OK,
    JSON_INDENT,
    QUESTION_UPDATABLE_FIELDS,
    MAX_STRING_FIELD_LENGTH,
    MAX_BATCH_SIZE,
    ALLOWED_QUESTION_STATUS,
    QUESTION_STATS_INITIAL,
    DEFAULT_QUESTION_STATUS,
    FIELD_ID,
    FIELD_PROJECT_ID,
    FIELD_QUESTION_ID,
    FIELD_QUESTION_IDS,
    FIELD_CONTENT,
    FIELD_ANSWER,
    FIELD_CHAIN_OF_THOUGHT,
    FIELD_STATUS,
    RESPONSE_STATUS_SUCCESS,
    BATCH_ERROR_EXCEEDS_LIMIT,
    BATCH_ERROR_QUESTION_IDS_LIST,
    MSG_INVALID_REQUEST_BODY,
    MSG_STATUS_MUST_BE_INTEGER,
    MSG_QUESTION_FILE_NOT_FOUND,
    MSG_QUESTION_UPDATED_SUCCESS,
    MSG_QUESTION_DELETED_SUCCESS,
    MSG_DELETE_BATCH_RESULT,
    LOG_OPERATION_FILE_DELETE,
    LOG_OPERATION_DELETE_QUESTION,
    LOG_FIELD_OPERATION,
    LOG_FIELD_PROJECT_ID,
    LOG_FIELD_QUESTION_ID,
    LOG_FIELD_REMOTE_ADDR,
    LOG_FIELD_SUCCESS,
)

question_bp = Blueprint('question', __name__)

logger = init_logger(__name__)


@question_bp.route('/project_questions', methods=['GET'])
def get_project_questions() -> Tuple[Response, int]:
    """项目问题列表路由"""
    # 功能说明：按项目分页获取问题列表，支持状态过滤
    try:
        project_id = request.args.get(FIELD_PROJECT_ID)
        if not project_id:
            logger.warning("Missing project_id parameter in get_project_questions request")
            return missing_param_response(FIELD_PROJECT_ID)

        id_err = validate_id_format(project_id, FIELD_PROJECT_ID)
        if id_err:
            return error_response(id_err)

        page, per_page, status_filter = get_pagination_params(request)

        logger.debug(
            'question_list',
            'started',
            {
                'project_id': project_id,
                'page': page,
                'per_page': per_page,
                'status_filter': status_filter,
                'remote_addr': request.remote_addr
            }
        )

        config = Config.load(DEFAULT_CONFIG_PATH)
        queries_dir = os.path.join(config.data_dir, project_id, DEFAULT_QUESTIONS_DIR)

        questions = _load_questions_from_directory(queries_dir, status_filter)
        paginated_questions = paginate_list(questions, page, per_page)
        pagination_info = calculate_pagination_info(len(questions), page, per_page)

        logger.debug(
            'question_list',
            'completed',
            {
                'project_id': project_id,
                'total_questions': len(questions),
                'returned_questions': len(paginated_questions),
                'page': page,
                'success': True
            }
        )

        return jsonify({
            "status": RESPONSE_STATUS_SUCCESS,
            "data": paginated_questions,
            "pagination": pagination_info
        }), HTTP_OK
    except Exception as e:
        logger.error("Failed to get project questions", exc_info=False)
        return server_error_response(str(e))


@question_bp.route('/project_question_stats', methods=['GET'])
def get_project_question_stats() -> Tuple[Response, int]:
    """问题统计路由"""
    # 功能说明：返回指定项目的问题统计信息
    try:
        project_id = request.args.get(FIELD_PROJECT_ID)
        if not project_id:
            logger.warning(f"Project question stats request without project_id")
            return missing_param_response(FIELD_PROJECT_ID)

        id_err = validate_id_format(project_id, FIELD_PROJECT_ID)
        if id_err:
            return error_response(id_err)

        logger.debug(
            'question_stats',
            'started',
            {'project_id': project_id, 'remote_addr': request.remote_addr}
        )

        config = Config.load(DEFAULT_CONFIG_PATH)
        queries_dir = os.path.join(config.data_dir, project_id, DEFAULT_QUESTIONS_DIR)

        stats = _calculate_question_stats(queries_dir)

        logger.debug(
            'question_stats',
            'completed',
            {'project_id': project_id, 'stats': stats, 'success': True}
        )
        return success_response(data=stats)
    except Exception as e:
        logger.error("Failed to get question stats", exc_info=True)
        return server_error_response(str(e))


@question_bp.route('/update_question', methods=['POST'])
def update_question() -> Tuple[Response, int]:
    """问题更新路由"""
    # 功能说明：更新指定问题的可更新字段
    logger.info(f"Question update requested from IP: {request.remote_addr}")

    data, json_err = validate_json_body(request)
    if json_err:
        return error_response(json_err)
    # 数据体类型检查，确保为字典
    if not isinstance(data, dict):
        return error_response(MSG_INVALID_REQUEST_BODY)

    project_id = data.get(FIELD_PROJECT_ID)
    question_id = data.get(FIELD_QUESTION_ID)

    if not project_id or not question_id:
        logger.warning("Missing project_id or question_id parameter")
        return missing_param_response('project_id or question_id')

    for param_name, param_val in [(FIELD_PROJECT_ID, project_id), (FIELD_QUESTION_ID, question_id)]:
        id_err = validate_id_format(param_val, param_name)
        if id_err:
            return error_response(id_err)

    # 校验字符串字段长度
    for field in (FIELD_CONTENT, FIELD_ANSWER, FIELD_CHAIN_OF_THOUGHT):
        err = validate_string_length(data.get(field), MAX_STRING_FIELD_LENGTH, field)
        if err:
            return error_response(err)

    # 校验 status 范围
    if FIELD_STATUS in data:
        try:
            status_val = int(data[FIELD_STATUS])
        except (ValueError, TypeError):
            return error_response(MSG_STATUS_MUST_BE_INTEGER)
        err = validate_in_set(status_val, ALLOWED_QUESTION_STATUS, FIELD_STATUS)
        if err:
            return error_response(err)

    logger.debug(
        'file_write',
        'started',
        {
            'operation': 'update_question',
            'project_id': project_id,
            'question_id': question_id,
            'remote_addr': request.remote_addr
        }
    )

    config = Config.load(DEFAULT_CONFIG_PATH)
    query_path = os.path.join(
        config.data_dir, project_id, DEFAULT_QUESTIONS_DIR, f'{question_id}.json'
    )

    if not os.path.exists(query_path):
        logger.warning(f"Question file not found: {query_path}")
        return not_found_response('Question file not found')

    try:
        updated_fields = _update_question_file(query_path, data)

        logger.debug(
            'file_write',
            'completed',
            {
                'operation': 'update_question',
                'project_id': project_id,
                'question_id': question_id,
                'updated_fields': updated_fields,
                'success': True
            }
        )
        return success_response('Question updated successfully')
    except Exception as e:
        logger.error("Failed to update question", exc_info=False)
        return server_error_response(str(e))


@question_bp.route('/delete_question', methods=['POST'])
def delete_question() -> Tuple[Response, int]:
    """删除单个问题路由"""
    # 功能说明：删除指定的问题记录
    logger.info(f"Question deletion requested from IP: {request.remote_addr}")

    try:
        data, json_err = validate_json_body(request)
        if json_err:
            return error_response(json_err)
        if not isinstance(data, dict):
            return error_response(MSG_INVALID_REQUEST_BODY)

        project_id = data.get(FIELD_PROJECT_ID)
        question_id = data.get(FIELD_QUESTION_ID)

        if not project_id or not question_id:
            logger.warning("Missing project_id or question_id parameter")
            return missing_param_response('project_id or question_id')

        for param_name, param_val in [(FIELD_PROJECT_ID, project_id), (FIELD_QUESTION_ID, question_id)]:
            id_err = validate_id_format(param_val, param_name)
            if id_err:
                return error_response(id_err)

        logger.debug(
            LOG_OPERATION_FILE_DELETE,
            'started',
            {
                LOG_FIELD_OPERATION: LOG_OPERATION_DELETE_QUESTION,
                LOG_FIELD_PROJECT_ID: project_id,
                LOG_FIELD_QUESTION_ID: question_id,
                LOG_FIELD_REMOTE_ADDR: request.remote_addr
            }
        )

        config = Config.load(DEFAULT_CONFIG_PATH)
        query_path = os.path.join(
            config.data_dir, project_id, DEFAULT_QUESTIONS_DIR, f'{question_id}.json'
        )

        if not os.path.exists(query_path):
            logger.warning(f"Question file not found for deletion: {query_path}")
            return not_found_response(MSG_QUESTION_FILE_NOT_FOUND)

        os.remove(query_path)

        logger.debug(
            LOG_OPERATION_FILE_DELETE,
            'completed',
            {
                LOG_FIELD_OPERATION: LOG_OPERATION_DELETE_QUESTION,
                LOG_FIELD_PROJECT_ID: project_id,
                LOG_FIELD_QUESTION_ID: question_id,
                LOG_FIELD_SUCCESS: True
            }
        )
        return success_response(MSG_QUESTION_DELETED_SUCCESS)
    except Exception as e:
        logger.error("Failed to delete question", exc_info=False)
        return server_error_response(str(e))


@question_bp.route('/delete_questions', methods=['POST'])
def delete_questions() -> Tuple[Response, int]:
    """批量删除问题路由"""
    # 功能说明：批量删除指定的多个问题
    try:
        data, json_err = validate_json_body(request)
        if json_err:
            return error_response(json_err)

        project_id = data.get(FIELD_PROJECT_ID)
        question_ids = data.get(FIELD_QUESTION_IDS)

        if not project_id or not question_ids:
            logger.warning("Missing project_id or question_ids parameter")
            return missing_param_response('project_id or question_ids')

        if not isinstance(question_ids, list):
            logger.warning("question_ids must be a list")
            return error_response(BATCH_ERROR_QUESTION_IDS_LIST)

        # project_id 格式校验
        id_err = validate_id_format(project_id, FIELD_PROJECT_ID)
        if id_err:
            return error_response(id_err)

        # 批量上限校验
        if len(question_ids) > MAX_BATCH_SIZE:
            return error_response(BATCH_ERROR_EXCEEDS_LIMIT.format(MAX_BATCH_SIZE))

        # 每个 question_id 格式校验
        for qid in question_ids:
            id_err = validate_id_format(str(qid), FIELD_QUESTION_ID)
            if id_err:
                return error_response(id_err)

        logger.debug(
            'file_batch_delete',
            'started',
            {'project_id': project_id, 'question_ids_count': len(question_ids)}
        )

        config = Config.load(DEFAULT_CONFIG_PATH)
        success_count, errors = _batch_delete_questions(
            config.data_dir, project_id, question_ids
        )

        logger.debug(
            'file_batch_delete',
            'completed',
            {
                'project_id': project_id,
                'total_count': len(question_ids),
                'success_count': success_count,
                'error_count': len(errors),
                'success': True
            }
        )

        if errors:
            return partial_success_response(
                f'Deleted {success_count} questions, but encountered {len(errors)} errors',
                success_count,
                errors
            )
        return jsonify({
            'status': 'success',
            'message': f"Successfully deleted {success_count} questions",
            'deleted_count': success_count
        }), HTTP_OK
    except Exception as e:
        logger.error("Failed to batch delete questions", exc_info=False)
        return server_error_response(str(e))


def _load_questions_from_directory(
    queries_dir: str,
    status_filter: Optional[int]
) -> List[Dict[str, Any]]:
    """
    从目录加载问题列表

    Args:
        queries_dir: 问题目录路径
        status_filter: 状态过滤值

    Returns:
        List[Dict[str, Any]]: 问题信息列表
    """
    questions = []
    if not os.path.exists(queries_dir):
        return questions

    for question_file in os.listdir(queries_dir):
        if question_file.endswith('.json'):
            question_path = os.path.join(queries_dir, question_file)
            question_info = _load_single_question(question_path, status_filter)
            if question_info:
                questions.append(question_info)
    return questions


def _load_single_question(
    question_path: str,
    status_filter: Optional[int]
) -> Optional[Dict[str, Any]]:
    """
    加载单个问题

    Args:
        question_path: 问题文件路径
        status_filter: 状态过滤值

    Returns:
        Optional[Dict[str, Any]]: 问题信息或None
    """
    try:
        with open(question_path, 'r', encoding=ENCODING_UTF8) as f:
            question_data = json.load(f)

        if status_filter is not None and question_data.get(FIELD_STATUS, DEFAULT_QUESTION_STATUS) != status_filter:
            return None

        return {
            FIELD_ID: question_data.get(FIELD_ID),
            FIELD_CONTENT: question_data.get(FIELD_CONTENT),
            FIELD_ANSWER: question_data.get(FIELD_ANSWER),
            FIELD_CHAIN_OF_THOUGHT: question_data.get(FIELD_CHAIN_OF_THOUGHT),
            FIELD_STATUS: question_data.get(FIELD_STATUS, DEFAULT_QUESTION_STATUS)
        }
    except Exception:
        return None


def _calculate_question_stats(queries_dir: str) -> Dict[int, int]:
    """
    计算问题统计

    Args:
        queries_dir: 问题目录路径

    Returns:
        Dict[int, int]: 状态统计字典
    """
    stats = dict(QUESTION_STATS_INITIAL)
    if not os.path.exists(queries_dir):
        return stats

    for filename in os.listdir(queries_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(queries_dir, filename)
            try:
                with open(filepath, 'r', encoding=ENCODING_UTF8) as f:
                    query_data = json.load(f)
                status = query_data.get('status', 0)
                if status in stats:
                    stats[status] += 1
            except Exception:
                logger.warning(f"Failed to load query from {filepath}")
                continue
    return stats


def _update_question_file(
    query_path: str,
    data: Dict[str, Any]
) -> List[str]:
    """
    更新问题文件

    Args:
        query_path: 问题文件路径
        data: 更新数据

    Returns:
        List[str]: 更新的字段列表
    """
    with open(query_path, 'r', encoding=ENCODING_UTF8) as f:
        query_data = json.load(f)

    updated_fields = []
    for field in QUESTION_UPDATABLE_FIELDS:
        if field in data:
            updated_fields.append(field)
            if field == FIELD_STATUS:
                query_data[field] = int(data[field])
            else:
                query_data[field] = data[field]

    with open(query_path, 'w', encoding=ENCODING_UTF8) as f:
        json.dump(query_data, f, ensure_ascii=False, indent=JSON_INDENT)

    return updated_fields


def _batch_delete_questions(
    data_dir: str,
    project_id: str,
    question_ids: List[str]
) -> Tuple[int, List[str]]:
    """
    批量删除问题

    Args:
        data_dir: 数据目录
        project_id: 项目ID
        question_ids: 问题ID列表

    Returns:
        Tuple[int, List[str]]: (成功数量, 错误列表)
    """
    success_count = 0
    errors = []

    for question_id in question_ids:
        query_path = os.path.join(
            data_dir, project_id, DEFAULT_QUESTIONS_DIR, f'{question_id}.json'
        )
        if os.path.exists(query_path):
            try:
                os.remove(query_path)
                success_count += 1
            except Exception as e:
                errors.append(f'Failed to remove {question_id}: {str(e)}')
        else:
            errors.append(f'Question {question_id} not found')

    return success_count, errors
