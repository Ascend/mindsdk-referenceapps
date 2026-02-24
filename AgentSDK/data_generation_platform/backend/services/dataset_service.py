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
import json
import uuid
from typing import Optional, List, Dict, Any, Tuple, Set, Union

from backend.config.config import Config
from backend.models.dataset import Dataset
from backend.models.question import Question
from backend.models.constants import (
    QUESTION_STATUS_ANSWERED,
    ENCODING_UTF8,
    JSON_INDENT,
    DEFAULT_DATASETS_DIR,
    DEFAULT_DATASET_FORMAT,
    DEFAULT_DATASET_FILE_TYPE,
    DEFAULT_QUESTIONS_DIR,
    SHAREGPT_FIELD_CONVERSATIONS,
    SHAREGPT_FIELD_FROM,
    SHAREGPT_FIELD_VALUE,
    SHAREGPT_ROLE_HUMAN,
    SHAREGPT_ROLE_GPT,
    DATASET_FORMAT_ALPACA,
    DATASET_FORMAT_SHAREGPT,
    DATASET_FORMAT_CUSTOM,
)
from backend.utils.file_utils import read_file, save_file
from backend.utils.logger import init_logger

logger = init_logger(__name__)


class DatasetService:
    """
    数据仓库管理器类，用于管理数据集的生命周期

    Attributes:
        project_dir: 项目根目录路径
        datasets_dir: 数据集存储目录
    """

    def __init__(self, project_dir: str):
        """
        初始化数据仓库管理器

        Args:
            project_dir: 项目根目录路径
        """
        self.project_dir = project_dir
        self.datasets_dir = os.path.join(project_dir, DEFAULT_DATASETS_DIR)
        os.makedirs(self.datasets_dir, exist_ok=True)

    @staticmethod
    def _get_existing_question_ids(dataset: Dataset) -> Set:
        """获取数据集中已存在的问题ID集合"""
        existing_ids = set()
        for q in dataset.questions:
            if hasattr(q, 'id') and q.id is not None:
                existing_ids.add(q.id)
        return existing_ids

    @staticmethod
    def _filter_new_questions(questions: List[Question], existing_ids: Set
    ) -> List[Question]:
        """过滤出新问题"""
        new_questions = []
        for q in questions:
            is_new = not hasattr(q, 'id') or q.id is None or q.id not in existing_ids
            if is_new:
                new_questions.append(q)
        return new_questions


    @staticmethod
    def _write_export_file(output_path: str, data: List[Dict], file_type: str
    ) -> None:
        """写入导出文件"""
        if file_type == "json":
            with open(output_path, 'w', encoding=ENCODING_UTF8) as f:
                json.dump(data, f, ensure_ascii=False, indent=JSON_INDENT)
        elif file_type == "jsonl":
            with open(output_path, 'w', encoding=ENCODING_UTF8) as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        else:
            raise ValueError(f"无效的文件类型: {file_type}")

    @staticmethod
    def _load_dataset_from_file(filepath: str) -> Optional[Dataset]:
        """从文件加载数据集"""
        try:
            dataset_data = read_file(filepath, "json")
            if dataset_data is None:
                logger.warning(f"数据集文件为空: {filepath}")
                return None

            return Dataset.from_dict(dataset_data)  # type: ignore
        except Exception as e:
            logger.error(f"加载数据集失败 {filepath}: {e}")
            return None

    @staticmethod
    def _load_question_by_id(questions_dir: str, question_id: Any
                             ) -> Optional[Question]:
        """按ID加载单个问题"""
        question_path = os.path.join(questions_dir, f"{question_id}.json")

        if not os.path.exists(question_path):
            logger.debug(f"问题文件不存在: {question_id}")
            return None

        try:
            question_data = read_file(question_path, "json")
            if question_data is None:
                logger.warning(f"问题文件为空: {question_path}")
                return None

            return Question.from_dict(question_data)  # type: ignore
        except Exception as e:
            logger.error(f"加载问题失败 {question_path}: {e}")
            return None

    @staticmethod
    def _remove_duplicate_file(filepath: str) -> None:
        """删除重复的数据集文件"""
        try:
            os.remove(filepath)
            logger.info(f"删除重复数据集: {filepath}")
        except Exception as e:
            logger.error(f"删除重复数据集失败 {filepath}: {e}")

    @staticmethod
    def _create_alpaca_item(question: Question, system_prompt: Optional[str]
                            ) -> Dict[str, Any]:
        """创建Alpaca格式的数据项"""
        item = {
            'instruction': getattr(question, 'content', ''),
            'input': '',
            'output': getattr(question, 'answer', ''),
        }

        if hasattr(question, 'chain_of_thought') and question.chain_of_thought:
            item['chain_of_thought'] = question.chain_of_thought

        if system_prompt:
            item['system'] = system_prompt

        return item

    @staticmethod
    def _create_sharegpt_conversation(question: Question, system_prompt: Optional[str]
                                      ) -> List[Dict[str, str]]:
        """创建ShareGPT格式的对话"""
        conversation = []

        if system_prompt:
            conversation.append({SHAREGPT_FIELD_FROM: 'system', SHAREGPT_FIELD_VALUE: system_prompt})

        conversation.append({
            SHAREGPT_FIELD_FROM: SHAREGPT_ROLE_HUMAN,
            SHAREGPT_FIELD_VALUE: getattr(question, 'content', ''),
        })

        answer = getattr(question, 'answer', '')
        if hasattr(question, 'chain_of_thought') and question.chain_of_thought:
            answer = f"{question.chain_of_thought}\n\n{answer}"

        conversation.append({SHAREGPT_FIELD_FROM: SHAREGPT_ROLE_GPT, SHAREGPT_FIELD_VALUE: answer})

        return conversation

    @staticmethod
    def _load_custom_format_config() -> Optional[Any]:
        """加载自定义格式配置"""
        try:
            # 使用相对于项目根目录的路径
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')
            config = Config.load(config_path)

            required_attrs = [
                "custom_system_key",
                "custom_question_key",
                "custom_answer_key",
            ]
            if not all(hasattr(config, attr) for attr in required_attrs):
                logger.warning("自定义格式配置不完整")
                return None

            return config
        except Exception as e:
            logger.error(f"加载自定义格式配置失败: {e}")
            return None

    @staticmethod
    def _create_custom_item(question: Question, config: Any, system_prompt: Optional[str]
                            ) -> Dict[str, Any]:
        """创建自定义格式的数据项"""
        item = {}

        item[config.custom_system_key] = getattr(question, 'system_prompt', system_prompt)
        item[config.custom_question_key] = getattr(question, 'content', '')

        answer = getattr(question, 'answer', '')
        if hasattr(question, 'chain_of_thought') and question.chain_of_thought:
            answer = f"<think>{question.chain_of_thought}</think>\n\n{answer}"

        item[config.custom_answer_key] = answer

        return item

    @staticmethod
    def _should_skip_question(question: Question) -> bool:
        """判断是否应跳过该问题"""
        if hasattr(question, 'status') and question.status < QUESTION_STATUS_ANSWERED:
            return True
        return False

    @staticmethod
    def _generate_unique_id() -> str:
        """生成唯一标识符"""
        return str(uuid.uuid4())

    @staticmethod
    def _safe_remove_file(file_path: str) -> None:
        """安全删除文件"""
        try:
            os.remove(file_path)
            logger.info(f"删除旧数据集文件: {file_path}")
        except Exception as e:
            logger.error(f"删除文件失败 {file_path}: {e}")

    def create_dataset(
        self,
        project_id: Union[int, str],
        name: str,
        format: str = DEFAULT_DATASET_FORMAT,
        file_type: str = DEFAULT_DATASET_FILE_TYPE,
        system_prompt: Optional[str] = None,
    ) -> Dataset:
        """
        创建新仓库

        Args:
            project_id: 项目ID
            name: 数据集名称
            format: 数据格式 (alpaca/sharegpt/custom)
            file_type: 文件类型 (json/jsonl)
            system_prompt: 系统提示词

        Returns:
            Dataset: 创建的数据集对象
        """
        # 构造数据集对象
        dataset = Dataset(
            project_id=project_id,
            name=name,
            format=format,
            file_type=file_type,
            system_prompt=system_prompt,
        )

        # 生成唯一ID并保存数据集元信息
        dataset.id = self._generate_unique_id()
        self._save_dataset(dataset)

        return dataset

    def add_question_to_dataset(
        self, dataset: Dataset, questions: List[Question]
    ) -> Dataset:
        """
        向仓库添加问题

        Args:
            dataset: 目标数据集对象
            questions: 要添加的问题列表

        Returns:
            Dataset: 更新后的数据集对象
        """
        # 获取数据集中已存在的问题ID集合
        existing_ids = self._get_existing_question_ids(dataset)
        new_questions = self._filter_new_questions(questions, existing_ids)

        # 将新问题追加到数据集对象
        dataset.questions.extend(new_questions)

        dataset_path = os.path.join(self.datasets_dir, f"{dataset.id}.json")
        save_file(dataset_path, dataset.to_dict(), base_dir=self.project_dir)

        return dataset


    def get_datasets(self, project_id: Union[int, str]) -> List[Dataset]:
        """
        获取项目仓库

        Args:
            project_id: 项目ID

        Returns:
            List[Dataset]: 项目的数据集列表
        """
        if not os.path.exists(self.datasets_dir):
            return []

        dataset_files = self._scan_dataset_files()
        processed_names: Set[str] = set()
        datasets: List[Dataset] = []

        for _, filepath, _ in dataset_files:
            dataset = self._load_and_process_dataset(
                filepath, project_id, processed_names
            )
            if dataset:
                datasets.append(dataset)

        return datasets

    def export_dataset(
        self, dataset: Dataset, output_path: Optional[str] = None
    ) -> str:
        """
        导出仓库内容

        Args:
            dataset: 要导出的数据集对象
            output_path: 输出文件路径

        Returns:
            str: 导出文件路径
        """
        if output_path is None:
            output_path = os.path.join(
                self.datasets_dir, f"{dataset.name}.{dataset.file_type}"
            )

        # 将数据集格式化为导出所需结构
        data = self._format_dataset(dataset)

        if not data:
            logger.warning("尝试导出空数据集")

        self._remove_old_dataset_files(str(dataset.id) if dataset.id else None, dataset.file_type)
        self._write_export_file(output_path, data, dataset.file_type)

        return output_path

    def get_dataset_by_name(
        self, project_id: Union[int, str], name: str
    ) -> Optional[Dataset]:
        """
        按名称获取数据集

        Args:
            project_id: 项目ID
            name: 数据集名称

        Returns:
            Optional[Dataset]: 找到的数据集对象或None
        """
        project_datasets = self.get_datasets(project_id)

        for dataset in project_datasets:
            if dataset.name == name:
                return dataset

        return None

    def _save_dataset(self, dataset: Dataset) -> None:
        """
        保存数据集到磁盘

        Args:
            dataset: 要保存的数据集对象
        """
        dataset_path = os.path.join(self.datasets_dir, f"{dataset.id}.json")
        with open(dataset_path, 'w', encoding=ENCODING_UTF8) as f:
            json.dump(dataset.to_dict(), f, ensure_ascii=False, indent=JSON_INDENT)

    def _format_dataset(self, dataset: Dataset) -> List[Dict[str, Any]]:
        """根据格式转换数据集"""
        format_handlers = {
            DATASET_FORMAT_ALPACA: self._format_as_alpaca,
            DATASET_FORMAT_SHAREGPT: self._format_as_sharegpt,
            DATASET_FORMAT_CUSTOM: self._format_as_custom,
        }

        handler = format_handlers.get(dataset.format)
        if handler is None:
            raise ValueError(f"无效的数据集格式: {dataset.format}")

        return handler(dataset)

    def _scan_dataset_files(self) -> List[Tuple[str, str, float]]:
        """扫描数据集目录中的所有JSON文件"""
        dataset_files = []

        for filename in os.listdir(self.datasets_dir):
            if not filename.endswith('.json'):
                continue

            filepath = os.path.join(self.datasets_dir, filename)
            mtime = os.path.getmtime(filepath)
            dataset_files.append((filename, filepath, mtime))

        dataset_files.sort(key=lambda x: x[2], reverse=True)
        return dataset_files

    def _load_and_process_dataset(
        self,
        filepath: str,
        project_id: Union[int, str],
        processed_names: Set[str],
    ) -> Optional[Dataset]:
        """加载并处理单个数据集文件"""
        dataset = self._load_dataset_from_file(filepath)
        if dataset is None:
            return None

        if dataset.project_id != project_id:
            return None

        if dataset.name is None:
            return None

        if dataset.name in processed_names:
            self._safe_remove_file(filepath)
            return None

        dataset.questions = self._load_full_questions(dataset)
        processed_names.add(dataset.name)

        return dataset

    def _load_full_questions(self, dataset: Dataset) -> List[Question]:
        """加载数据集的完整问题列表"""
        full_questions = []
        questions_dir = os.path.join(self.project_dir, DEFAULT_QUESTIONS_DIR)

        for question in dataset.questions:
            loaded_question = self._load_question_by_id(questions_dir, question.id)
            if loaded_question:
                full_questions.append(loaded_question)

        return full_questions

    def _format_as_alpaca(self, dataset: Dataset) -> List[Dict[str, Any]]:
        """转换为Alpaca风格"""
        data = []

        for question in dataset.questions:
            if self._should_skip_question(question):
                continue

            item = self._create_alpaca_item(question, dataset.system_prompt)
            data.append(item)

        return data

    def _format_as_sharegpt(self, dataset: Dataset) -> List[Dict[str, Any]]:
        """转换为ShareGPT风格"""
        data = []

        for question in dataset.questions:
            if self._should_skip_question(question):
                continue

            conversation = self._create_sharegpt_conversation(
                question, dataset.system_prompt
            )
            data.append({SHAREGPT_FIELD_CONVERSATIONS: conversation})

        return data

    def _format_as_custom(self, dataset: Dataset) -> List[Dict[str, Any]]:
        """转换为自定义风格"""
        config = self._load_custom_format_config()
        if config is None:
            return []

        data = []
        for question in dataset.questions:
            if self._should_skip_question(question):
                continue

            item = self._create_custom_item(question, config, dataset.system_prompt)
            data.append(item)

        return data

    def _remove_old_dataset_files(self, dataset_id: Union[int, str, None], file_type: str) -> None:
        """删除过时的数据集文件"""
        if not os.path.exists(self.datasets_dir):
            return

        if dataset_id is None:
            return

        dataset_id_str = str(dataset_id)
        for filename in os.listdir(self.datasets_dir):
            if filename.startswith(f"{dataset_id_str}.") and filename.endswith(f".{file_type}"):
                self._safe_remove_file(os.path.join(self.datasets_dir, filename))
