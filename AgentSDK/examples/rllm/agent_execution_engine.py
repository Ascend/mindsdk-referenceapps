"""
Copyright 2025 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Agent execution engine for OpenAIRouter-compatible API interations.

This module provides routing and execution capabilities for agents-based 
reinforcement learning with OpenAI-compatible model servers.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any, Dict, List, Optional, Union, Callable

from rllm.engine import AgentExecutionEngine as _AgentExecutionEngine
from rllm.parser.chat_template import ChatTemplateParser
from rllm.router.router import Router

logger = logging.getLogger(__name__)


class OpenAIRouter(Router):
    """
    Router for OpenAI-compatible API interactions with load balancing.

    Handled address allocation, usage tracking, and API communication with
    proper resource management and error handling.
    """
    # Defalt parameters
    DEFAULT_SAMPLING_PARAMS = {"n": 1}
    DEFAULT_MAX_RETRY_ATTEMPTS = 3
    DEFAULT_RETRY_DELAY = 1

    def __init__(
        self,
        completions: List[Callable]
    ) -> None:
        """
        Initialize the OpenAIRouter.

        Args:
            completions (List[Callable]): A list of functions, each of which is used to call a remote LLM interface.

        Raises:
            ValueError: If no completion functions are provided.
        """
        if not completions:
            raise ValueError("At least one completion function must be provided.")
        
        if not all(callable(comp) for comp in completions):
            raise ValueError("All completion functions must be callable.")
        
        self.completions = completions
        self._lock = asyncio.Lock()
        # Track usage count for each completion function
        self._usage: Dict[Callable, int] = {comp: 0 for comp in self.completions}
        # Map application IDs to completion functions
        self._application_id_to_address: Dict[str, Callable] = {}

    @classmethod
    async def _chat(cls, completion: Callable, **completions_request):
        # Remove meta_info if present
        if "meta_info" in completions_request:
            completions_request.pop("meta_info")
        # Remove extra_headers from the payload if present
        if "extra_headers" in completions_request:
            completions_request.pop("extra_headers")

        max_retries = cls.DEFAULT_MAX_RETRY_ATTEMPTS        # Maximum number of retries
        retry_delay = cls.DEFAULT_RETRY_DELAY               # Initial delay between retries in seconds

        for retry in range(max_retries):
            try:
                # Call the completion function
                response = completion(completions_request)
                return response
            except Exception as e:
                import traceback
                traceback.print_exc()
                # If this was the last retry, raise the exception
                if retry == max_retries - 1:
                    raise e
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    async def chat(
        self,
        prompt: str,
        application_id: str,
        default_sampling: dict,
        **kwargs
    ) -> Any:
        """
        Perform chat completion using the least used completion function.

        Args:
            prompt (str): The input prompt for the chat completion.
            application_id (str): The unique identifier for the application.
            default_sampling (dict): Default sampling parameters for the completion.
            **kwargs: Additional keyword arguments for the completion function.

        Raises:
            RuntimeError: If no completion functions are available.
        """
        default_kwargs = OpenAIRouter.DEFAULT_SAMPLING_PARAMS
        merged_kwargs = {**default_kwargs, **default_sampling, **kwargs}

        # Select the least used completion function
        completion = await self.get_address(application_id)
        try:
            response = await self._chat(completion, prompt=prompt, **merged_kwargs)
            return self._extract_response_text(response)
        except Exception as e:
            logger.error(f"Error during chat completion for application {application_id}: {e}")
            raise RuntimeError(f"Chat completion failed for application {application_id}") from e
        finally:
            await self.release_address(completion, application_id)

    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        Extract the text from the completion response.

        Args:
            response (Dict[str, Any]): The response from the completion function.
        
        Returns:
            str: The extracted text from the response.
        
        Raises:
            ValueError: If the response format is invalid.
        """
        try:
            choices = response.get("choices", [])
            if not choices:
                raise ValueError("No choices found in the response.")
            
            choice = choices[0]
            text = choice.get("text", "")
            if not isinstance(text, str):
                raise ValueError("Invalid text format in the response.")
            return text
        except Exception as e:
            raise e
        
        
class AgentExecutionEngine(_AgentExecutionEngine):
    """
    Agent Execution Engine for reinforcement learning with OpenAI-compatible APIs.

    Extends the base AgentExecutionEngine to utilize the OpenAIRouter for
    managing API calls and routing.
    """
    # Default configuration values
    DEFAULT_TRAJECTORY_TIMEOUT = int(1e9)
    DEFAULT_MAX_WORKERS = 64
    DEFAULT_GAMMA = 0.2
    DEFAULT_API_RETRIES = 3
    DEFAULT_RETRY_LIMIT = 3
    DEFAULT_MAX_STEPS = 5
    DEFAULT_MAX_RESPONSE_LENGTH = 8192
    DEFAULT_MAX_PROMPT_LENGTH = 1024

    def __init__(
        self,
        tokenizer: Any,
        router: Optional[OpenAIRouter] = None,
        chat_parser: Optional[ChatTemplateParser] = None,
        n_parallel_agents: int = 1,
        trajectory_timeout: int = DEFAULT_TRAJECTORY_TIMEOUT,
        gamma: float | int = DEFAULT_GAMMA,
        retry_limit: int = DEFAULT_RETRY_LIMIT,
        max_steps: int = DEFAULT_MAX_STEPS,
        max_response_length: int = DEFAULT_MAX_RESPONSE_LENGTH,
        max_prompt_length: int = DEFAULT_MAX_PROMPT_LENGTH,
        max_workers: int = DEFAULT_MAX_WORKERS,
        enforce_max_prompt_length: bool = False,
        overlong_filter: bool = False,
        **kwargs
    ) -> None:
        """
        Initialize the AgentExecutionEngine.

        Args:
            tokenizer (Any): The tokenizer for processing text.
            router (Optional[OpenAIRouter]): The router for managing API calls.
            chat_parser (Optional[ChatTemplateParser]): The parser for chat templates.
            n_parallel_agents (int): Number of parallel agents to run.
            trajectory_timeout (int): Timeout for trajectory execution.
            gamma (float | int): Discount factor for rewards.
            retry_limit (int): Maximum number of retries for API calls.
            max_steps (int): Maximum steps per trajectory.
            max_response_length (int): Maximum length of the response.
            max_prompt_length (int): Maximum length of the prompt.
            max_workers (int): Maximum number of worker threads for environment operations.
            enforce_max_prompt_length (bool): Whether to enforce max prompt length.
            overlong_filter (bool): Whether to filter overlong trajectories.
            **kwargs: Additional keyword arguments.

        Raises:
            ValueError / TypeError: if validation of any argument fails.
        """
        # Initialize cor attibutes
        self.tokenizer = tokenizer
        self.engine_name = "openai"
        self.n_parallel_agents = n_parallel_agents
        self.overlong_filter = overlong_filter

        # Interaction parameters
        self.gamma = gamma
        self.retry_limit = retry_limit
        self.max_steps = max_steps
        self.max_response_length = max_response_length
        self.max_prompt_length = max_prompt_length
        self.enforce_max_prompt_length = enforce_max_prompt_length

        # Initialize agent and environment lists
        self.agents = [None] * n_parallel_agents
        self.envs = [None] * n_parallel_agents

        # Initialize trajectory timeout
        self.trajectory_timeout = trajectory_timeout

        # Router configuration
        self.router = router
        if self.router is None:
            logger.warning("No router provided. Some functionalities may be limited.")
        else:
            if not isinstance(self.router, OpenAIRouter):
                raise TypeError("router must be an instance of OpenAIRouter.")
            
        self.sampling_params = kwargs.get("sampling_params", {})

        # Thread pool for environment operations
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, 
            thread_name_prefix="agent-env-worker"
            )

        # Chat parser configuration
        if chat_parser is None:
            disable_thinking = kwargs.get("disable_thinking", False)
            self.chat_parser = ChatTemplateParser.get_parser(
                self.tokenizer, disable_thinking=disable_thinking
            )
        else:
            self.chat_parser = chat_parser

        self._validate_initialization_params()
        
    async def get_model_response(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        application_id: str,
        **kwargs
    ) -> str:
        """
        Get model response using the router based on the given prompt.

        Args:
            prompt (str): The input prompt for the model.
            application_id (str): The unique identifier for the application.
            **kwargs: Additional keyword arguments for the model call.

        Returns:
            str: The model's response text.

        Raises:
            ValueError: If the prompt is invalid.
            RuntimeError: If the router is not configured.
        """
        if self.router is None:
            raise RuntimeError("Router is not configured for AgentExecutionEngine.")
        
        if isinstance(prompt, list):
            if not all(isinstance(msg, dict) for msg in prompt):
                raise ValueError("All messages in the prompt list must be dictionaries.")
            prompt_text = self.chat_parser.parse(
                prompt, add_generation_prompt=True, is_first_msg=True
            )
        elif isinstance(prompt, str):
            prompt_text = prompt
        else:
            raise ValueError("Prompt must be either a string or a list of message dictionaries.")
        
        response = await self.router.chat(
            prompt=prompt_text,
            application_id=application_id,
            default_sampling=self.sampling_params,
            **kwargs
        )
        return response
    
    def _validate_initialization_params(self) -> None:
        """
        Validate the initialization parameters of the engine.

        """
        AgentExecutionEngine._validate_obj_params("router", self.router, OpenAIRouter)
        AgentExecutionEngine._validate_obj_params("chat_parser", self.chat_parser, ChatTemplateParser)
        AgentExecutionEngine._validate_obj_params("enforce_max_prompt_length", self.enforce_max_prompt_length, bool, expected_bool=True)
        AgentExecutionEngine._validate_obj_params("overlong_filter", self.overlong_filter, bool, expected_bool=True)
        AgentExecutionEngine._validate_numeric_params("max_workers", self.max_workers, int, min_value=1)
        AgentExecutionEngine._validate_numeric_params("gamma", self.gamma, (float, int), min_value=0, max_value=1)
        AgentExecutionEngine._validate_numeric_params("retry_limit", self.retry_limit, int, min_value=0)

        if not isinstance(self.trajectory_timeout, int):
            raise TypeError("trajectory_timeout must be an integer.")
        if self.trajectory_timeout <= 0:
            raise ValueError("trajectory_timeout must be a positive integer.")
    
    @staticmethod
    def _validate_obj_params(param_name, param_value, expected_type, expected_bool=False):
        if not expected_bool:
            if param_value is not None and not isinstance(param_value, expected_type):
                raise TypeError(f"{param_name} must be of type {expected_type.__name__} if not None")
        else:
            if not isinstance(param_value, expected_type):
                raise TypeError(f"{param_name} must be a boolean value")
            
    @staticmethod
    def _validate_numeric_params(param_name, param_value, expected_type, min_value=None, max_value=None):
        if not isinstance(param_value, expected_type):
            raise TypeError(f"{param_name} must be of type {expected_type}")
        if min_value is not None and param_value < min_value:
            raise ValueError(f"{param_name} must be at least {min_value}")
        if max_value is not None and param_value > max_value:
            raise ValueError(f"{param_name} must be at most {max_value}")
        
    def __del__(self):
        """Clean up resources on deletion."""
        if hasattr(self, 'executor') and self.executor:
            self.executor.shutdown(wait=False)