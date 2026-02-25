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

import mimetypes
import os
from typing import Dict, Optional, Tuple, Any

from backend.models.constants import BYTES_PER_MB
from backend.utils.file_utils import secure_filename
from backend.utils.logger import init_logger

logger = init_logger(__name__)


class FileValidator:
    """文件校验器"""
    
    # 默认文件名最大长度
    MAX_FILENAME_LENGTH = 255
    
    # 默认文件最大大小（10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # 默认允许的文件类型
    DEFAULT_ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx', 'md', 'xlsx'
    }
    
    # 危险文件扩展名（严格禁止）
    DANGEROUS_EXTENSIONS = {
        'exe', 'dll', 'scr', 'bat', 'cmd', 'com', 'pif', 'jar', 'vbe', 
        'js', 'msi', 'sh', 'ps1', 'php', 'asp', 'jsp', 'pl', 'py', 'rb'
    }

    def __init__(self, 
                  max_filename_length: Optional[int] = None,
                  max_file_size: Optional[int] = None,
                  allowed_extensions: Optional[set] = None):
        """
        # 读取配置：校验文件是否存在
        初始化文件校验器
        
        Args:
            max_filename_length: 最大文件名长度
            max_file_size: 最大文件大小（字节）
            allowed_extensions: 允许的文件扩展名集合
        """
        # 构造函数：允许自定义最大长度、最大大小与允许的文件扩展名集合
        self.max_filename_length = max_filename_length or self.MAX_FILENAME_LENGTH
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE
        self.allowed_extensions = allowed_extensions or self.DEFAULT_ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file_exists(file_path: str) -> Tuple[bool, str]:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        # 校验文件是否存在
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        return True, ""

    @staticmethod
    def validate_symlink(file_path: str) -> Tuple[bool, str]:
        """
        检查是否为软链接

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        # 如果文件不存在，跳过软链接检查
        if not os.path.exists(file_path):
            return True, ""  # 如果文件不存在，跳过软链接检查

        if os.path.islink(file_path):
            return False, f"不允许软链接文件: {file_path}"

        return True, ""

    @staticmethod
    def validate_path_security(file_path: Optional[str], base_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        验证路径安全性（防路径遍历攻击）

        Args:
            file_path: 文件路径
            base_dir: 基础目录

        Returns:
            Tuple[bool, str]: (是否安全, 错误消息)
        """
        # 路径安全性校验：防止路径遍历与越界访问
        if not file_path:
            return False, "文件路径不能为空"

        if not isinstance(file_path, str):
            return False, "文件路径必须是字符串"

        # 标准化路径
        normalized_path = os.path.normpath(file_path)

        # 检查路径遍历攻击
        if '..' in normalized_path or normalized_path.startswith('/') or normalized_path.startswith('\\'):
            return False, "检测到路径遍历攻击"

        # 如果提供了基础目录，确保文件在基础目录内
        if base_dir:
            # 确保 base_dir 是字符串类型
            if not isinstance(base_dir, str):
                return False, "基础目录必须是字符串"
            # 标准化路径
            abs_path = os.path.abspath(os.path.join(base_dir, file_path))
            abs_base = os.path.abspath(base_dir)

            # 检查是否在基础目录内（允许子目录）
            if not abs_path.startswith(abs_base + os.sep) and abs_path != abs_base:
                return False, f"文件路径超出允许目录: {base_dir}"

        return True, ""

    @staticmethod
    def validate_file_upload(file_storage, upload_dir: Optional[str] = None,
                             validator: Optional['FileValidator'] = None) -> Dict[str, Any]:
        """验证上传的文件（兼容Flask的FileStorage对象）"""
        # 上传文件校验入口（Flask/werkzeug FileStorage 对象）
        if validator is None:
            validator = FileValidator()

        if not file_storage or not file_storage.filename:
            return FileValidator._make_error_result('没有选择文件或文件名为空')

        safe_filename = secure_filename(file_storage.filename)
        if not safe_filename:
            return FileValidator._make_error_result('无效的文件名')

        result = {
            'valid': True, 'filename': safe_filename,
            'errors': [], 'warnings': [], 'checks': {},
        }

        FileValidator._apply_check(result, 'filename_length', *validator.validate_filename_length(safe_filename))
        FileValidator._apply_check(result, 'file_type', *validator.validate_file_type(safe_filename))

        if not result['valid']:
            return result

        FileValidator._check_upload_file_size(result, file_storage, validator)

        if upload_dir:
            FileValidator._apply_check(result, 'path_security',
                                       *validator.validate_path_security(safe_filename, upload_dir))

        return result

    @staticmethod
    def _check_upload_file_size(result: Dict[str, Any], file_storage, validator: 'FileValidator') -> None:
        """检查上传文件的大小"""
        try:
            file_size = len(file_storage.read())
            file_storage.seek(0)

            if file_size > validator.max_file_size:
                error_msg = f"文件过大，最大允许 {validator.max_file_size / BYTES_PER_MB:.1f} MB"
                FileValidator._apply_check(result, 'file_size', False, error_msg)
        except (IOError, OSError) as e:
            logger.warning(f"文件大小检查失败: {str(e)}")
            pass

    @staticmethod
    def _apply_check(result: Dict[str, Any], check_name: str, valid: bool, error: str) -> None:
        """将单项校验结果写入综合结果字典"""
        result['checks'][check_name] = {'valid': valid, 'error': error}
        if not valid:
            result['valid'] = False
            result['errors'].append(error)

    @staticmethod
    def _make_error_result(error_msg: str) -> Dict[str, Any]:
        """创建包含单条错误的校验结果"""
        return {'valid': False, 'errors': [error_msg], 'warnings': [], 'checks': {}}

    def validate_filename_length(self, filename: Optional[str]) -> Tuple[bool, str]:
        """
        检查文件名长度
        
        Args:
            filename: 文件名
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        # 检查文件名长度
        """
        if not filename:
            return False, "文件名不能为空"
        
        if len(filename) > self.max_filename_length:
            return False, f"文件名过长，最大允许 {self.max_filename_length} 字符"
        
        return True, ""

    def validate_file_size(self, file_path: str) -> Tuple[bool, str]:
        """
        检查文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        # 尝试获取并比较文件大小
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return False, f"文件过大，最大允许 {self.max_file_size / BYTES_PER_MB:.1f} MB"
            return True, ""
        except OSError:
            return False, "无法获取文件大小"

    def validate_file_type(self, filename: Optional[str], file_path: Optional[str] = None) -> Tuple[bool, str]:
        # 文件类型有效性检查
        """
        检查文件类型
        
        Args:
            filename: 文件名
            file_path: 文件路径（可选）
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not filename:
            return False, "文件名不能为空"
        
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        ext = ext.lower().lstrip('.')
        
        if not ext:
            return False, "文件必须有扩展名"
        
        # 检查是否为危险文件类型
        if ext in self.DANGEROUS_EXTENSIONS:
            return False, f"不支持的文件类型: .{ext}"
        
        # 检查是否为允许的文件类型
        if ext not in self.allowed_extensions:
            return False, f"不支持的文件类型 .{ext}，允许的类型: {', '.join(sorted(self.allowed_extensions))}"
        
        # 如果提供了文件路径，可以进一步验证MIME类型
        if file_path and os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type and mime_type.startswith('application/'):
                # 对可执行文件类型进行额外检查
                if mime_type in ['application/x-msdownload', 'application/x-msdos-program']:
                    return False, "不允许的可执行文件类型"
        
        return True, ""

    def validate_file(self, filename: Optional[str], file_path: Optional[str] = None, base_dir: Optional[str] = None) -> Dict[str, Any]:
        """综合文件校验"""
        result = {
            'valid': True, 'filename': filename, 'file_path': file_path,
            'errors': [], 'warnings': [], 'checks': {},
        }

        self._apply_check(result, 'filename_length', *self.validate_filename_length(filename))
        self._apply_check(result, 'file_type', *self.validate_file_type(filename, file_path))

        if file_path:
            self._validate_file_path_checks(result, file_path, base_dir)

        return result

    def _validate_file_path_checks(self, result: Dict[str, Any], file_path: str, base_dir: Optional[str]) -> None:
        """对已有路径的文件执行存在性、链接、大小和安全性校验"""
        normalized_file_path = os.path.normpath(file_path)
        check_path = normalized_file_path
        if base_dir and not os.path.isabs(normalized_file_path):
            normalized_base_dir = os.path.normpath(base_dir)
            # 兼容“相对路径但已携带 base_dir 前缀”的场景，避免重复拼接目录
            if not (
                normalized_file_path == normalized_base_dir
                or normalized_file_path.startswith(normalized_base_dir + os.sep)
            ):
                check_path = os.path.join(normalized_base_dir, normalized_file_path)

        self._apply_check(result, 'file_exists', *self.validate_file_exists(check_path))
        self._apply_check(result, 'symlink', *self.validate_symlink(check_path))
        self._apply_check(result, 'file_size', *self.validate_file_size(check_path))

        # 对绝对路径场景，将路径转换为相对 base_dir 的形式再做路径安全校验
        path_for_security = normalized_file_path
        security_base_dir = base_dir
        if os.path.isabs(check_path):
            security_base_dir = base_dir or os.path.dirname(check_path)
            path_for_security = os.path.relpath(check_path, security_base_dir)

        self._apply_check(result, 'path_security', *self.validate_path_security(path_for_security, security_base_dir))



# 全局默认实例
default_validator = FileValidator()


# 向后兼容的函数接口
def validate_file_type(filename: Optional[str], file_path: Optional[str] = None) -> bool:
    """
    向后兼容的文件类型验证函数
    
    Args:
        filename: 文件名
        file_path: 文件路径
        
    Returns:
        bool: 是否通过验证
    """
    if filename is None:
        return False
    valid, _ = default_validator.validate_file_type(filename, file_path)
    return valid


def validate_file_upload(file_storage, upload_dir: Optional[str] = None) -> bool:
    """
    向后兼容的文件上传验证函数
    
    Args:
        file_storage: Flask的FileStorage对象
        upload_dir: 上传目录
        
    Returns:
        bool: 是否通过验证
    """
    result = FileValidator.validate_file_upload(file_storage, upload_dir)
    return result.get('valid', False)


def validate_path_security(file_path: Optional[str], base_dir: Optional[str]) -> Tuple[bool, str]:
    """
    向后兼容的路径安全验证函数
    
    Args:
        file_path: 文件路径
        base_dir: 基础目录
        
    Returns:
        Tuple[bool, str]: (是否安全, 错误消息)
    """
    if file_path is None or base_dir is None:
        return False, "参数不能为空"
    return default_validator.validate_path_security(file_path, base_dir)


__all__ = [
    'FileValidator',
    'validate_file_type',
    'validate_file_upload',
    'validate_path_security'
]
