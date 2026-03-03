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

import logging
from argparse import ArgumentParser
from logging import StreamHandler
from pathlib import Path

from datasets import load_dataset

logger = logging.getLogger(__name__)
logger.addHandler(StreamHandler())

parser = ArgumentParser()
parser.add_argument("--path", type=str, required=True)
parser.add_argument("--output", type=str, default="search.jsonl")
parsed_args = parser.parse_args()

data_path = Path(parsed_args.path)

if not data_path.exists():
    raise FileNotFoundError(f"given path: {parsed_args.path} is not exist.")

try:
    data = load_dataset(str(data_path.resolve()), "search")
except Exception as e:
    logger.info(f"unable to load datasets from given path: {parsed_args.path}")
    raise

if "validation" not in data.column_names:
    raise RuntimeError("unable to find column 'validation' from gaia2/search, check if dataset "
                       "has been download successfully.")

data["validation"].to_json(parsed_args.output)
