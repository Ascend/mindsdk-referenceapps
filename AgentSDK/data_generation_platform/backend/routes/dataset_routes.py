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
import subprocess
from typing import List, Optional, Tuple

import json
import uuid
from flask import Blueprint, request, jsonify, send_file, Response

from backend.config.config import Config
from backend.services.project_service import ProjectService
from backend.services.dataset_service import DatasetService
from backend.services.document_service import DocumentService
from backend.services.question_service import QuestionService
from backend.utils.logger import init_logger
from backend.utils.response_utils import (
    error_response,
    server_error_response,
    not_found_response,
    access_denied_response,
    unsupported_media_type_response,
    gateway_timeout_response,
)
from backend.utils.validation_utils import (
    validate_id_format,
    validate_json_body,
    validate_string_length,
)
from backend.utils.file_utils import secure_filename
from backend.models.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_UPLOAD_DIR,
    DEFAULT_DOCUMENTS_DIR,
    DEFAULT_DATASETS_DIR,
    ENCODING_UTF8,
    HTTP_OK,
    SUBPROCESS_TIMEOUT_SECONDS,
    MAX_STRING_FIELD_LENGTH,
    QUESTION_STATUS_ANSWERED,
    QUESTION_STATUS_REVIEWED,
    IMPORT_RESULT_KEYWORD,
    IMPORT_COUNT_KEYWORD,
    DEFAULT_UPLOADED_FILENAME,
)

from backend.utils.file_validator import validate_file_type, validate_file_upload, validate_path_security, FileValidator

dataset_bp = Blueprint('dataset', __name__)

logger = init_logger(__name__)


def _classify_validation_error(errors: List[str]) -> Tuple[str, int]:
    """
    根据校验错误类型确定HTTP状态码

    Args:
        errors: 错误消息列表

    Returns:
        Tuple[str, int]: (合并的错误消息, HTTP状态码)
    """
    # 根据错误类型确定返回的错误消息和状态码
    error_msg = "文件校验失败: " + '; '.join(errors)

    for err in errors:
        if '不支持的文件类型' in err or '不允许的可执行文件类型' in err:
            return error_msg, 415

    for err in errors:
        if '文件过大' in err:
            return error_msg, 413

    return error_msg, 400


@dataset_bp.route('/upload_document', methods=['POST'])
def upload_document():
    """文件上传路由"""
    # 上传文档入口：校验、保存并返回结果
    if 'file' not in request.files:
        logger.warning("No file provided in upload_document request")
        return error_response('没有文件被上传')

    file = request.files['file']

    config = Config.load(DEFAULT_CONFIG_PATH)
    upload_dir = os.path.join(config.data_dir, DEFAULT_UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)

    try:
        # 完成文件上传的完整步骤
        validation_result = FileValidator.validate_file_upload(file, upload_dir)

        if not validation_result.get('valid', False):
            errors = validation_result.get('errors', [])
            logger.warning(f"File validation failed: {'; '.join(errors)}")
            msg, status_code = _classify_validation_error(errors)
            if status_code == 415:
                return unsupported_media_type_response(msg)
            return error_response(msg, status_code)

        return _save_and_respond_upload(file, upload_dir, config)
    except (OSError, IOError) as e:
        # 捕获文件操作相关的具体异常（如权限问题、磁盘空间不足等）
        logger.error(f"文件操作失败: {file.filename}, 错误: {str(e)}", exc_info=True)
        return server_error_response("文件保存过程中发生错误")
    except Exception as e:
        # 捕获其他未预见的异常，避免过于宽泛的异常处理
        logger.error(f"上传文档时发生意外错误: {file.filename}", exc_info=True)
        return server_error_response("文件上传失败")


def _save_and_respond_upload(file, upload_dir: str, config: Config):
    """保存上传文件并返回成功响应"""
    # 核心逻辑：将上传的文件保存到目标目录并返回相对路径
    safe_filename = secure_filename(file.filename or "")
    final_filename = f"{str(uuid.uuid4())}_{safe_filename}"
    final_path = os.path.join(upload_dir, final_filename)
    file.save(final_path)

    # 文件落盘后做一次完整校验，避免后续流程处理异常文件
    validation_result = FileValidator().validate_file(final_filename, final_path, upload_dir)
    if not validation_result.get('valid', False):
        errors = validation_result.get('errors', [])
        logger.warning(f"Post-save file validation failed: {'; '.join(errors)}")
        try:
            os.remove(final_path)
        except OSError:
            logger.warning(f"Failed to cleanup invalid uploaded file: {final_path}")
        msg, status_code = _classify_validation_error(errors)
        if status_code == 415:
            return unsupported_media_type_response(msg)
        return error_response(msg, status_code)

    file_size = os.path.getsize(final_path)
    logger.info(f"File uploaded successfully: {final_filename} ({file_size} bytes)")

    # 构建相对于 data_dir 的路径
    rel_path = os.path.relpath(final_path, config.data_dir)
    # 统一使用正斜杠
    rel_path = rel_path.replace("\\", '/')

    return jsonify({
        'status': 'success',
        'file_path': rel_path,
        'message': '文件上传成功'
    }), HTTP_OK


@dataset_bp.route('/delete_upload_file', methods=['POST'])
def delete_upload_file():
    """删除上传文件路由"""
    data, json_err = validate_json_body(request)
    if json_err:
        return error_response(json_err)

    file_path = data.get('file_path')
    if not file_path:
        logger.warning("No file_path provided in delete_upload_file request")
        return error_response('文件路径不能为空')

    err = validate_string_length(file_path, MAX_STRING_FIELD_LENGTH, 'file_path')
    if err:
        return error_response(err)

    config = Config.load(DEFAULT_CONFIG_PATH)
    upload_dir = os.path.join(config.data_dir, DEFAULT_UPLOAD_DIR)
    if not file_path.startswith(config.data_dir):
        file_path = os.path.join(config.data_dir, file_path)
    is_safe, error_msg = validate_path_security(file_path, upload_dir)
    if not is_safe:
        logger.warning(f"Access denied for file deletion outside upload directory: {file_path}")
        return access_denied_response('不允许删除此文件: ' + error_msg)

    try:
        if not os.path.exists(file_path):
            return error_response('文件不存在', 500)
            
        file_size = os.path.getsize(file_path)
        os.remove(file_path)
        
        logger.info(f"File deleted successfully: {file_path} ({file_size} bytes)")
        
        return jsonify({
            'status': 'success',
            'message': '文件删除成功'
        }), HTTP_OK
    except Exception as e:
        logger.error(f"Failed to delete upload file {file_path}", exc_info=True)
        return error_response('删除文件失败: ' + str(e))


@dataset_bp.route('/download_dataset')
def download_dataset():
    """数据集下载路由"""
    file_path = request.args.get('file_path')
    if not file_path:
        logger.warning("Download dataset request without file_path")
        return Response("文件路径不能为空", status=400)

    err = validate_string_length(file_path, MAX_STRING_FIELD_LENGTH, 'file_path')
    if err:
        return Response(err, status=400)

    # 路径安全验证 - 防止任意文件下载
    config = Config.load(DEFAULT_CONFIG_PATH)
    allowed_dirs = [
        config.data_dir,
        os.path.join(config.data_dir, DEFAULT_DATASETS_DIR)
    ]

    is_safe = False
    for allowed_dir in allowed_dirs:
        safe, _ = validate_path_security(file_path, allowed_dir)
        if safe:
            is_safe = True
            break

    if not is_safe:
        logger.warning(f"Download attempt blocked for unauthorized path: {file_path}")
        return Response("拒绝访问：文件不在允许的目录内", status=403)

    if not os.path.exists(file_path):
        logger.warning(f"Download dataset request for non-existent file: {file_path}")
        return Response("文件不存在", status=404)

    try:
        logger.info(f"File download started: {file_path} from {request.remote_addr}")

        filename = os.path.basename(file_path)
        response = send_file(file_path, as_attachment=True, download_name=filename)

        logger.info(f"File download completed: {file_path} ({filename})")
        return response
    except Exception:
        logger.error(f"Download dataset failed for file {file_path}", exc_info=True)
        return Response("下载文件时发生错误", status=500)


@dataset_bp.route('/export_dataset', methods=['POST'])
def export_dataset() -> Tuple[Response, int]:
    """数据集导出路由"""
    data, json_err = validate_json_body(request)
    if json_err:
        return error_response(json_err)

    project_id = data.get('project_id')

    if not project_id:
        return error_response('项目ID不能为空')

    id_err = validate_id_format(project_id, 'project_id')
    if id_err:
        return error_response(id_err)

    config = Config.load(DEFAULT_CONFIG_PATH)
    project_service = ProjectService(config.data_dir)
    project = project_service.get_project(project_id)

    if not project:
        return not_found_response('项目未找到')

    dataset_name = f"{project.name}_dataset"

    try:
        project_dir = os.path.join(config.data_dir, str(project.id))
        export_path = _execute_dataset_export(project_dir, config, project.id, dataset_name)

        return jsonify({
            'status': 'success',
            'message': '数据集导出成功',
            'paths': [export_path]
        }), HTTP_OK
    except Exception as e:
        return server_error_response(f"导出数据集时发生错误: {str(e)}")


def _execute_dataset_export(project_dir: str, config, project_id, dataset_name: str) -> str:
    """
    执行数据集创建、填充与导出

    Returns:
        str: 导出文件路径
    """
    dataset_service = DatasetService(project_dir)
    document_service = DocumentService(project_dir, config.__dict__)
    question_service = QuestionService(
        project_dir, llm_service=None,
        system_prompt=config.system_prompt
    )

    dataset = dataset_service.create_dataset(
        project_id=project_id,
        name=dataset_name,
        format=config.default_dataset_format,
        file_type=config.default_dataset_file_type,
        system_prompt=config.system_prompt,
    )

    answered = _collect_answered_questions(document_service, question_service, project_id)
    if answered:
        dataset = dataset_service.add_question_to_dataset(dataset, answered)

    return dataset_service.export_dataset(dataset)


def _collect_answered_questions(document_service, question_service, project_id) -> list:
    """收集项目中所有已回答和已审核的问题"""
    all_questions = []
    documents = document_service.get_documents(project_id)
    if documents:
        for document in documents:
            questions = question_service.get_questions_by_document_id(document.id)
            all_questions.extend(questions)

    return [
        q for q in all_questions
        if q.status in (QUESTION_STATUS_ANSWERED, QUESTION_STATUS_REVIEWED)
    ]


@dataset_bp.route('/import_questions', methods=['POST'])
def import_questions() -> Tuple[Response, int]:
    """问题导入路由"""
    try:
        validation_error = _validate_import_request()
        if validation_error:
            return validation_error

        file = request.files['file']
        project_id = request.form.get('project_id')
        project_name = request.form.get('project_name')

        config = Config.load(DEFAULT_CONFIG_PATH)
        uploaded_file_path = _save_uploaded_file(file, config.data_dir, project_id or "")

        if not os.path.exists(uploaded_file_path):
            return server_error_response('文件保存失败')

        upload_validation = FileValidator().validate_file(
            os.path.basename(uploaded_file_path),
            uploaded_file_path,
            os.path.dirname(uploaded_file_path)
        )
        if not upload_validation.get('valid', False):
            errors = upload_validation.get('errors', [])
            logger.warning(f"Import upload validation failed: {'; '.join(errors)}")
            msg, status_code = _classify_validation_error(errors)
            if status_code == 415:
                return unsupported_media_type_response(msg)
            return error_response(msg, status_code)

        document_path = _find_document_path(config.data_dir, project_id or "")
        cmd_parts = _build_import_command(project_name or "", uploaded_file_path, document_path)

        # 使用列表参数（不使用 shell=True）并添加超时
        result = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding=ENCODING_UTF8
        )
        try:
            output, _ = result.communicate(timeout=SUBPROCESS_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            result.kill()
            result.wait()
            logger.error(f"Import subprocess timeout after {SUBPROCESS_TIMEOUT_SECONDS}s")
            return gateway_timeout_response(f"导入超时（{SUBPROCESS_TIMEOUT_SECONDS}秒）")

        imported_count = _parse_import_result(output)

        if result.returncode != 0:
            return server_error_response("导入过程中发生错误")

        return jsonify({
            'status': 'success',
            'imported_count': imported_count,
            'message': '问题导入完成',
            'output': output
        }), HTTP_OK
    except Exception as e:
        return server_error_response(f"处理导入请求时发生错误: {str(e)}")


def _validate_import_request() -> Optional[Tuple[Response, int]]:
    """
    验证导入请求

    Returns:
        Optional[Tuple[Response, int]]: 如果验证失败返回错误响应，否则返回None
    """
    if 'file' not in request.files:
        return error_response('没有上传文件')

    file = request.files['file']
    if file.filename == '':
        return error_response('未选择文件')

    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        return unsupported_media_type_response('只支持XLSX文件格式')

    project_id = request.form.get('project_id')
    if not project_id:
        return error_response('缺少项目ID')

    id_err = validate_id_format(project_id, 'project_id')
    if id_err:
        return error_response(id_err)

    # 校验 project_name 长度
    project_name = request.form.get('project_name')
    if project_name:
        err = validate_string_length(project_name, MAX_STRING_FIELD_LENGTH, 'project_name')
        if err:
            return error_response(err)

    return None


def _save_uploaded_file(
    file,
    data_dir: str,
    project_id: str
) -> str:
    """
    保存上传文件

    Args:
        file: 上传的文件对象
        data_dir: 数据目录
        project_id: 项目ID

    Returns:
        str: 保存的文件路径
    """
    project_data_dir = os.path.join(data_dir, project_id)
    uploads_dir = os.path.join(project_data_dir, DEFAULT_UPLOAD_DIR)
    os.makedirs(uploads_dir, exist_ok=True)

    safe_name = secure_filename(file.filename or "")
    if not safe_name:
        safe_name = DEFAULT_UPLOADED_FILENAME
    uploaded_file_path = os.path.join(uploads_dir, safe_name)
    file.save(uploaded_file_path)
    return uploaded_file_path


def _find_document_path(data_dir: str, project_id: str) -> Optional[str]:
    """
    查找文档路径

    Args:
        data_dir: 数据目录
        project_id: 项目ID

    Returns:
        Optional[str]: 文档路径或None
    """
    project_data_dir = os.path.join(data_dir, project_id)
    documents_dir = os.path.join(project_data_dir, DEFAULT_DOCUMENTS_DIR)

    if not os.path.exists(documents_dir):
        logger.error(f"文档目录不存在: {documents_dir}")
        return None

    document_files = [f for f in os.listdir(documents_dir) if f.endswith('.json')]
    if not document_files:
        return None

    document_path = os.path.join(documents_dir, document_files[0])

    try:
        with open(document_path, 'r', encoding=ENCODING_UTF8) as f:
            document_data = json.load(f)
        original_file_name = document_data.get("file_name", "")

        if original_file_name:
            original_file_path = os.path.join(
                os.path.dirname(document_path), original_file_name
            )
            if os.path.exists(original_file_path):
                return original_file_path
    except Exception as e:
        logger.error(f"获取文档信息时出错: {str(e)}")

    return None


def _build_import_command(
    project_name: str,
    uploaded_file_path: str,
    document_path: Optional[str]
) -> List[str]:
    """
    构建导入命令

    Args:
        project_name: 项目名称
        uploaded_file_path: 上传文件路径
        document_path: 文档路径

    Returns:
        List[str]: 命令参数列表
    """
    cmd_parts = [
        'python', 'main.py',
        '--config', 'config.json',
        '--project', project_name,
        '--import_questions', uploaded_file_path
    ]

    if document_path:
        cmd_parts.extend(['--document', document_path])

    return cmd_parts


def _parse_import_result(output: str) -> int:
    """
    解析导入结果

    Args:
        output: 命令输出

    Returns:
        int: 导入数量
    """
    imported_count = 0
    for line in output.split("\n"):
        if IMPORT_RESULT_KEYWORD in line.lower():
            try:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.lower() == IMPORT_COUNT_KEYWORD:
                        imported_count = int(parts[i + 1])
                        break
            except Exception:
                imported_count = 0
    return imported_count
