# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import enum


class ErrorType(enum.Enum):
    INPUT_NOT_STR = 0
    FILE_TYPE_ERROR = 1
    FILE_READ_ERROR = 2
    NO_DICT_ERROR = 3
    YAML_LOAD_ERROR = 3
    INVALID_TOOL_ERROR = 4
    NO_NAME_ERROR = 5
    INVALID_INPUT_PARAM = 6
    INVALID_OUPUT_PARAM = 7
    NODE_CONFILCT_ERROR = 8
    INVALID_DEPENDENCY = 9
    NODE_NOT_DEPENDENT = 10


ERROR_MAP = {
    ErrorType.INPUT_NOT_STR: "Invalid arguements type: the content need a str",
    ErrorType.FILE_TYPE_ERROR: "The type of file {filename} is not supported, only json or yaml is fine",
    ErrorType.FILE_READ_ERROR: "Failed to read the file {filename}: Error message: {error}",
    ErrorType.NO_DICT_ERROR: "The content cannot be converted to dict format.",
    ErrorType.YAML_LOAD_ERROR: "Loading content with YAML error: {error}",
    ErrorType.INVALID_TOOL_ERROR: "The tool {toolname} doesn't exist.",
    ErrorType.NO_NAME_ERROR: "some nodes did not assign a value to a necessary parameter [name] and [toolname].",
    ErrorType.INVALID_INPUT_PARAM: "Additional parameters {params} were input during the calling tool {tool}.",
    ErrorType.INVALID_OUPUT_PARAM: "These parameters {params} do not exist in the output of the node {node}.",
    ErrorType.NODE_CONFILCT_ERROR: "the Node name {name} is duplicated.",
    ErrorType.INVALID_DEPENDENCY:  "The current node depends on node {node} that does not exist in the plan.",
    ErrorType.NODE_NOT_DEPENDENT: "The output of node {node} is being used, but it is not within the dependency"

}


class PlanStrategyType(enum.Enum):
    REACT = 1
    RESEARCH = 2
    COT = 3
    EMPTY = 4
    SOP = 5
    DHP = 6