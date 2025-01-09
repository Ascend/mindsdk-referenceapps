import warnings
import argparse

from loguru import logger
from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from agent_sdk.agentchain.tool_less_agent import ToollessAgent

warnings.filterwarnings('ignore')
MAX_CONTEXT_LEN = 4096


def test_toolless_agent():
    llm = get_llm_backend(BACKEND_OPENAI_COMPATIBLE, API_BASE, API_KEY, LLM_NAME).run
    agent = ToollessAgent(llm=llm, max_context_len=MAX_CONTEXT_LEN)
    response = agent.run("Can you help with a 5 day trip from Orlando to Paris? Departure date is April 10, 2022.", 
                     text="given information")
    logger.info(f"5 day trip from Orlando to Paris:{response.answer}")


def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("--model_name", type=str, default="Qwen1.5-32B-Chat", help="OpenAI客户端模型名")
    parse.add_argument("--base_url", type=str, default="http://10.44.115.108:1055/v1", help="OpenAI客户端模型地址")
    parse.add_argument("--api_key", type=str, default="EMPTY", help="OpenAI客户端api key")
    return parse.parse_args().__dict__


if __name__ == "__main__":
    args = get_args()
    API_BASE = args.pop("base_url")
    API_KEY = args.pop("api_key")
    LLM_NAME = args.pop("model_name")
    logger.info("toolless agent test begin")
    test_toolless_agent()
    logger.info("toolless agent test end")