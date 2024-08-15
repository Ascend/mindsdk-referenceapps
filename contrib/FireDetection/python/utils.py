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


def file_base_check(path: str) -> None:
    file_name = os.path.basename(path)
    if not path or not os.path.isfile(path):
        raise Exception('The file:{} does not exist!'.format(file_name))
    if os.path.islink(path):
        raise Exception('The file:{} is link. invalid file!'.format(file_name))
    if not os.access(path, mode=os.R_OK):
        raise Exception('The file:{} is unreadable!'.format(file_name))


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
    file_base_check(infer_config_instance["video_path"])
    file_path = infer_config_instance["video_saved_path"]
    file_path = infer_config_instance["model_path"]
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if os.path.exists(file_path):
        os.remove(file_path)
    if infer_config_instance["skip_frame_number"] < 1:
        raise Exception('skip_frame_number must >= 1.')
    return logger_instance, infer_config_instance


logger, infer_config = _init()