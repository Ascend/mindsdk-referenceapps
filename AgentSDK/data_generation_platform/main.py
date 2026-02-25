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

import argparse
import getpass
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from typing import Optional, Tuple

from backend.config.config import Config
from backend.utils.file_validator import FileValidator
from backend.services.project_service import ProjectService
from backend.services.llm_service import LLMService
from backend.services.document_service import DocumentService
from backend.services.question_service import QuestionService
from backend.services.dataset_service import DatasetService
from backend.models.param_config import DatasetCreateConfig
from backend.models.constants import (
    DOCUMENT_STATUS_QUESTIONS_GENERATED,
    QUESTION_STATUS_UNANSWERED,
    QUESTION_STATUS_ANSWERED,
    QUESTION_STATUS_REVIEWED,
    API_KEY_MIN_LENGTH,
    API_KEY_MAX_LENGTH,
    OPENAI_KEY_PREFIX,
    OPENAI_KEY_PATTERN,
    API_KEY_SUSPICIOUS_PATTERNS,
    DEFAULT_LLM_PROVIDER,
    ARG_CONFIG,
    ARG_PROJECT,
    ARG_DOCUMENT,
    ARG_GENERATE_QUESTIONS,
    ARG_GENERATE_ANSWERS,
    ARG_GENERATE_ANSWERS_NO_CHAIN,
    ARG_CREATE_DATASET,
    ARG_EXPORT_DATASET,
    ARG_IMPORT_QUESTIONS,
    ARG_CONFIG_DEFAULT,
    ARG_STORE_DEFAULT,
    HELP_CONFIG,
    HELP_PROJECT,
    HELP_DOCUMENT,
    HELP_GENERATE_QUESTIONS,
    HELP_GENERATE_ANSWERS,
    HELP_GENERATE_ANSWERS_NO_CHAIN,
    HELP_CREATE_DATASET,
    HELP_EXPORT_DATASET,
    HELP_IMPORT_QUESTIONS,
    MSG_API_KEY_EMPTY,
    MSG_API_KEY_TOO_SHORT,
    MSG_API_KEY_TOO_LONG,
    MSG_API_KEY_PREFIX,
    MSG_DOCUMENT_NOT_FOUND,
    MSG_XLSX_NOT_FOUND,
    MSG_NO_DOCUMENTS,
    MSG_DATASET_NOT_FOUND,
    MSG_CONFIG_NOT_FOUND,
)
from backend.utils.logger import init_logger

logger = init_logger(__name__)


class ConfigurationError(Exception):
    """配置错误异常类"""
    pass


# ==================== 配置加载相关函数 ====================

def _read_stdin_config() -> dict:
    """从标准输入读取配置（JSON格式）"""
    # 检查是否为交互式终端，非交互式则尝试读取stdin
    if sys.stdin.isatty():
        return {}

    def read_and_parse():
        data = sys.stdin.read().rstrip("\n")
        if data:
            return json.loads(data)
        return None

    try:
        # 使用线程池执行，设置5秒超时
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(read_and_parse)
            result = future.result(timeout=5.0)  # 5秒超时
            return result if result is not None else {}
    except TimeoutError:
        # 超时时直接返回空字典
        return {}
    except Exception:
        # 其他异常也返回空字典
        return {}


def _is_real_terminal() -> bool:
    """检测是否为真实终端（用于判断是否可以使用getpass隐藏输入）"""
    if not sys.stdin.isatty():
        return False
    try:
        return os.isatty(sys.stdin.fileno())
    except Exception:
        return False


# ==================== API密钥处理函数 ====================

def _prompt_api_key(provider: str) -> str:
    """提示用户输入API密钥"""
    if _is_real_terminal():
        return getpass.getpass(f"\n需要 LLM API KEY (provider: {provider})\n请输入 API KEY: ")
    else:
        logger.warning(f"\n警告: 使用IDE终端执行不支持密码隐藏，输入将明文显示")
        logger.info(f"需要 LLM API KEY (provider: {provider})")
        return input("请输入 API KEY: ").strip()


def _validate_api_key(api_key: str, provider: str) -> Tuple[bool, str]:
    """验证API KEY的格式和基本要求"""
    if not api_key or not isinstance(api_key, str):
        return False, MSG_API_KEY_EMPTY

    api_key = api_key.strip()

    if len(api_key) < API_KEY_MIN_LENGTH:
        return False, MSG_API_KEY_TOO_SHORT.format(API_KEY_MIN_LENGTH)

    if len(api_key) > API_KEY_MAX_LENGTH:
        return False, MSG_API_KEY_TOO_LONG.format(API_KEY_MAX_LENGTH)

    if provider.lower() == DEFAULT_LLM_PROVIDER:
        if not api_key.startswith(OPENAI_KEY_PREFIX):
            return False, MSG_API_KEY_PREFIX.format(OPENAI_KEY_PREFIX)
        if not OPENAI_KEY_PATTERN.match(api_key):
            return False, "OpenAI API KEY格式不正确"

    for pattern in API_KEY_SUSPICIOUS_PATTERNS:
        if re.search(pattern, api_key.lower()):
            return False, f"API KEY包含可疑内容: {pattern}"

    return True, ""


# ==================== 命令行参数解析函数 ====================

def _parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="问答数据集生成工具")
    parser.add_argument(ARG_CONFIG, type=str, default=ARG_CONFIG_DEFAULT, help=HELP_CONFIG)
    parser.add_argument(ARG_PROJECT, type=str, nargs='+', help=HELP_PROJECT)
    parser.add_argument(ARG_DOCUMENT, type=str, help=HELP_DOCUMENT)
    parser.add_argument(ARG_GENERATE_QUESTIONS, action=ARG_STORE_DEFAULT, help=HELP_GENERATE_QUESTIONS)
    parser.add_argument(ARG_GENERATE_ANSWERS, action=ARG_STORE_DEFAULT, help=HELP_GENERATE_ANSWERS)
    parser.add_argument(ARG_GENERATE_ANSWERS_NO_CHAIN, action=ARG_STORE_DEFAULT, help=HELP_GENERATE_ANSWERS_NO_CHAIN)
    parser.add_argument(ARG_CREATE_DATASET, type=str, help=HELP_CREATE_DATASET)
    parser.add_argument(ARG_EXPORT_DATASET, type=str, help=HELP_EXPORT_DATASET)
    parser.add_argument(ARG_IMPORT_QUESTIONS, type=str, help=HELP_IMPORT_QUESTIONS)
    return parser.parse_args()


# ==================== 服务初始化函数 ====================

@dataclass
class DatasetCreationContext:
    """
    数据集创建上下文

    用于封装数据集创建过程中需要的服务和配置参数。
    """
    args: argparse.Namespace
    config: Config
    document_service: DocumentService
    question_service: QuestionService
    dataset_service: DatasetService
    project: any

def _needs_api_key(args: argparse.Namespace) -> bool:
    """判断当前命令是否需要LLM API KEY"""
    return args.generate_questions or args.generate_answers or args.generate_answers_no_chain


def _resolve_api_key(config: Config) -> Optional[str]:
    """获取并验证LLM API KEY"""
    llm_api_key = None

    # 先尝试从stdin读取
    stdin_config = _read_stdin_config()
    if stdin_config:
        llm_api_key = stdin_config.get('llm_api_key')

    # 如果没有从stdin获取到，尝试交互式输入
    if not llm_api_key:
        try:
            llm_api_key = _prompt_api_key(config.llm_provider)
        except (EOFError, IOError):
            # IDE环境可能不支持交互式输入
            pass

    # 如果仍然没有获取到API密钥，记录错误并抛出异常
    if not llm_api_key:
        error_detail = (
            f"无法获取LLM API KEY\n"
            f"请通过以下方式之一提供正确的API KEY:\n"
            f"  1. 在前端页面<配置管理>中配置 <API 密钥>\n"
            f"  2. 使用CLI而非IDE运行main.py"
        )
        raise ConfigurationError(error_detail)

    is_valid, error_msg = _validate_api_key(llm_api_key, config.llm_provider)
    if not is_valid:
        error_detail = (
            f"API KEY验证失败: {error_msg}\n"
            f"请通过以下方式之一提供正确的API KEY:\n"
            f"  1. 在前端页面<配置管理>中配置 <API 密钥>\n"
            f"  2. 使用CLI而非IDE运行main.py"
        )
        raise ConfigurationError(error_detail)

    return llm_api_key


def _create_llm_service(config: Config, api_key: Optional[str]) -> LLMService:
    """创建LLMService实例"""
    from backend.models.param_config import (
        LLMProviderConfig,
        LLMGenerationConfig,
        LLMPromptConfig,
    )

    provider_config = LLMProviderConfig(
        provider=config.llm_provider,
        api_key=api_key,
        model_name=config.llm_model,
        llm_api=config.llm_api,
    )

    generation_config = LLMGenerationConfig(
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )

    prompt_config = LLMPromptConfig(
        system_prompt=config.system_prompt,
        answer_prompt=config.answer_prompt,
        chain_of_thought_prompt=config.chain_of_thought_prompt,
    )

    return LLMService(
        provider_config=provider_config,
        generation_config=generation_config,
        prompt_config=prompt_config,
    )


def _get_project_dir(config: Config, project) -> str:
    """获取项目数据目录"""
    return os.path.join(config.data_dir, str(project.id))


# ==================== 业务处理函数 ====================

def _handle_document(args, document_service, project) -> None:
    """处理文档导入"""
    if not (args.document and project):
        return

    if not os.path.exists(args.document):
        raise ConfigurationError(MSG_DOCUMENT_NOT_FOUND.format(args.document))

    absolute_document_path = os.path.abspath(args.document)
    document_validation = FileValidator().validate_file(
        os.path.basename(absolute_document_path),
        absolute_document_path,
        os.path.dirname(absolute_document_path)
    )
    if not document_validation.get('valid', False):
        errors = document_validation.get('errors', [])
        raise ConfigurationError(f"文档文件校验失败: {'; '.join(errors)}")

    logger.info(f"正在处理文档: {args.document}")
    document = document_service.create_document(project.id, args.document)
    chunks = document_service.split_document(document)
    logger.info(f"文档已分割为 {len(chunks)} 个文本块")


def _collect_unanswered_questions(document_service, question_service, project) -> list:
    """收集项目中所有未回答的问题"""
    all_questions = []
    documents = document_service.get_documents(project.id)

    for document in documents:
        questions = question_service.get_questions_by_document_id(document.id)
        all_questions.extend(questions)

    return [q for q in all_questions if q.status == QUESTION_STATUS_UNANSWERED]


def _handle_generate_questions(args, document_service, question_service, project) -> None:
    """处理问题生成"""
    if not (args.generate_questions and project):
        return

    logger.info("正在生成问题...")
    documents = document_service.get_documents(project.id)
    document = documents[-1]  # 取最后一篇文档 当前数据生成流程仅与最新文档绑定
    if document.status < DOCUMENT_STATUS_QUESTIONS_GENERATED:
        questions = question_service.generate_questions_for_document(document)
        logger.info(f"已为文档 {document.file_name} 生成 {len(questions)} 个问题")
    else:
        logger.info(f"文档 {document.file_name} 的问题已生成")


# ==================== 答案生成处理函数 ====================

def _handle_generate_answers(args, document_service, question_service, project) -> None:
    """处理答案生成（含/不含思维链）"""
    if not (args.generate_answers or args.generate_answers_no_chain) or not project:
        return
    with_no_chain = args.generate_answers_no_chain
    log_message = "正在生成答案（不含思维链）..." if with_no_chain else "正在生成答案和思维链..."
    success_message = "已为 {0} 个问题生成答案(不含思维链)" if with_no_chain else "已为 {0} 个问题生成答案和思维链"

    logger.info(log_message)
    unanswered = _collect_unanswered_questions(document_service, question_service, project)

    if unanswered:
        updated = question_service.generate_answers(unanswered, with_chain_of_thought=False) \
            if with_no_chain else question_service.generate_answers(unanswered, with_chain_of_thought=True)
        logger.info(success_message.format(len(updated)))
    else:
        logger.info("所有问题都已回答")


# ==================== 问题导入处理函数 ====================

def _handle_import_questions(args, document_service, question_service, project) -> None:
    """处理问题导入"""
    if not (args.import_questions and project):
        return

    if not os.path.exists(args.import_questions):
        raise ConfigurationError(MSG_XLSX_NOT_FOUND.format(args.import_questions))

    logger.info(f"正在从 {args.import_questions} 导入问题...")

    documents = document_service.get_documents(project.id)
    if not documents:
        raise ConfigurationError(MSG_NO_DOCUMENTS)

    document = documents[0]
    chunk_id = document.chunks[0] if document.chunks else 0

    imported = question_service.import_questions_from_xlsx(
        args.import_questions, document.id, chunk_id
    )
    logger.info(f"已从XLSX文件中导入 {len(imported)} 个问题")

    # 删除XLSX文件前的校验
    xlsx_path = args.import_questions
    if imported:
        # 校验1: 确认文件存在
        if not os.path.exists(xlsx_path):
            logger.warning(f"XLSX文件不存在，跳过删除: {xlsx_path}")
        # 校验2: 确认是XLSX文件
        elif not xlsx_path.lower().endswith('.xlsx'):
            logger.warning(f"文件不是XLSX格式，跳过删除: {xlsx_path}")
        else:
            try:
                os.remove(xlsx_path)
                logger.info(f"已删除XLSX文件: {xlsx_path}")
            except OSError as e:
                logger.error(f"删除XLSX文件失败: {e}")


# ==================== 数据集处理函数 ====================

def _collect_answered_questions(document_service, question_service, project) -> list:
    """收集项目中所有已回答和已审核的问题"""
    all_questions = []
    documents = document_service.get_documents(project.id)
    for document in documents:
        questions = question_service.get_questions_by_document_id(document.id)
        all_questions.extend(questions)

    return [
        q for q in all_questions
        if q.status in (QUESTION_STATUS_ANSWERED, QUESTION_STATUS_REVIEWED)
    ]


def _handle_create_dataset(ctx: DatasetCreationContext) -> None:
    """处理数据集创建"""
    if not (ctx.args.create_dataset and ctx.project):
        return

    logger.info(f"正在创建数据集 '{ctx.args.create_dataset}'...")

    dataset = ctx.dataset_service.create_dataset(
        project_id=ctx.project.id,
        name=ctx.args.create_dataset,
        format=ctx.config.default_dataset_format,
        file_type=ctx.config.default_dataset_file_type,
        system_prompt=ctx.config.system_prompt,
    )

    answered = _collect_answered_questions(ctx.document_service, ctx.question_service, ctx.project)

    if answered:
        dataset = ctx.dataset_service.add_question_to_dataset(dataset, answered)
        logger.info(f"已将 {len(answered)} 个已回答的问题添加到数据集 '{dataset.name}'")
    else:
        logger.info("没有找到已回答的问题，无法创建数据集")


def _handle_export_dataset(args, dataset_service, project) -> None:
    """处理数据集导出"""
    if not (args.export_dataset and project):
        return

    logger.info(f"正在导出数据集 '{args.export_dataset}'...")

    dataset = dataset_service.get_dataset_by_name(project.id, args.export_dataset)
    logger.info(f"已找到数据集 '{dataset}'")

    if dataset:
        export_path = dataset_service.export_dataset(dataset)
        logger.info(f"数据集已导出到: {export_path}")
    else:
        logger.error(MSG_DATASET_NOT_FOUND.format(args.export_dataset))


def execute_application():
    """主函数，实现命令行问答数据集生成工具"""
    args = _parse_arguments()

    try:
        config = Config.load(args.config)
    except FileNotFoundError as e:
        logger.error(MSG_CONFIG_NOT_FOUND.format(e))
        sys.exit(1)

    project_service = ProjectService(config.data_dir, config.__dict__)

    # 处理 project 参数（nargs='+' 返回列表，需要合并）
    project_name = ' '.join(args.project) if isinstance(args.project, list) else args.project

    if not project_name:
        return

    project = project_service.get_or_create_project(project_name)

    try:
        llm_api_key = _resolve_api_key(config) if _needs_api_key(args) else None

        llm_service = _create_llm_service(config, llm_api_key)
        project_dir = _get_project_dir(config, project)

        document_service = DocumentService(project_dir, config.__dict__)
        question_service = QuestionService(project_dir, llm_service, system_prompt=config.system_prompt)
        dataset_service = DatasetService(project_dir)

        _handle_document(args, document_service, project)
        _handle_generate_questions(args, document_service, question_service, project)
        _handle_generate_answers(args, document_service, question_service, project)
        _handle_import_questions(args, document_service, question_service, project)

        dataset_ctx = DatasetCreationContext(
            args=args,
            config=config,
            document_service=document_service,
            question_service=question_service,
            dataset_service=dataset_service,
            project=project
        )
        _handle_create_dataset(dataset_ctx)
        _handle_export_dataset(args, dataset_service, project)
    except ConfigurationError as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    execute_application()
