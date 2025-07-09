import sys
import argparse
import threading
from queue import Queue
from typing import Any
import httpx
import openai
from langchain.chains import LLMChain
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger



class EventData:

    def __init__(self, data, finish_reason):
        self.data = data
        self.finish_reason = finish_reason


class StreamingLLMCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self._is_done = False
        self._queue = Queue()

    def clear(self):
        with self._queue.mutex:
            self._queue.queue.clear()
            self._is_done = False

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self._queue.put(EventData(data=token, finish_reason="0"))

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        self._queue.put(EventData(data="", finish_reason="done"))
        self._is_done = True

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        logger.error(f" error happend:{error}")
        self._queue.put(EventData(data=f"{error}", finish_reason="done"))
        self._is_done = True

    @property
    def stream_gen(self):
        while not self._queue.empty() or not self._is_done:
            try:
                delta = self._queue.get()
                yield str(delta.data)
            except Exception as e:
                logger.error(f"Exception:{e}")

class LLMInfo:
    def __init__(self, base_url, model_name, handler, ssl, ca_path, cert_path, key_path, pwd):
        self.base_url = base_url
        self.model_name = model_name
        self.handler = handler
        self.ssl = ssl
        self.ca_path = ca_path
        self.cert_path = cert_path
        self.key_path = key_path
        self.pwd = pwd


def create_llm_chain(params: LLMInfo):
    base_url = params.base_url
    model_name = params.model_name
    handler = params.handler
    ssl = params.ssl
    ca_path = params.ca_path
    cert_path = params.cert_path
    key_path = params.key_path
    pwd = params.pwd

    if not ssl:
        http_client = httpx.Client()
    else:
        http_client = httpx.Client(
            cert=(cert_path, key_path, pwd),
            verify=ca_path
        )
    root_client = openai.OpenAI(
        base_url=base_url,
        api_key="sk_fake",
        http_client=http_client
    )

    client = root_client.chat.completions

    llm = ChatOpenAI(
        api_key="sk_fake",
        client=client,
        model_name=model_name,
        temperature=0.5,
        streaming=True,
        callbacks=[handler]
    )

    template = """<指令>你是一个旅游专家，请简明扼要回答用户问题。<指令>\n用户问题：{question}"""
    prompt = PromptTemplate.from_template(template)

    # chain = LLMChain(
    #     llm=llm,
    #     prompt=prompt
    # )
    return prompt | llm


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_default_metavar_for_optional(self, action):
        return action.type.__name__

    def _get_default_metavar_for_positional(self, action):
        return action.type.__name__


if __name__ == "__main__":
    parse = argparse.ArgumentParser(formatter_class=CustomFormatter)
    parse.add_argument("--base_url", type=str, default="http://127.0.0.1:1025/v1", help="大模型url base地址")
    parse.add_argument("--model_name", type=str, default="Llama3-8B-Chinese-Chat", help="大模型名称")
    parse.add_argument("--ssl", type=bool, default=False, help="是否开启认证")
    parse.add_argument("--ca_path", type=str, default="", help="ca证书")
    parse.add_argument("--cert_path", type=str, default="", help="客户端证书")
    parse.add_argument("--key_path", type=str, default="", help="客户端私钥")
    parse.add_argument("--pwd", type=str, default="", help="私钥解密口令")

    args = parse.parse_args()

    streaming_llm_callback_handler = StreamingLLMCallbackHandler()
    streaming_llm_callback_handler.clear()


    def get_llm_result(handler):
        for chunk in handler.stream_gen:
            logger.info(chunk)


    thread = threading.Thread(target=get_llm_result, args=(streaming_llm_callback_handler,))
    thread.start()

    llm_chain = create_llm_chain(base_url=args.base_url,
                                 model_name=args.model_name,
                                 handler=streaming_llm_callback_handler,
                                 ssl=args.ssl,
                                 ca_path=args.ca_path,
                                 cert_path=args.cert_path,
                                 key_path=args.key_path,
                                 pwd=args.pwd
                                 )
    llm_chain.invoke({"question": "介绍北京风景区"})
