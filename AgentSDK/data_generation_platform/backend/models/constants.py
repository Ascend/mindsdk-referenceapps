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

import re

# ==================== HTTP 状态码常量 ====================
HTTP_OK = 200
HTTP_MULTI_STATUS = 207
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_UNSUPPORTED_MEDIA_TYPE = 415
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_GATEWAY_TIMEOUT = 504

# ==================== 分页常量 ====================
DEFAULT_PAGE_SIZE = 5
DEFAULT_PAGE_NUMBER = 1
INDEX_ONE = 1
MAX_PAGE_SIZE = 100
PAGINATION_DISPLAY_RANGE = 1

# ==================== 数据集格式常量 ====================
DATASET_FORMAT_ALPACA = "alpaca"
DATASET_FORMAT_SHAREGPT = "sharegpt"
DATASET_FORMAT_CUSTOM = "custom"
DEFAULT_DATASET_FORMAT = DATASET_FORMAT_ALPACA

# ==================== 数据集文件类型常量 ====================
DATASET_FILE_TYPE_JSON = "json"
DATASET_FILE_TYPE_JSONL = "jsonl"
DEFAULT_DATASET_FILE_TYPE = DATASET_FILE_TYPE_JSON

# ==================== 文档状态常量 ====================
DOCUMENT_STATUS_UNPROCESSED = 0  # 未处理
DOCUMENT_STATUS_CHUNKED = 1      # 已分割
DOCUMENT_STATUS_QUESTIONS_GENERATED = 2  # 已生成问题
DEFAULT_DOCUMENT_STATUS = DOCUMENT_STATUS_UNPROCESSED

# ==================== 问题状态常量 ====================
QUESTION_STATUS_UNANSWERED = 0  # 未回答
QUESTION_STATUS_ANSWERED = 1    # 已回答
QUESTION_STATUS_REVIEWED = 2    # 已审核
DEFAULT_QUESTION_STATUS = QUESTION_STATUS_UNANSWERED

# ==================== 文件操作常量 ====================
DEFAULT_DATA_DIR = "data"
DEFAULT_UPLOAD_DIR = "uploads"
DEFAULT_PROJECTS_DIR = "projects"
DEFAULT_QUERIES_DIR = "queries"
DEFAULT_DOCUMENTS_DIR = "documents"
DEFAULT_DOCUMENTS_RAW_DIR = "documents_raw"
DEFAULT_CHUNKS_DIR = "chunks"
DEFAULT_DATASETS_DIR = "datasets"
DEFAULT_QUESTIONS_DIR = "questions"

# ==================== 编码和格式化常量 ====================
ENCODING_UTF8 = 'utf-8'
JSON_INDENT = 2

# ==================== 文件大小格式化常量 ====================
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024
MB_FORMAT_PRECISION = 1  # 文件大小格式化时的小数位数

# ==================== 命令执行常量 ====================
COMMAND_TIMEOUT_SECONDS = 900  # 15分钟
OUTPUT_READ_INTERVAL_SECONDS = 0.1
COMMAND_BUFFER_SIZE = 1

# ==================== 服务器配置常量 ====================
# 安全默认值 - 生产环境不应暴露到公网
DEFAULT_HOST = "127.0.0.1"  # 默认只监听本地
DEFAULT_PORT = 5000
DEFAULT_DEBUG_MODE = False  # 默认关闭调试模式

# ==================== 请求限制常量 ====================
MAX_CONTENT_LENGTH = 128 * 1024 * 1024  # 128 MB

# ==================== HTTP 请求超时常量 ====================
HTTP_REQUEST_CONNECT_TIMEOUT = 100  # 连接超时（秒）
HTTP_REQUEST_READ_TIMEOUT = 900  # 读取超时（秒）- LLM 响应可能较慢

# ==================== 子进程超时常量 ====================
SUBPROCESS_TIMEOUT_SECONDS = 900 # 秒

# ==================== 配置文件常量 ====================
DEFAULT_CONFIG_PATH = "config.json"

# ==================== 文本处理常量 ====================
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_START_INDEX = 0
DEFAULT_PREVIEW_LENGTH = 100
DEFAULT_SPLIT_METHOD = "sentence"

# ==================== LLM 服务常量 ====================
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_MODEL = "gpt-3.5-turbo"
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TEMPERATURE = 0.0
DEFAULT_NUM_QUESTIONS = 3
DEFAULT_LOCAL_API_URL = "http://localhost:11434/api/chat"

# ==================== 默认提示词常量 ====================
DEFAULT_SYSTEM_PROMPT = "system_prompt"
DEFAULT_GENERATE_PROMPT = "Generate questions based on context"
DEFAULT_ANSWER_PROMPT = "Answer the question based on the context"
DEFAULT_CHAIN_OF_THOUGHT_PROMPT = "Think step by step and show your reasoning process before answering"
DEFAULT_QUESTIONS_PER_CHUNK = 3

# ==================== API KEY 校验常量 ====================
API_KEY_MIN_LENGTH = 10
API_KEY_MAX_LENGTH = 200
OPENAI_KEY_PREFIX = "sk-"
OPENAI_KEY_PATTERN = re.compile(r'^sk-[A-Za-z0-9_-]+$')
API_KEY_SUSPICIOUS_PATTERNS = [
    r'(password|passwd|pwd)',
    r'(secret|token)',
    r'(key|api)',
    r'[\<\>]',
]

# ==================== 自定义格式键常量 ====================
CUSTOM_QUESTION_KEY = "instruction"
CUSTOM_ANSWER_KEY = "output"
CUSTOM_SYSTEM_KEY = "system"

# ==================== 文件类型常量 ====================
TEXT_FILE_EXTENSIONS = ['txt', 'text', 'md', 'markdown']
JSON_FILE_EXTENSION = 'json'
YAML_FILE_EXTENSIONS = ['yaml', 'yml']
DOCX_FILE_EXTENSION = ['docx', 'doc']
PDF_FILE_EXTENSION = 'pdf'
XLSX_FILE_EXTENSION = 'xlsx'

# ==================== 上传文件验证常量 ====================
ALLOWED_UPLOAD_EXTENSIONS = ['.xlsx']
ALLOWED_DOCUMENT_EXTENSIONS = ['.txt', '.md', '.json', '.docx', '.pdf', '.xlsx']
MAX_FILENAME_LENGTH = 255
DEFAULT_UPLOADED_FILENAME = "uploaded_file.xlsx"

# ==================== 命令执行白名单常量 ====================
ALLOWED_PYTHON_SCRIPTS = ['main.py']  # 允许的 Python 脚本白名单

# Python命令变体白名单（支持多版本兼容）
ALLOWED_PYTHON_COMMAND_PATTERNS = [
    'python',      # 标准python命令
    'python3',     # Python 3.x
    'python3.',    # Python 3.x具体版本 (如 python3.9)
    'py',          # Windows Python启动器
]

# ==================== 配置字段类型常量 ====================
CONFIG_BOOLEAN_FIELDS = ["use_chain_of_thought"]
CONFIG_NUMERIC_FIELDS = ["chunk_size", "chunk_overlap", "max_tokens", "temperature"]

# ==================== 分页显示常量 ====================
PAGINATION_WINDOW_SIZE = 5
PAGINATION_EDGE_THRESHOLD = 3

# ==================== 命令执行常量（补充） ====================
COMMAND_PREVIEW_LENGTH = 100

# ==================== 响应消息常量 ====================
MSG_SUCCESS = "success"
MSG_ERROR = "error"
MSG_PARTIAL_SUCCESS = "partial_success"
MSG_MISSING_PARAM = "Missing required parameter: {}"
MSG_FILE_NOT_FOUND = "File not found"
MSG_ACCESS_DENIED = "Access denied"

# ==================== 敏感字段常量 ====================
SENSITIVE_FIELD_NAMES = [
    'llm_api_key', 'api_key', 'secret', 'password', 'token', 'auth'
]
SENSITIVE_KEYWORDS = ['key', 'token', 'password', 'secret', 'auth']
SENSITIVE_COMMAND_PLACEHOLDER = '[COMMAND_WITH_SENSITIVE_INFO]'
SAFE_FIELDS = ["max_tokens", "custom_question_key", "custom_answer_key", "custom_system_key"]
CONFIG_STORED_IN_MEMORY_PLACEHOLDER = "[STORED_IN_MEMORY]"
CONFIG_FILTERED_PLACEHOLDER = "[FILTERED]"
CONFIG_LLM_API_KEY_FIELD = "llm_api_key"

# ==================== SSE响应常量 ====================
SSE_CONTENT_TYPE = "text/event-stream"
SSE_CACHE_CONTROL = "no-cache"
SSE_BUFFER_HEADER = "X-Accel-Buffering"
SSE_BUFFER_VALUE = "no"

# ==================== JSON内容字段常量 ====================
JSON_CONTENT_FIELDS = ["content", "answer", "chain_of_thought", "status"]

# ==================== 问题可更新字段常量 ====================
QUESTION_UPDATABLE_FIELDS = ["content", "answer", "chain_of_thought", "status"]

# ==================== 参数校验常量 ====================
# ID 格式：字母、数字、下划线、连字符（防路径注入）
ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')
MAX_ID_LENGTH = 128
MAX_STRING_FIELD_LENGTH = 8192      # content/answer 等文本字段
MAX_BATCH_SIZE = 100                  # 批量操作上限
MAX_COMMAND_LENGTH = 1024             # 命令参数最大长度

# 配置字段白名单
ALLOWED_CONFIG_FIELDS = {
    'data_dir', 'llm_provider', 'llm_api_key', 'llm_model', 'llm_api',
    'default_dataset_format', 'default_dataset_file_type',
    'system_prompt', 'generate_prompt', 'answer_prompt', 'chain_of_thought_prompt',
    'chunk_size', 'chunk_overlap', 'max_tokens', 'temperature',
    'custom_question_key', 'custom_answer_key', 'custom_system_key',
    'use_chain_of_thought',
}

# 数值配置范围
CONFIG_NUMERIC_RANGES = {
    'chunk_size': (1, 100000),
    'chunk_overlap': (0, 50000),
    'max_tokens': (1, 8192),
    'temperature': (0.0, 1.0),
}

# 问题 status 允许值
ALLOWED_QUESTION_STATUS = {0, 1, 2}

# 配置字符串字段最大长度
MAX_CONFIG_STRING_LENGTH = 1024
MAX_CONFIG_PROMPT_LENGTH = 8192

# LLM provider 白名单
ALLOWED_LLM_PROVIDERS = {'openai', 'local', 'deepseek', 'ollama'}

# 数据集格式白名单
ALLOWED_DATASET_FORMATS = {'alpaca', 'sharegpt', 'custom'}
ALLOWED_DATASET_FILE_TYPES = {'json', 'jsonl'}

# ==================== 枚举验证配置映射 ====================
CONFIG_ENUM_FIELDS = {
    'llm_provider': ALLOWED_LLM_PROVIDERS,
    'default_dataset_format': ALLOWED_DATASET_FORMATS,
    'default_dataset_file_type': ALLOWED_DATASET_FILE_TYPES,
}

# ==================== 导入结果解析常量 ====================
IMPORT_RESULT_KEYWORD = 'excel导入完成'
IMPORT_COUNT_KEYWORD = '共成功导入'

# ==================== 问题统计初始状态 ====================
QUESTION_STATS_INITIAL = {
    QUESTION_STATUS_UNANSWERED: 0,
    QUESTION_STATUS_ANSWERED: 0,
    QUESTION_STATUS_REVIEWED: 0,
}

# ==================== 内容安全策略常量 ====================
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
    "img-src 'self' data:; "
    "connect-src 'self'"
)

# ==================== 字典键名常量 ====================
# 用于序列化/反序列化的字典键名常量，避免使用魔法字符串
FIELD_ID = 'id'
FIELD_PROJECT_ID = 'project_id'
FIELD_DOCUMENT_ID = 'document_id'
FIELD_CHUNK_ID = 'chunk_id'
FIELD_CONTENT = 'content'
FIELD_ANSWER = 'answer'
FIELD_CHAIN_OF_THOUGHT = 'chain_of_thought'
FIELD_STATUS = 'status'
FIELD_LABELS = 'labels'
FIELD_NAME = 'name'
FIELD_DESCRIPTION = 'description'
FIELD_FORMAT = 'format'
FIELD_FILE_TYPE = 'file_type'
FIELD_SYSTEM_PROMPT = 'system_prompt'
FIELD_QUESTIONS = 'questions'
FIELD_CHUNKS = 'chunks'
FIELD_FILE_NAME = 'file_name'
FIELD_POSITION = 'position'
FIELD_SUMMARY = 'summary'
FIELD_DOCUMENTS = 'documents'
FIELD_DATASETS = 'datasets'

# ==================== 命令行参数常量 ====================
# 用于避免命令行参数中的魔法字符串
ARG_CONFIG = "--config"
ARG_PROJECT = "--project"
ARG_DOCUMENT = "--document"
ARG_GENERATE_QUESTIONS = "--generate_questions"
ARG_GENERATE_ANSWERS = "--generate_answers"
ARG_GENERATE_ANSWERS_NO_CHAIN = "--generate_answers_no_chain"
ARG_CREATE_DATASET = "--create_dataset"
ARG_EXPORT_DATASET = "--export_dataset"
ARG_IMPORT_QUESTIONS = "--import_questions"
ARG_CONFIG_DEFAULT = "config.json"
ARG_STORE_DEFAULT = "store_true"

# ==================== 命令行帮助文本常量 ====================
HELP_CONFIG = "配置文件路径(默认config.json)"
HELP_PROJECT = "项目名称"
HELP_DOCUMENT = "文档文件路径"
HELP_GENERATE_QUESTIONS = "生成问题标志"
HELP_GENERATE_ANSWERS = "生成答案标志"
HELP_GENERATE_ANSWERS_NO_CHAIN = "不生成思维链的答案标志"
HELP_CREATE_DATASET = "创建数据集名称"
HELP_EXPORT_DATASET = "导出数据集名称"
HELP_IMPORT_QUESTIONS = "导入问题的XLSX文件路径"

# ==================== API Key 验证消息常量 ====================
MSG_API_KEY_EMPTY = "API KEY不能为空且必须是字符串类型"
MSG_API_KEY_TOO_SHORT = "API KEY长度不能少于{}个字符"
MSG_API_KEY_TOO_LONG = "API KEY长度不能超过{}个字符"
MSG_API_KEY_PREFIX = "OpenAI API KEY应以 '{}' 开头"
MSG_API_KEY_FORMAT = "OpenAI API KEY格式不正确"
MSG_API_KEY_SUSPICIOUS = "API KEY包含可疑内容: {}"

# ==================== 错误消息常量 ====================
MSG_DOCUMENT_NOT_FOUND = "错误: 文档文件不存在 - {}"
MSG_XLSX_NOT_FOUND = "错误: XLSX文件不存在 - {}"
MSG_NO_DOCUMENTS = "错误: 项目中没有文档，无法导入问题"
MSG_DATASET_NOT_FOUND = "错误: 找不到名为 '{}' 的数据集"
MSG_CONFIG_NOT_FOUND = "错误: 配置文件不存在: {}"

# ==================== Routes 路由相关常量 ====================
# 用于避免 routes 层代码中的魔法字符串
FIELD_QUESTION_ID = 'question_id'
FIELD_QUESTION_IDS = 'question_ids'
FIELD_CHAIN_OF_THOTGHT = 'chain_of_thought'

# SSE 事件类型常量
SSE_TYPE_OUTPUT = 'output'
SSE_TYPE_COMPLETE = 'complete'
SSE_FIELD_TYPE = 'type'
SSE_FIELD_CONTENT = 'content'
SSE_FIELD_EXIT_CODE = 'exitCode'

# API 响应状态常量
RESPONSE_STATUS_SUCCESS = 'success'
RESPONSE_STATUS_ERROR = 'error'

# 批量操作消息常量
BATCH_ERROR_EXCEEDS_LIMIT = '批量操作数量超过上限({})'
BATCH_ERROR_QUESTION_IDS_LIST = 'question_ids must be a list'

# 问题更新相关消息
MSG_INVALID_REQUEST_BODY = 'Invalid request body'
MSG_STATUS_MUST_BE_INTEGER = 'status 必须为整数'
MSG_QUESTION_FILE_NOT_FOUND = 'Question file not found'
MSG_QUESTION_UPDATED_SUCCESS = 'Question updated successfully'
MSG_QUESTION_DELETED_SUCCESS = 'Question deleted successfully'
MSG_DELETE_BATCH_RESULT = "Successfully deleted {} questions"

# dataset_routes 层响应常量
FILE_PATH = 'file_path'
PROJECT_ID = 'project_id'

# ==================== 日志操作名称常量 ====================
# 用于避免 routes 层日志操作名称中的魔法字符串
LOG_OPERATION_PROJECT_LIST = 'project_list'
LOG_OPERATION_PROJECT_DELETE = 'project_delete'
LOG_OPERATION_PROJECT_STATS = 'project_stats'
LOG_OPERATION_GET_PROJECTS = 'get_projects'
LOG_OPERATION_FILE_WRITE = 'file_write'
LOG_OPERATION_FILE_DELETE = 'file_delete'
LOG_OPERATION_FILE_BATCH_DELETE = 'file_batch_delete'
LOG_OPERATION_COMMAND_EXECUTE = 'command_execute'

# ==================== 日志字段常量 ====================
LOG_FIELD_OPERATION = 'operation'
LOG_FIELD_PROJECT_ID = 'project_id'
LOG_FIELD_PROJECT_PATH = 'project_path'
LOG_FIELD_PROJECT_DATA_PATH = 'project_data_path'
LOG_FIELD_PROJECTS_DIR = 'projects_dir'
LOG_FIELD_PROJECTS_COUNT = 'projects_count'
LOG_FIELD_SUCCESS = 'success'
LOG_FIELD_REMOTE_ADDR = 'remote_addr'
LOG_FIELD_COMMAND_PREVIEW = 'command_preview'
LOG_FIELD_EXIT_CODE = 'exit_code'
LOG_FIELD_QUESTION_IDS_COUNT = 'question_ids_count'
LOG_FIELD_TOTAL_COUNT = 'total_count'
LOG_FIELD_SUCCESS_COUNT = 'success_count'
LOG_FIELD_ERROR_COUNT = 'error_count'
LOG_FIELD_DELETED_COUNT = 'deleted_count'

# ==================== ShareGPT 数据格式常量 ====================
# 用于避免 dataset_service.py 中的魔法字符串
SHAREGPT_FIELD_CONVERSATIONS = 'conversations'
SHAREGPT_FIELD_FROM = 'from'
SHAREGPT_FIELD_VALUE = 'value'
SHAREGPT_ROLE_HUMAN = 'human'
SHAREGPT_ROLE_GPT = 'gpt'

# ==================== Dataset Service 数据格式常量 ====================
DATASET_FORMAT_ALPACA = 'alpaca'
DATASET_FORMAT_SHAREGPT = 'sharegpt'
DATASET_FORMAT_CUSTOM = 'custom'

# ==================== Question Routes 日志操作常量 ====================
LOG_OPERATION_DELETE_QUESTION = 'delete_question'
LOG_FIELD_QUESTION_ID = 'question_id'
