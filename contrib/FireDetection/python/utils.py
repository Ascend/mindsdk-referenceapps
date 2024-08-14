#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.
Description: Common function for utilization.
Author: MindX SDK
Create: 2024
History: NA
"""
import json
import os
import logging


def file_base_check(file_path: str) -> None:
    base_name = os.path.basename(file_path)
    if not file_path or not os.path.isfile(file_path):
        raise FileNotFoundError(f'the file:{base_name} does not exist!')
    if os.path.islink(file_path):
        raise Exception(f'the file:{base_name} is link. invalid file!')
    if not os.access(file_path, mode=os.R_OK):
        raise FileNotFoundError(f'the file:{base_name} is unreadable!')


def read_json_config(json_path: str) -> dict:
    file_base_check(json_path)
    try:
        with open(json_path, "r") as fr:
            json_data = json.load(fr)
    except json.decoder.JSONDecodeError as e:
        raise Exception('json decode error: config file is not a json format file!') from e
    finally:
        pass
    if not isinstance(json_data, dict):
        raise Exception('json decode error: config file is not a json format file!')
    return json_data


def _init():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger_instance = logging.getLogger()
    file_base_check("./infer_config.json")
    infer_config_instance = read_json_config("./infer_config.json")
    directory = os.path.dirname(infer_config_instance ["video_saved_path"])
    if not os.path.exists(directory):
        os.makedirs(directory)
    return logger_instance, infer_config_instance


logger, infer_config = _init()