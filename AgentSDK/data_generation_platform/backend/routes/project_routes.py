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

from flask import Blueprint, request, Response

from backend.config.config import Config
from backend.services.project_service import ProjectService
from backend.utils.logger import init_logger
from backend.utils.response_utils import (
    success_response,
    error_response,
    server_error_response,
    not_found_response,
    missing_param_response,
)
from backend.utils.validation_utils import validate_id_format, validate_json_body
from backend.utils.file_validator import validate_path_security
from backend.models.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROJECTS_DIR,
    ENCODING_UTF8,
    FIELD_ID,
    FIELD_NAME,
    FIELD_DESCRIPTION,
    FIELD_PROJECT_ID,
    LOG_OPERATION_PROJECT_LIST,
    LOG_OPERATION_PROJECT_DELETE,
    LOG_FIELD_PROJECTS_DIR,
    LOG_FIELD_PROJECTS_COUNT,
    LOG_FIELD_SUCCESS,
    LOG_FIELD_PROJECT_ID,
    LOG_FIELD_PROJECT_PATH,
    LOG_FIELD_PROJECT_DATA_PATH,
    LOG_FIELD_REMOTE_ADDR,
    LOG_FIELD_OPERATION,
    LOG_OPERATION_GET_PROJECTS,
)

project_bp = Blueprint('project', __name__)

logger = init_logger(__name__)


# ==================== 公开路由函数 ====================

@project_bp.route('/projects', methods=['GET'])
def get_projects() -> Tuple[Response, int]:
    """项目列表路由 - 获取所有项目列表"""
    try:
        logger.debug(LOG_OPERATION_PROJECT_LIST, LOG_OPERATION_GET_PROJECTS, {LOG_FIELD_OPERATION: LOG_OPERATION_GET_PROJECTS})

        # 从配置加载数据目录路径
        config = Config.load(DEFAULT_CONFIG_PATH)
        # 归一化路径，处理 Windows 风格相对路径（如 .\data）在 Linux 上的问题
        data_dir = os.path.normpath(config.data_dir)
        projects_dir = os.path.join(data_dir, DEFAULT_PROJECTS_DIR)

        # 检查项目目录是否存在，不存在则返回空列表
        if not os.path.exists(projects_dir):
            logger.debug(
                LOG_OPERATION_PROJECT_LIST,
                LOG_OPERATION_GET_PROJECTS,
                {LOG_FIELD_PROJECTS_DIR: projects_dir, LOG_FIELD_PROJECTS_COUNT: 0, LOG_FIELD_SUCCESS: True}
            )
            return success_response(data=[])

        # 遍历项目目录加载所有项目信息
        projects = _load_projects_from_directory(projects_dir)

        logger.debug(
            LOG_OPERATION_PROJECT_LIST,
            LOG_OPERATION_GET_PROJECTS,
            {LOG_FIELD_PROJECTS_DIR: projects_dir, LOG_FIELD_PROJECTS_COUNT: len(projects), LOG_FIELD_SUCCESS: True}
        )
        return success_response(data=projects)
    except Exception as e:
        logger.error("Failed to get projects", exc_info=False)
        return server_error_response(str(e))


@project_bp.route('/delete_project', methods=['POST'])
def delete_project() -> Tuple[Response, int]:
    """删除项目路由"""
    logger.info(f"Project deletion requested from IP: {request.remote_addr}")

    try:
        data, json_err = validate_json_body(request)
        if json_err:
            return error_response(json_err)

        project_id = data.get(FIELD_PROJECT_ID)

        if not project_id:
            logger.warning("Missing project_id parameter in delete_project request")
            return missing_param_response(FIELD_PROJECT_ID)

        id_err = validate_id_format(project_id, FIELD_PROJECT_ID)
        if id_err:
            return error_response(id_err)

        config = Config.load(DEFAULT_CONFIG_PATH)
        data_dir = config.data_dir

        is_valid, error_msg = validate_path_security(project_id, data_dir)
        if not is_valid:
            logger.warning(f"Path security validation failed for project deletion: {error_msg}")
            return error_response(error_msg)

        logger.debug(
            LOG_OPERATION_PROJECT_DELETE,
            'started',
            {LOG_FIELD_PROJECT_ID: project_id, LOG_FIELD_REMOTE_ADDR: request.remote_addr}
        )

        # 归一化路径，处理 Windows 风格相对路径（如 .\data）在 Linux 上的问题
        data_dir = os.path.normpath(config.data_dir)
        project_path = os.path.join(data_dir, DEFAULT_PROJECTS_DIR, project_id)
        project_data_path = os.path.join(data_dir, project_id)

        if not os.path.exists(project_path):
            logger.warning(f"Project directory not found for deletion: {project_path}")
            return not_found_response('Project directory not found')

        project_service = ProjectService(data_dir)
        if not project_service.delete_project(project_id):
            logger.error(f"Service failed to delete project: {project_id}")
            return server_error_response("Failed to delete project")

        logger.debug(
            LOG_OPERATION_PROJECT_DELETE,
            'completed',
            {
                LOG_FIELD_PROJECT_ID: project_id,
                LOG_FIELD_PROJECT_PATH: project_path,
                LOG_FIELD_PROJECT_DATA_PATH: project_data_path,
                LOG_FIELD_SUCCESS: True
            }
        )
        return success_response('Project deleted successfully')
    except Exception as e:
        logger.error("Failed to delete project", exc_info=False)
        return server_error_response(str(e))

# ==================== 内部辅助函数 ====================

def _load_projects_from_directory(projects_dir: str) -> List[Dict[str, Any]]:
    """从目录加载项目列表 - 遍历目录获取所有项目"""
    projects = []
    for item in os.listdir(projects_dir):
        project_path = os.path.join(projects_dir, item)
        if os.path.isdir(project_path):
            project_info = _load_single_project(project_path)
            if project_info:
                projects.append(project_info)
    return projects


def _load_single_project(project_path: str) -> Optional[Dict[str, Any]]:
    """加载单个项目信息 - 读取project.json文件"""
    # 查找项目配置文件
    project_json_path = os.path.join(project_path, 'project.json')
    if not os.path.exists(project_json_path):
        return None

    try:
        # 解析JSON获取项目基本信息
        with open(project_json_path, 'r', encoding=ENCODING_UTF8) as f:
            project_data = json.load(f)

        return {
            FIELD_ID: project_data.get(FIELD_ID),
            FIELD_NAME: project_data.get(FIELD_NAME),
            FIELD_DESCRIPTION: project_data.get(FIELD_DESCRIPTION, '')
        }
    except Exception:
        return None
