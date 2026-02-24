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

from typing import Optional, List, Dict, Any, Union

from backend.models.question import Question
from backend.models.constants import (
    DEFAULT_DATASET_FORMAT,
    DEFAULT_DATASET_FILE_TYPE,
    FIELD_ID,
    FIELD_PROJECT_ID,
    FIELD_NAME,
    FIELD_FORMAT,
    FIELD_FILE_TYPE,
    FIELD_SYSTEM_PROMPT,
    FIELD_QUESTIONS,
)
from backend.utils.logger import init_logger

logger = init_logger(__name__)


def _parse_questions_data(questions_data: List[Any]) -> List[Question]:
    """
    解析questions数据，处理不同格式

    Args:
        questions_data: 问题数据列表（可能是字典列表或其他格式）

    Returns:
        List[Question]: 解析后的Question对象列表
    """
    if not questions_data or not isinstance(questions_data, list):
        return []

    if not questions_data:
        return []

    # 检查是否为字典格式
    if isinstance(questions_data[0], dict):
        try:
            return [Question.from_dict(q) for q in questions_data]
        except Exception as e:
            logger.warning(f"解析问题数据时出错: {e}")
            return []

    # 旧格式或其他格式
    logger.warning("检测到已弃用的问题格式")
    return []


class Dataset:
    """
    数据集类，用于管理数据集

    Attributes:
        id: 数据集唯一标识符
        project_id: 所属项目ID
        name: 数据集名称
        format: 数据格式 (alpaca/sharegpt/custom)
        file_type: 文件类型 (json/jsonl)
        system_prompt: 系统提示词
        questions: 关联的问题列表
    """

    def __init__(
        self,
        id: Optional[Union[int, str]] = None,
        project_id: Optional[Union[int, str]] = None,
        name: Optional[str] = None,
        format: str = DEFAULT_DATASET_FORMAT,
        file_type: str = DEFAULT_DATASET_FILE_TYPE,
        system_prompt: Optional[str] = None,
    ):
        """
        初始化数据仓库实例

        Args:
            id: 数据集唯一标识符
            project_id: 所属项目ID
            name: 数据集名称
            format: 数据格式，默认"alpaca"，可选"sharegpt"
            file_type: 文件类型，默认"json"，可选"jsonl"
            system_prompt: 系统提示词
        """
        # 关键字段：数据集标识与元信息
        self.id = id
        self.project_id = project_id  # 所属项目ID
        self.name = name  # 数据集名称
        self.format = format  # 数据格式（alpaca/sharegpt/custom）
        self.file_type = file_type  # 文件类型（json/jsonl）
        self.system_prompt = system_prompt  # 系统提示词
        self.questions: List[Question] = []  # 关联的问题列表

    @classmethod
    def from_dict(
        cls,
        data: Optional[Dict[str, Any]],
        questions: Optional[List[Question]] = None,
    ) -> 'Dataset':
        """
        从字典创建Dataset实例

        Args:
            data: 数据字典
            questions: 可选的问题列表

        Returns:
            Dataset: 创建的实例

        Raises:
            ValueError: data为None时抛出
        """
        if data is None:
            raise ValueError("数据不能为None")

        instance = cls(
            id=data.get(FIELD_ID),
            project_id=data.get(FIELD_PROJECT_ID),
            name=data.get(FIELD_NAME),
            format=data.get(FIELD_FORMAT, DEFAULT_DATASET_FORMAT),
            file_type=data.get(FIELD_FILE_TYPE, DEFAULT_DATASET_FILE_TYPE),
            system_prompt=data.get(FIELD_SYSTEM_PROMPT),
        )

        # 处理questions数据
        repo_questions = questions or []
        questions_data = data.get(FIELD_QUESTIONS, [])
        if questions_data:
            repo_questions = _parse_questions_data(questions_data)

        instance.questions = repo_questions
        return instance

    def to_dict(self) -> Dict[str, Any]:
        """
        将实例导出为字典

        Returns:
            Dict[str, Any]: 包含所有属性的字典
        """
        return {
            FIELD_ID: self.id,
            FIELD_PROJECT_ID: self.project_id,
            FIELD_NAME: self.name,
            FIELD_FORMAT: self.format,
            FIELD_FILE_TYPE: self.file_type,
            FIELD_SYSTEM_PROMPT: self.system_prompt,
            FIELD_QUESTIONS: [q.to_dict() for q in self.questions],
        }
