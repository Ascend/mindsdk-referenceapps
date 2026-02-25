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
import shlex
import subprocess
import time
from queue import Queue, Empty
from threading import Thread
from typing import Any, Dict, Generator, List, Tuple
from urllib.parse import unquote

from flask import Blueprint, request, Response

from backend.config.config import Config
from backend.config.memory_config import MemoryConfig
from backend.utils.logger import init_logger
from backend.utils.validation_utils import contains_sensitive_keyword
from backend.models.constants import (
    OUTPUT_READ_INTERVAL_SECONDS,
    COMMAND_PREVIEW_LENGTH,
    COMMAND_BUFFER_SIZE,
    COMMAND_TIMEOUT_SECONDS,
    DEFAULT_CONFIG_PATH,
    ENCODING_UTF8,
    SSE_CONTENT_TYPE,
    SSE_CACHE_CONTROL,
    SSE_BUFFER_HEADER,
    SSE_BUFFER_VALUE,
    SENSITIVE_COMMAND_PLACEHOLDER,
    ALLOWED_PYTHON_COMMAND_PATTERNS,
    ALLOWED_PYTHON_SCRIPTS,
    MAX_COMMAND_LENGTH,
    SSE_TYPE_OUTPUT,
    SSE_TYPE_COMPLETE,
    SSE_FIELD_TYPE,
    SSE_FIELD_CONTENT,
    SSE_FIELD_EXIT_CODE,
)

command_bp = Blueprint('command', __name__)

logger = init_logger(__name__)


@command_bp.route('/execute')
def execute_command() -> Response:
    """
    命令执行路由 - 返回Server-Sent Events流

    响应数据结构:
    {
      "type": "output" | "complete",
      "content": string,      // 输出的文本内容
      "exitCode": number     // 仅在type为"complete"时存在
    }
    """
    # 入口注释：解析、验证命令并以 SSE 形式返回执行输出
    encoded_command = request.args.get('command')
    if not encoded_command:
        logger.warning("Execute command called without command parameter")
        return Response("No command provided", status=400)

    if len(encoded_command) > MAX_COMMAND_LENGTH:
        logger.warning(f"Command parameter too long: {len(encoded_command)} > {MAX_COMMAND_LENGTH}")
        return Response(f"命令参数长度超过限制({MAX_COMMAND_LENGTH})", status=400)

    try:
        command, args = _validate_and_decode_command(encoded_command)
        safe_command = _get_safe_command_preview(command)

        logger.debug('command_execute','started',
                      {'command_preview': safe_command, 'args_count': len(args), 'first_arg': args[0] if args else None})

        # 注入 -u 以确保 Python 子进程无缓冲输出
        args = _inject_python_unbuffered(args)
        process, q_stdout, q_stderr = _setup_command_execution(args)

        generator = _create_sse_generator(process, q_stdout, q_stderr, safe_command)
        headers = _build_sse_headers()

        response = Response(generator, mimetype=SSE_CONTENT_TYPE, headers=headers)
        logger.debug(
            'command_execute',
            'stream_started',
            {'command_preview': safe_command}
        )
        return response
    except ValueError as e:
        # 命令白名单验证失败
        logger.warning(f"Command validation failed: {e}")
        return Response(f"命令验证失败: {str(e)}", status=403)
    except Exception as e:
        logger.error(f"Command execution failed: {e}", exc_info=True)
        return Response("命令执行失败", status=500)


def _is_allowed_python_command(command: str) -> bool:
    """
    检查是否为允许的Python命令

    支持多种Python命令格式：
    - python (标准)
    - python3 (Python 3.x)
    - python3.9 (特定版本)
    - py (Windows启动器)
    - /usr/bin/python3 (完整路径)

    Args:
        command: 命令字符串

    Returns:
        bool: 是否为允许的Python命令
    """
    command_lower = command.lower().strip()

    # 检查是否匹配允许的模式
    for pattern in ALLOWED_PYTHON_COMMAND_PATTERNS:
        if command_lower == pattern or command_lower.startswith(pattern + '.'):
            return True

    # 检查是否为完整路径形式的Python命令
    if '/' in command_lower or '\\' in command_lower:
        basename = os.path.basename(command_lower)
        for pattern in ALLOWED_PYTHON_COMMAND_PATTERNS:
            if basename == pattern or basename.startswith(pattern + '.'):
                return True

    return False

def _validate_and_decode_command(encoded_command: str) -> Tuple[str, List[str]]:
    """
    验证并解码命令

    使用白名单验证，只允许执行预定义的安全命令。

    Args:
        encoded_command: URL编码的命令

    Returns:
        Tuple[str, List[str]]: (解码后的命令, 参数列表)

    Raises:
        ValueError: 命令不在白名单中
    """
    command = unquote(encoded_command)
    args = shlex.split(command)

    # 白名单验证
    if not args:
        raise ValueError("空命令")

    base_command = args[0]
    if not _is_allowed_python_command(base_command):
        raise ValueError(f"不允许的命令: {base_command}")

    if len(args) < 2:
        raise ValueError("Python 命令缺少脚本参数")

    # 处理 -u 参数
    script_index = 1
    if args[1] == '-u' and len(args) > 2:
        script_index = 2

    script_name = os.path.basename(args[script_index])
    if script_name not in ALLOWED_PYTHON_SCRIPTS:
        raise ValueError(f"不允许的脚本: {script_name}")

    # 转换 --document 参数为绝对路径
    args = _resolve_document_path(args)

    return command, args

def _resolve_document_path(args: list) -> list:
    """
    将 --document 参数的相对路径转换为绝对路径

    Args:
        args: 命令参数列表

    Returns:
        list: 处理后的参数列表
    """
    import os

    args = args.copy()

    for i, arg in enumerate(args):
        if arg == '--document' and i + 1 < len(args):
            doc_path = args[i + 1]
            # 如果路径是相对路径，转换为基于 data_dir 的绝对路径
            if not os.path.isabs(doc_path) and not doc_path.startswith('data/'):
                try:
                    config = Config.load(DEFAULT_CONFIG_PATH)
                    full_path = os.path.join(config.data_dir, doc_path)
                    args[i + 1] = full_path
                    logger.debug(f"Document path resolved: {doc_path} -> {full_path}")
                except Exception as e:
                    logger.warning(f"Failed to resolve document path: {e}")
            break

    return args

def _get_safe_command_preview(command: str) -> str:
    """
    获取安全的命令预览（过滤敏感信息）

    Args:
        command: 原始命令

    Returns:
        str: 安全的命令预览
    """
    if contains_sensitive_keyword(command):
        return SENSITIVE_COMMAND_PLACEHOLDER
    return command[:COMMAND_PREVIEW_LENGTH]


def _inject_python_unbuffered(args: List[str]) -> List[str]:
    """
    为Python命令注入-u参数（无缓冲输出）

    Args:
        args: 原始参数列表

    Returns:
        List[str]: 处理后的参数列表
    """
    if args and args[0] == "python" and "main.py" in args:
        args = args.copy()
        args.insert(1, "-u")
    return args


def _setup_command_execution(
    args: List[str]
) -> Tuple[subprocess.Popen, Queue, Queue]:
    """
    设置命令执行环境

    Args:
        args: 命令参数列表

    Returns:
        Tuple[Popen, Queue, Queue]: (进程对象, stdout队列, stderr队列)
    """
    llm_api_key = MemoryConfig.get_llm_api_key()
    stdin_data = ""
    if llm_api_key:
        stdin_data = json.dumps({"llm_api_key": llm_api_key})
        logger.debug(f"Passing API key via stdin (length: {len(llm_api_key)})")
    else:
        logger.debug("No API key in memory, stdin will be empty")

    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding=ENCODING_UTF8,
        bufsize=COMMAND_BUFFER_SIZE,
    )

    if stdin_data:
        process.stdin.write(stdin_data)
    process.stdin.close()

    q_stdout: Queue = Queue()
    q_stderr: Queue = Queue()

    t_stdout = Thread(target=_enqueue_output, args=(process.stdout, q_stdout))
    t_stderr = Thread(target=_enqueue_output, args=(process.stderr, q_stderr))

    t_stdout.daemon = True
    t_stderr.daemon = True

    t_stdout.start()
    t_stderr.start()

    return process, q_stdout, q_stderr


def _create_sse_generator(
    process: subprocess.Popen,
    q_stdout: Queue,
    q_stderr: Queue,
    safe_command: str
) -> Generator[str, None, None]:
    """
    创建SSE事件生成器

    Args:
        process: 子进程对象
        q_stdout: stdout队列
        q_stderr: stderr队列
        safe_command: 安全的命令预览

    Yields:
        str: SSE事件数据
    """
    start_time = time.time()

    try:
        while process.poll() is None or not q_stdout.empty() or not q_stderr.empty():
            # 超时检查
            elapsed = time.time() - start_time
            if elapsed > COMMAND_TIMEOUT_SECONDS:
                process.terminate()
                logger.warning(f"Command terminated due to timeout: {safe_command}")
                yield _format_sse_event({
                    SSE_FIELD_TYPE: SSE_TYPE_OUTPUT,
                    SSE_FIELD_CONTENT: f"ERROR: 命令执行超时（{COMMAND_TIMEOUT_SECONDS}秒）"
                })
                yield _format_sse_event({SSE_FIELD_TYPE: SSE_TYPE_COMPLETE, SSE_FIELD_EXIT_CODE: -1})
                return

            yield from _drain_output_queue(q_stdout, is_error=False)
            yield from _drain_output_queue(q_stderr, is_error=True)
            time.sleep(OUTPUT_READ_INTERVAL_SECONDS)

        exit_code = process.returncode
        logger.debug(
            'command_execute',
            'completed',
            {'exit_code': exit_code, 'command_preview': safe_command}
        )
        yield _format_sse_event({SSE_FIELD_TYPE: SSE_TYPE_COMPLETE, SSE_FIELD_EXIT_CODE: exit_code})
    except Exception as e:
        logger.error(f"Error in command execution stream: {e}", exc_info=True)
        yield _format_sse_event({SSE_FIELD_TYPE: SSE_TYPE_OUTPUT, SSE_FIELD_CONTENT: "命令执行出错"})
    finally:
        _cleanup_process(process)


def _drain_output_queue(
    queue: Queue,
    is_error: bool
) -> Generator[str, None, None]:
    """
    排空输出队列

    Args:
        queue: 输出队列
        is_error: 是否为错误输出

    Yields:
        str: SSE事件数据
    """
    while True:
        try:
            line = queue.get_nowait()
            content = f"ERROR: {line}" if is_error else line
            yield _format_sse_event({SSE_FIELD_TYPE: SSE_TYPE_OUTPUT, SSE_FIELD_CONTENT: content})
        except Empty:
            break


def _format_sse_event(data: Dict[str, Any]) -> str:
    """
    格式化SSE事件

    Args:
        data: 事件数据

    Returns:
        str: 格式化的SSE事件字符串
    """
    return f'data: {json.dumps(data)}\n\n'


def _build_sse_headers() -> Dict[str, str]:
    """
    构建SSE响应头

    Returns:
        Dict[str, str]: 响应头字典
    """
    return {
        "Cache-Control": SSE_CACHE_CONTROL,
        SSE_BUFFER_HEADER: SSE_BUFFER_VALUE
    }


def _cleanup_process(process: subprocess.Popen) -> None:
    """
    清理进程资源

    Args:
        process: 子进程对象
    """
    if process.stdout and not process.stdout.closed:
        process.stdout.close()
    if process.stderr and not process.stderr.closed:
        process.stderr.close()
    if process.poll() is None:
        process.terminate()
        process.wait()


def _enqueue_output(out, queue: Queue) -> None:
    """
    将输出放入队列

    Args:
        out: 输出流
        queue: 目标队列
    """
    try:
        for line in iter(out.readline, ''):
            queue.put(line.strip())
    except UnicodeDecodeError as e:
        error_msg = f"Error decoding process output: {str(e)}"
        queue.put(error_msg)
    except Exception as e:
        error_msg = f"Error reading process output: {str(e)}"
        queue.put(error_msg)
    finally:
        out.close()
