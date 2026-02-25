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

from flask import Flask, render_template, jsonify

from backend.utils.logger import init_logger
from backend.models.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_DEBUG_MODE,
    MAX_CONTENT_LENGTH,
    BYTES_PER_MB,
    CONTENT_SECURITY_POLICY,
)


def create_app() -> Flask:
    """
    应用工厂函数

    创建并配置Flask应用实例，注册所有蓝图。

    Returns:
        Flask: 配置完成的Flask应用实例
    """
    flask_app = Flask(__name__, static_folder='frontend/static', template_folder='frontend/templates')

    # 安全配置：请求体大小限制
    flask_app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

    _register_blueprints(flask_app)
    _register_index_route(flask_app)
    _register_error_handlers(flask_app)
    _register_security_headers(flask_app)

    return flask_app


def _register_blueprints(flask_app: Flask) -> None:
    """
    注册所有路由蓝图

    Args:
        flask_app: Flask应用实例
    """
    from backend.routes import (
        config_bp,
        command_bp,
        file_bp,
        project_bp,
        question_bp,
        dataset_bp
    )

    blueprints = [
        config_bp,
        command_bp,
        file_bp,
        project_bp,
        question_bp,
        dataset_bp
    ]

    for bp in blueprints:
        flask_app.register_blueprint(bp)


def _register_index_route(flask_app: Flask) -> None:
    """
    注册首页路由

    Args:
        flask_app: Flask应用实例
    """
    @flask_app.route('/')
    def index():
        """返回首页模板"""
        return render_template('index.html')


def _register_error_handlers(flask_app: Flask) -> None:
    """
    注册错误处理器

    Args:
        flask_app: Flask应用实例
    """
    @flask_app.errorhandler(413)
    def request_entity_too_large(error):
        """处理请求体过大错误"""
        max_mb = MAX_CONTENT_LENGTH // BYTES_PER_MB
        return jsonify({
            'status': 'error',
            'message': f'请求体过大，最大允许 {max_mb} MB'
        }), 413


def _register_security_headers(flask_app: Flask) -> None:
    """
    注册安全响应头

    Args:
        flask_app: Flask应用实例
    """
    @flask_app.after_request
    def add_security_headers(response):
        """添加安全响应头"""
        # 防止 MIME 类型嗅探
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # 防止点击劫持
        response.headers['X-Frame-Options'] = 'DENY'
        # XSS 保护
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # 内容安全策略
        response.headers['Content-Security-Policy'] = CONTENT_SECURITY_POLICY
        # 引用策略
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response


app = create_app()

# 初始化日志记录器
logger = init_logger(__name__)
logger.info("Application started")


if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', str(DEFAULT_PORT)))

    app.run(
        debug=DEFAULT_DEBUG_MODE,
        host=DEFAULT_HOST,
        port=port,
        use_reloader=False
    )
