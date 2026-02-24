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
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING

from backend.models.constants import (
    FIELD_ID,
    FIELD_NAME,
    FIELD_DESCRIPTION,
    FIELD_DOCUMENTS,
    FIELD_DATASETS,
)

if TYPE_CHECKING:
    from backend.models.document import Document
    from backend.models.dataset import Dataset


def _extract_object_id(obj: Any) -> Union[int, str, Any]:
    """
    提取对象的ID

    Args:
        obj: 可能是Document/Dataset对象或ID

    Returns:
        Union[int, str, Any]: 如果对象有id属性则返回id，否则返回对象本身
    """
    if hasattr(obj, FIELD_ID) and getattr(obj, FIELD_ID) is not None:
        return getattr(obj, FIELD_ID)
    return obj


class Project:
    """
    项目类，用于管理项目配置和关联资源

    Attributes:
        id: 项目唯一标识符
        name: 项目名称
        description: 项目描述
        llm_provider: 大语言模型提供商
        api_key: API密钥
        model_name: 使用的模型名称
        documents: 关联文档列表
        datasets: 关联数据集列表
    """
    def __init__(
        self,
        id: Optional[Union[int, str]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        初始化项目实例

        Args:
            id: 项目唯一标识符
            name: 项目名称
            description: 项目描述
            llm_provider: 大语言模型提供商
            api_key: API密钥
            model_name: 使用的模型名称
        """
        # 备注：核心属性初始化
        self.id = id
        self.name = name
        self.description = description
        self.llm_provider = llm_provider
        self.api_key = api_key
        self.model_name = model_name
        # 关联的文档和数据集列表（保持引用，方便增量更新）
        self.documents: List[Any] = []
        self.datasets: List[Any] = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        从配置字典创建Project实例

        Args:
            data: 包含项目配置的字典

        Returns:
            Project: 创建的项目实例
        """
        # 从配置字典创建Project实例
        instance = cls(
            id=data.get(FIELD_ID),
            name=data.get(FIELD_NAME),
            description=data.get(FIELD_DESCRIPTION),
            llm_provider=data.get('llm_provider'),
            api_key=data.get('api_key'),
            model_name=data.get('model_name'),
        )

        instance.documents = data.get(FIELD_DOCUMENTS, [])
        instance.datasets = data.get(FIELD_DATASETS, [])

        return instance

    def to_dict(self) -> Dict[str, Any]:
        """
        将实例导出为配置字典

        Returns:
            Dict[str, Any]: 包含所有属性的配置字典
        """
        # 将实例导出为配置字典（包含核心属性和关联对象引用）
        return {
            FIELD_ID: self.id,
            FIELD_NAME: self.name,
            FIELD_DESCRIPTION: self.description,
            'llm_provider': self.llm_provider,
            'api_key': self.api_key,
            'model_name': self.model_name,
            FIELD_DOCUMENTS: [_extract_object_id(doc) for doc in self.documents],
            FIELD_DATASETS: [_extract_object_id(dataset) for dataset in self.datasets],
        }
