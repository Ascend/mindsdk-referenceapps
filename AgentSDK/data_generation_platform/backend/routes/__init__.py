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

from backend.routes.config_routes import config_bp
from backend.routes.file_routes import file_bp
from backend.routes.project_routes import project_bp
from backend.routes.question_routes import question_bp
from backend.routes.command_routes import command_bp
from backend.routes.dataset_routes import dataset_bp

__all__ = [
    'config_bp',
    'file_bp',
    'project_bp',
    'question_bp',
    'command_bp',
    'dataset_bp',
]
