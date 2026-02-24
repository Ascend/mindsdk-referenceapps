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
import shutil
import uuid
from typing import Optional, List, Dict, Any

import json

from backend.models.project import Project
from backend.utils.file_utils import read_file, save_file
from backend.utils.validation_utils import validate_project_name
from backend.models.constants import (
    ENCODING_UTF8,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    DEFAULT_PROJECTS_DIR,
)
from backend.utils.logger import init_logger

logger = init_logger(__name__)

# ==================== 文件名常量 ====================
PROJECT_CONFIG_FILENAME = "project.json"


class ProjectService:
    """
    项目服务类，管理项目的整个生命周期

    Attributes:
        data_dir: 数据存储目录路径
        config: 配置字典
        projects_dir: 项目存储目录路径
    """

    def __init__(self, data_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化项目管理工作区

        Args:
            data_dir: 数据存储目录路径
            config: 配置字典 (默认None)
        """
        self.data_dir = data_dir
        self.config = config or {}
        self.projects_dir = os.path.join(data_dir, DEFAULT_PROJECTS_DIR)
        os.makedirs(self.projects_dir, exist_ok=True)

    @staticmethod
    def _generate_unique_id() -> str:
        """
        生成唯一ID

        Returns:
            str: UUID字符串
        """
        return str(uuid.uuid4())

    def get_projects(self) -> List[Project]:
        """
        获取所有项目

        Returns:
            List[Project]: 项目列表
        """
        # 收集当前根目录下的所有项目信息
        projects = []

        if not os.path.exists(self.projects_dir):
            return projects

        for project_dir_name in os.listdir(self.projects_dir):
            project = self._load_project_from_dir(project_dir_name)
            if project:
                projects.append(project)

        return projects

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        根据ID获取单个项目

        Args:
            project_id: 项目ID

        Returns:
            Optional[Project]: 找到的项目对象或None
        """
        # 根据ID定位到项目配置文件
        project_file = self._get_project_config_path(project_id)

        if not os.path.exists(project_file):
            return None

        try:
            with open(project_file, 'r', encoding=ENCODING_UTF8) as f:
                project_data = json.load(f)

            project = Project.from_dict(project_data)
            project.id = project_id
            return project
        except Exception as e:
            logger.warning(f"读取项目失败 {project_id}: {e}")
            return None

    def get_or_create_project(self, name: str) -> Project:
        """
        获取或创建项目

        Args:
            name: 项目名称

        Returns:
            Project: 项目对象(可能是已存在的或新创建的)

        Raises:
            ValueError: 项目名称校验失败
        """
        # 校验项目名称
        name_error = validate_project_name(name)
        if name_error:
            logger.warning(f"项目名称校验失败: {name_error}")
            raise ValueError(name_error)

        existing_project = self._find_project_by_name(name)
        if existing_project:
            return existing_project

        return self._create_new_project(name)

    def update_project(self, project: Project) -> Project:
        """
        更新项目详情

        Args:
            project: 要更新的项目对象

        Returns:
            Project: 更新后的项目对象
        """
        self._save_project(project)
        return project

    def delete_project(self, project_id: str) -> bool:
        """
        删除项目

        Args:
            project_id: 项目ID

        Returns:
            bool: 删除是否成功
        """
        project_config_dir = os.path.join(self.projects_dir, project_id)
        project_data_dir = os.path.join(self.data_dir, project_id)

        if not os.path.exists(project_config_dir):
            logger.warning(f"项目目录不存在: {project_id}")
            return False

        try:
            for target_dir in (project_config_dir, project_data_dir):
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)

            logger.info(f"成功删除项目及数据目录: {project_id}")
            return True
        except Exception as e:
            logger.error(f"删除项目失败 {project_id}: {e}")
            return False

    def _load_project_from_dir(self, project_dir_name: str) -> Optional[Project]:
        """
        从目录加载项目

        Args:
            project_dir_name: 项目目录名

        Returns:
            Optional[Project]: 项目对象或None
        """
        project_dir = os.path.join(self.projects_dir, project_dir_name)

        if not os.path.isdir(project_dir):
            return None

        project_file = os.path.join(project_dir, PROJECT_CONFIG_FILENAME)

        if not os.path.exists(project_file):
            return None

        try:
            project_data = read_file(project_file, "json")
            project = Project.from_dict(project_data)  # type: ignore
            project.id = project_dir_name
            return project
        except Exception as e:
            logger.warning(f"加载项目失败 {project_dir_name}: {e}")
            return None

    def _get_project_config_path(self, project_id: str) -> str:
        """
        获取项目配置文件路径

        Args:
            project_id: 项目ID

        Returns:
            str: 项目配置文件的完整路径
        """
        project_dir = os.path.join(self.projects_dir, project_id)
        return os.path.join(project_dir, PROJECT_CONFIG_FILENAME)

    def _find_project_by_name(self, name: str) -> Optional[Project]:
        """
        按名称查找项目

        Args:
            name: 项目名称

        Returns:
            Optional[Project]: 找到的项目或None
        """
        all_projects = self.get_projects()
        for project in all_projects:
            if project.name == name:
                return project
        return None

    def _create_new_project(self, name: str) -> Project:
        """
        创建新项目

        Args:
            name: 项目名称

        Returns:
            Project: 创建的项目对象
        """
        project = Project(
            name=name,
            description=f"自动创建的项目: {name}",
            llm_provider=self.config.get("llm_provider", DEFAULT_LLM_PROVIDER),
            api_key=self.config.get("llm_api_key"),
            model_name=self.config.get("llm_model", DEFAULT_LLM_MODEL),
        )

        project.id = self._generate_unique_id()
        self._save_project(project)

        return project

    def _save_project(self, project: Project) -> None:
        """
        保存项目到磁盘

        Args:
            project: 要保存的项目对象
        """
        project_dir = os.path.join(self.projects_dir, str(project.id))
        os.makedirs(project_dir, exist_ok=True)

        project_file = os.path.join(project_dir, PROJECT_CONFIG_FILENAME)
        save_file(project_file, project.to_dict(), base_dir=self.data_dir)
