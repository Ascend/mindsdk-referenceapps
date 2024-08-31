# Copyright 2024 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

import argparse
from multiprocessing import Process
import os
import sys


class FastChatLLM:

    def __init__(self,
                 host: str,
                 port: int,
                 model_path: str,
                 device: int,
                 ssl: bool,
                 cert_file: str,
                 key_file: str):
        self._host = host
        self._port = port
        self._model_path = model_path
        self._device = device
        self._ssl = ssl
        self._cert_file = cert_file
        self._key_file = key_file

    def start(self):
        def controller():
            os.system(f"python3 -m fastchat.serve.controller --host {self._host} ")

        def model_worker():
            os.environ["ASCEND_RT_VISIBLE_DEVICES"] = str(self._device)
            os.system(f"python3 -m fastchat.serve.model_worker --host {self._host} "
                      f"--model-path {self._model_path} --device npu")

        def api_server():
            if self._ssl:
                os.environ["SSL_KEYFILE"] = self._key_file
                os.environ["SSL_CERTFILE"] = self._cert_file
                os.system(f"python3 -m fastchat.serve.openai_api_server --host {self._host} "
                          f"--port {self._port} --ssl")
            else:
                os.system(f"python3 -m fastchat.serve.openai_api_server --host {self._host} "
                          f"--port {self._port}")

        Process(target=controller).start()
        Process(target=model_worker).start()
        Process(target=api_server).start()


def create_fastchat():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--model_path", type=str)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--ssl", action="store_true", required=False, default=False)
    parser.add_argument("--cert_file", type=str)
    parser.add_argument("--key_file", type=str)
    args = parser.parse_args()

    llm = FastChatLLM(args.host,
                      args.port,
                      args.model_path,
                      args.device,
                      args.ssl,
                      args.cert_file,
                      args.key_file)

    llm.start()


if __name__ == "__main__":
    sys.exit(create_fastchat())
