# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import enum
import os
import stat
from datetime import datetime, timezone
from loguru import logger

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
    

THOUGHT = "Thought"
ACTION = "Action"
ACTION_INPUT = "Action Input"
OBSERVATION = "Observation"


def save_traj_local(query, traj, path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            new_permissions = 0o755
            os.chmod(directory, new_permissions)
        except Exception as e:
            logger.error(f"make dir error, {e}")
    flag = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    mode = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(path, flags=flag, mode=mode), "a") as fout:
        fout.write("****************TASK START*******************\n")
        fout.write(f"task: {query}\n")
        fout.write(f"trajectory:\n{traj}\n")
        fout.write(f"created_at {str(datetime.now(tz=timezone.utc))}\n")
        fout.write("*****************TASK END*******************\n\n\n")