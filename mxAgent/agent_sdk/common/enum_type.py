# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import enum

from pydantic import BaseModel


class PlanStrategyType(enum.Enum):
    REACT = 1
    RESEARCH = 2
    COT = 3
    EMPTY = 4
    SOP = 5
    DHP = 6


class AgentRunStatus(BaseModel):
    success_cnt: int = 0
    total_cnt: int = 0

    def __str__(self):
        rate = round((self.success_cnt / self.total_cnt) * 100, 2)
        return str(rate) + f"% {self.success_cnt}/{self.total_cnt}"