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

Agent execution engine for OpenAIRouter-compatible API interations.

This module provides routing and execution capabilities for agents-based
reinforcement learning with OpenAI-compatible model servers.
"""

import logging
import sys

# 日志格式配置
_LOG_FORMAT_TEMPLATE = "%(levelname)s %(asctime)s [Dataset Python] [%(filename)s:%(lineno)d] %(funcName)s: %(message)s"
_TIMESTAMP_FORMAT = "%m-%d %H:%M:%S"


def initialize_logging_system(component_name: str) -> logging.Logger:
    """
    初始化并配置日志系统组件
    
    Args:
        component_name (str): 组件名称用于标识日志来源
        
    Returns:
        logging.Logger: 配置好的日志记录器实例
    """
    # 获取或创建日志记录器
    logger_component = logging.getLogger(component_name)
    
    # 检查是否已存在处理器以避免重复配置
    if len(logger_component.handlers) > 0:
        return logger_component
    
    # 设置日志级别
    logger_component.setLevel(logging.INFO)
    
    # 创建控制台输出处理器
    console_output_handler = logging.StreamHandler(sys.stdout)
    console_output_handler.setLevel(logging.INFO)
    
    # 配置日志格式化器
    message_formatter = logging.Formatter(_LOG_FORMAT_TEMPLATE, _TIMESTAMP_FORMAT)
    console_output_handler.setFormatter(message_formatter)
    
    # 应用配置并禁用传播
    logger_component.addHandler(console_output_handler)
    logger_component.propagate = False
    
    return logger_component


# 保持向后兼容性的别名
init_logger = initialize_logging_system