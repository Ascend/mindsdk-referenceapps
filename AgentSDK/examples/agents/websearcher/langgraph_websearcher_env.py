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

import time
from typing import Any
import httpx
import time
from typing import Any, List

from rllm.rewards import RewardFunction

from examples.agents.websearcher.rewards.reward_config import WebSearcherRewardStage
from examples.agents.websearcher.websearcher_env import WebSearcherEnvironment
from agentic_rl.base.log.loggers import Loggers

logger = Loggers(__name__)


class LangGraphWebSearchEnv(WebSearcherEnvironment):
    """LangGraph-compatible web search environment.

    Extends WebSearcherEnvironment to provide LangGraph integration
    for web search functionality.
    """

    def __init__(
        self,
        task: dict | None = None,
        reward_fn: RewardFunction | None = None,
        **kwargs,
    ):
        """Initializes the LangGraph web search environment.

        Args:
            task: Task configuration dictionary.
            reward_fn: Reward function for evaluating agent performance.
            **kwargs: Additional keyword arguments for base class.
        """
        self.format_reward = -1.0  # Default reward for invalid format
        super().__init__(task, reward_fn, **kwargs)

    @staticmethod
    def from_dict(env_args: dict):
        """Creates an instance from a dictionary of arguments.

        Args:
            env_args: Dictionary containing environment configuration.

        Returns:
            A new LangGraphWebSearchEnv instance.
        """
        return LangGraphWebSearchEnv(**env_args)

    @staticmethod
    def to_langchain_tool(
        server_url: str = "http://127.0.0.1:8000",
        max_retries: int = 5,
        timeout: float = 300.0,
        tokenizer: Any = None,
        max_tool_length: int = 8192,
    ):
        """
        Create a LangChain StructuredTool for retrieval server.

        Args:
            server_url: URL of the dense retrieval server (default: http://127.0.0.1:8000)
            max_retries: Maximum number of retry attempts.
            delay: Delay between retries in seconds.
            timeout: Request timeout in seconds (default: 30.0)
            name: Name of langchain tool

        Returns:
            A LangChain StructuredTool instance that can be used with LangGraph agents

        """
        try:
            from langchain_core.tools import StructuredTool
        except ImportError:
            raise ImportError(
                "langchain_core is required to use to_langchain_tool(). Install it with: pip install langchain-core"
            ) from None

        # Create HTTP client for the retrieval server
        client = httpx.Client(timeout=timeout)
        server_url = server_url.rstrip("/")

        def _retrieve_from_server(query: List[str]) -> str:
            def _retry_request():
                response = None
                for attempt in range(max_retries):
                    try:
                        payload = {"queries": query, "topk": 3, "return_scores": True}
                        response = client.post(f"{server_url}/retrieve", json=payload)

                        response = response.json()
                        if response:
                            break

                        logger.warning(f"Empty response from {server_url}, retrying...")

                    except httpx.TimeoutException:
                        logger.error(
                            f"Error: Request timeout after {timeout} seconds. Please check if the retrieval server is running."
                        )
                    except httpx.ConnectError:
                        logger.error(
                            f"Error: Could not connect to retrieval server at {server_url}. Please ensure the server is running."
                        )
                    except httpx.RequestError as e:
                        logger.error(
                            f"Error: Request is not correct: {str(e)}. Please check the the request for the server"
                        )
                    except Exception as e:
                        logger.error(f"Error: Unexpected error - {str(e)}")

                    if attempt == max_retries - 1:
                        raise Exception(f"Failed after {max_retries} attempts")

                    time.sleep(1)
                return response
                
            def _local_search():
                try:
                    response = _retry_request()
                    content = LangGraphWebSearchEnv._format_results(
                        query, response["result"]
                    )
                    return {"tool_output": content, "query": query}
                except Exception as e:
                    logger.error(f"Local search failed: {e}", exc_info=True)
                    return {
                        "tool_output": "",
                        "query": query,
                        "error_output": f"ERROR: Local search failed: {str(e)}",
                    }

            try:
                output_dict = _local_search()
                output_str = LangGraphWebSearchEnv._format_tool_result(
                    tokenizer, max_tool_length, output_dict
                )
                return output_str
            except Exception as e:
                return f"execute search tool failed: {e}"

        # Convert to LangChain StructuredTool
        langchain_tool = StructuredTool.from_function(
            func=_retrieve_from_server,
            name="search",
            description="Search for information using a dense retrieval server with Wikipedia corpus",
        )

        return langchain_tool

    @staticmethod
    def _format_tool_result(tokenizer, max_tool_length, tool_output_dict):
        """Format tool output dictionary to string with token length control.

        Args:
            tokenizer: Tokenizer for encoding/decoding text.
            max_tool_length: Maximum token length for the formatted result.
            tool_output_dict: Input dictionary containing tool output data.

        Returns:
            Formatted string (truncated if exceeds max_tool_length).
        """
        filtered_dict = {
            k: v
            for k, v in tool_output_dict.items()
            if k not in {"tool_name", "url", "query"}
        }
        res_str = "\n".join(str(v) for v in filtered_dict.values())

        encoded = tokenizer.encode(res_str)
        if len(encoded) > max_tool_length:
            res_str = tokenizer.decode(encoded[:max_tool_length])

        return res_str
    
    @staticmethod
    def _format_results(queries, results):
        """Formats search results into a human-readable string.

        Args:
            queries: The original search queries.
            results: The search results from the vector database.

        Returns:
            A formatted string containing all search results.
        """

        def _passages2string(retrieval_result):
            format_reference = ""
            for idx, doc_item in enumerate(retrieval_result):
                try:
                    content_lines = doc_item["document"]["contents"].split("\n")
                    title = content_lines[0]
                    url = doc_item["document"]["url"]
                    text = "\n".join(content_lines[1:])
                    format_reference += (
                        f"[Doc {idx + 1}](Title: {title})(url: {url}):\n{text}\n"
                    )
                except (KeyError, IndexError) as e:
                    logger.warning(f"Invalid document format: {e}")
            return format_reference

        content = ""
        for query, res in zip(queries, results):
            content += (
                f"A search for '{query}' found {len(res)} results:\n\n## Web Results\n"
                + _passages2string(res)
                + "\n"
            )
        return content
    
    def calculate_llm_reward(self, action: dict):
        """Calculates reward for LLM action based on format and stage.

        Args:
            action: Agent action dictionary containing function call information.

        Returns:
            tuple: (next_observation, reward, done, info)
        """
        if not action or not isinstance(action, dict):
            raise TypeError("action must be a non-empty dictionary.")

        self.step_count += 1
        tool_call_name = action.get("function").get("name", "")
        finished = tool_call_name == "finish"

        done = self.step_count >= self.max_steps or finished
        if done:
            # Final step reward calculation
            llm_response = action.get("function").get("arguments").get("response", "")
            reward, metadata = self._calculate_reward(
                llm_response, WebSearcherRewardStage.DONE
            )
            return {}, reward, done, self._build_info(action, metadata)

        self.format_reward, format_metadata = self._calculate_reward(
            action, WebSearcherRewardStage.TOOLS_FORMAT
        )
        if self.format_reward < 0:
            # Invalid format - return error observation
            next_obs = {"tool_output": {action["id"]: format_metadata["reward_obs"]}}
            return (
                next_obs,
                self.format_reward,
                done,
                self._build_info(action, format_metadata),
            )
        return {}, self.format_reward, done, self._build_info(action, format_metadata)

    def calculate_tool_reward(self, content: str, tool_calls: list[dict[Any, Any]]):
        """Calculates reward for tool execution results.

        Args:
            content: Tool execution content.
            tool_calls: List of tool call dictionaries.

        Returns:
            tuple: (next_observation, reward, done, info)
        """
        tool_outputs = self._execute_format_tool_output(content, tool_calls)
        next_obs = {"tool_outputs": tool_outputs}

        exec_reward, exec_meta = self._calculate_reward(
            next_obs, WebSearcherRewardStage.TOOLS_RETURN
        )

        return (
            next_obs,
            self.format_reward + exec_reward,
            False,
            self._build_info(tool_calls, exec_meta),
        )

    def _execute_format_tool_output(
        self, content: str, tool_calls: list[dict[Any, Any]]
    ):
        """Executes tool calls in parallel and formats their outputs.

        Args:
            content: Tool execution content to be processed.
            tool_calls: List of tool call dictionaries to execute.

        Returns:
            dict: Mapping of tool call IDs to formatted outputs.
        """

        tool_outputs: dict[str, str] = {}
        for _, tool_call in enumerate(tool_calls):
            tool_name = tool_call["name"]
            obs = {"tool_result": content, "tool_name": tool_name}
            output_str = self._format_tool_output(obs)
            tool_outputs[tool_call["id"]] = output_str

        return tool_outputs
