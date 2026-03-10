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

import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import torch
from typing import Any, Dict, List, Optional, Literal, TypedDict, Annotated
import uuid

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, ToolMessage, AnyMessage
from langchain_core.messages.content import InvalidToolCall
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from rllm.parser.chat_template import ChatTemplateParser  # v0.1
from rllm.agents.agent import Trajectory, Action
from rllm.agents.utils import (
    convert_messages_to_tokens_and_masks,
    get_recent_assistant_user_messages,
)
from rllm.environments.env_utils import compute_mc_return
from agentic_rl import BaseEngineWrapper, Trajectory as AgenticRlTrajectory
from examples.agents.agents_mapping import get_agent_by_name
from examples.rllm.utils.utils import compute_trajectory_reward


logger = logging.getLogger(__name__)
MODEL = "Qwen2.5-7B-Instruct"
GREEN = "\033[92m"
RESET = "\033[0m"


class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    agent: Any
    env: Any
    observation: Any
    reward: float
    done: bool
    info: Any
    delta_time: float
    tool_calls: Any
    llm_time: float
    env_delta_time: float


def tools_condition(state: AgentState) -> Literal["tools", "agent", "__end__"]:
    """Determines the next execution path in LangGraph based on reward value.

    Args:
        state: Current graph state containing agent, environment, and execution data.

    Returns:
        str: Next node to execute - "tools", "agent", or "__end__".
    """
    if "reward" in state:
        if state["reward"] < 0:
            return "agent"
        else:
            return "tools"
    return "end"


class LangGraphEngineWrapper(BaseEngineWrapper):
    DEFAULT_MAX_PROMPT_LENGTH = 8192
    DEFAULT_MAX_RESPONSE_LENGTH = 16384
    DEFAULT_N_PARALLEL_AGENTS = 8
    DEFAULT_MAX_STEPS = 128
    DEFAULT_ENV_CREATION_WORKERS = 64
    DEFAULT_AGENT_CREATION_WORKERS = 64
    DEFAULT_MAX_WORKERS = 64

    def __init__(
        self,
        agent_name: str,
        tokenizer: Any,
        sampling_params: Optional[Dict[str, Any]] = None,
        max_prompt_length: int = DEFAULT_MAX_PROMPT_LENGTH,
        max_response_length: int = DEFAULT_MAX_RESPONSE_LENGTH,
        n_parallel_agents: int = DEFAULT_N_PARALLEL_AGENTS,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> None:
        """Initializes the LangGraphEngineWrapper.

        Args:
            agent_name: Name of the agent type to use.
            tokenizer: Tokenizer for processing messages.
            sampling_params: Parameters for model sampling.
            max_prompt_length: Maximum allowed prompt length in tokens.
            max_response_length: Maximum allowed response length in tokens.
            n_parallel_agents: Number of parallel agents to run.
            max_steps: Maximum number of steps per trajectory.
        """
        self.executor = ThreadPoolExecutor(max_workers=self.DEFAULT_MAX_WORKERS)
        super().__init__(
            agent_name,
            tokenizer,
            sampling_params,
            max_prompt_length,
            max_response_length,
            n_parallel_agents,
            max_steps,
        )

        agent_config = get_agent_by_name(agent_name)
        self.agent_class = agent_config.agent_class
        self.env_class = agent_config.env_class
        self.agent_args = agent_config.agent_args
        self.env_args = agent_config.env_args

        self.graphs = []
        self.agents = []
        self.envs = []

    def initialize(self):
        """Initializes the engine with timeout and chat parser settings."""
        self.trajectory_timeout = 1e9
        self.chat_parser = ChatTemplateParser.get_parser(
            self.tokenizer, disable_thinking=False
        )

    async def run_search_agent(self, idx: int, max_truns: int = 5):
        """Runs a single search agent to generate a trajectory for a given task.

        Args:
            idx: Index of the agent/environment pair to use.
            max_truns: Maximum number of graph execution runs.

        Returns:
            Dict: Token result containing trajectory data, tokens, masks, and metrics.
        """
        agent = self.agents[idx]
        env = self.envs[idx]
        termination_reason = None
        done = False
        response_token_len = 0
        response_tokens = []
        response_masks = []
        total_time = 0.0
        reward_time = None
        next_observation = None
        llm_time = 0.0
        env_time = 0.0
        reward = 0.0

        loop = asyncio.get_event_loop()
        observation, info = await loop.run_in_executor(self.executor, env.reset)
        info["max_steps"] = self.max_steps

        agent.reset()
        agent.update_from_env(
            observation=observation,
            reward=0.0,
            done=False,
            info=info,
        )

        messages = agent.chat_completions
        prompt_tokens, _ = convert_messages_to_tokens_and_masks(
            messages,
            tokenizer=self.tokenizer,
            parser=self.chat_parser,
            contains_first_msg=True,
            contains_generation_msg=True,
        )
        prompt_token_len = len(prompt_tokens)

        if prompt_token_len > self.max_prompt_length:
            agent.reset()
            raise Exception(
                f"Trajectory {idx}: initial prompt length {prompt_token_len} already exceeded max_prompt_length {self.max_prompt_length}, retrying"
            )

        async for step in self.graphs[idx].astream(
            {"messages": messages, "agent": agent, "env": env},
            {"recursion_limit": max_truns * 2 + 5},
        ):
            node_name, ctx = step.popitem()
            message = ctx["messages"][0]
            content = message.content
            step_done = True
            if node_name == "agent":
                llm_time += ctx["llm_time"]
                reward = ctx["reward"]
                if not ctx["done"] and reward >= 0:
                    step_done = False

            elif node_name == "tools":

                reward += ctx["reward"]

            env_time += ctx["env_delta_time"]
            total_time += ctx["llm_time"] + ctx["env_delta_time"]
            if not step_done:
                continue
            next_observation = ctx["observation"]
            reward = ctx["reward"]
            done = ctx["done"]
            info = ctx["info"]
            info["max_steps"] = self.max_steps
            info["cur_tokens"] = response_token_len
            agent.update_from_env(
                observation=next_observation,
                reward=reward,
                done=done,
                info=info,
            )
            cur_step = agent.get_current_state()
            cur_step.reward = reward
            cur_step.done = done
            cur_step.info.update(info)

            chat_completions_messages = agent.chat_completions
            assistant_message, env_messages = get_recent_assistant_user_messages(
                chat_completions_messages
            )

            assistant_msg_tokens, assistant_msg_masks = [], []
            env_msg_tokens, env_msg_masks = [], []

            if assistant_message:
                assistant_msg_tokens, assistant_msg_masks = (
                    convert_messages_to_tokens_and_masks(
                        [assistant_message],
                        tokenizer=self.tokenizer,
                        parser=self.chat_parser,
                        contains_first_msg=False,
                        contains_generation_msg=False,
                    )
                )

            if env_messages:
                env_msg_tokens, env_msg_masks = convert_messages_to_tokens_and_masks(
                    env_messages,
                    tokenizer=self.tokenizer,
                    parser=self.chat_parser,
                    contains_first_msg=False,
                    contains_generation_msg=True,
                )

            response_token_len += len(assistant_msg_tokens) + len(env_msg_tokens)

            if response_token_len >= self.max_response_length:
                truncation_length = self.max_response_length - response_token_len

                if truncation_length < 0:
                    truncated_response_tokens = (assistant_msg_tokens + env_msg_tokens)[
                        :truncation_length
                    ]
                    truncated_response_masks = (assistant_msg_masks + env_msg_masks)[
                        :truncation_length
                    ]
                else:
                    truncated_response_tokens = assistant_msg_tokens + env_msg_tokens
                    truncated_response_masks = assistant_msg_masks + env_msg_masks

                response_tokens.extend(truncated_response_tokens)
                response_masks.extend(truncated_response_masks)

                cur_step = agent.get_current_state()
                if response_token_len - len(env_msg_tokens) > self.max_response_length:
                    cur_step.reward = 0.0
                cur_step.done = True
                termination_reason = "TRUNCATION"
                break

            response_tokens.extend(assistant_msg_tokens)
            response_masks.extend(assistant_msg_masks)

            if total_time >= self.trajectory_timeout:
                termination_reason = "TIMEOUT"
                cur_step = agent.get_current_state()
                done = True
                cur_step.done = done
                break

            if done:
                termination_reason = "ENV_DONE"
                break

            response_tokens.extend(env_msg_tokens)
            response_masks.extend(env_msg_masks)

            if env.step_count == self.max_steps - 1:
                termination_reason = "MAX_STEPS"
                break

        trajectory: Trajectory = agent.trajectory
        compute_trajectory_reward(trajectory)
        compute_mc_return(trajectory, gamma=0.2)
        print(
            f"{GREEN}Trajectory {idx} completed due to: {termination_reason}. Reward is {trajectory.reward}. \n{RESET}"
        )
        token_result = {
            "prompt_tokens": torch.tensor(prompt_tokens, dtype=torch.long),
            "response_tokens": torch.tensor(response_tokens, dtype=torch.long),
            "response_masks": torch.tensor(response_masks, dtype=torch.long),
            "trajectory_reward": trajectory.reward,
            "idx": env.idx,
            "chat_completions": agent.chat_completions,
            "metrics": {
                "steps": len(trajectory.steps),
                "reward_time": reward_time,
                "env_time": env_time,
                "llm_time": llm_time,
                "total_time": total_time,
                "res_reward": trajectory.res_reward,
                "toolcall_reward": trajectory.toolcall_reward,
            },
        }

        return token_result

    def init_envs_and_agents(self, tasks: List[dict]):
        """Initializes environments, agents, and LangGraph workflows for all tasks.

        Args:
            tasks: List of task dictionaries to initialize.
        """
        task_num = len(tasks)
        logger.info(f"Initializing {task_num} environments and agents...")

        search_url = self.env_args.get("search_url", "")
        address_num = len(self.server_addresses)
        self.envs = [None] * task_num
        self.agents = [None] * task_num
        self.graphs = [None] * task_num
        for i, _ in enumerate(tasks):
            agent = self.agent_class(**self.agent_args)
            self.agents[i] = agent

            env_args_copy = self.env_args.copy()
            env_args_copy["task"] = tasks[i]
            env_args_copy["max_steps"] = self.max_steps
            env = self.env_class.from_dict(env_args_copy)
            env.idx = i
            self.envs[i] = env

            address = self.server_addresses[i % address_num]

            llm_model = init_chat_model(
                MODEL,
                model_provider="openai",
                base_url="http://" + address + "/v1",
                api_key="EMPTY",
            )

            retriever_tool = env.to_langchain_tool(
                server_url=search_url, tokenizer=self.tokenizer, max_tool_length=8192
            )

            def create_agent_step(llm_model):
                async def agent_step(state: AgentState) -> Dict[str, Any]:
                    agent = state["agent"]
                    env = state["env"]
                    prompt_messages = agent.chat_completions.copy()
                    start_time = time.time()
                    response = await llm_model.ainvoke(prompt_messages)
                    state["llm_time"] = time.time() - start_time
                    try:
                        tool_call = agent.tool_parser.parse(response.content)
                        tool_call_dict = (
                            {
                                "id": str(uuid.uuid4()),
                                "type": "tool_call",
                                "function": tool_call,
                            }
                            if tool_call
                            else None
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to parse tool calls from string response: {e}"
                        )
                        tool_call_dict = None

                    if tool_call_dict:
                        response = AIMessage(
                            content=response.content,
                            tool_calls=[
                                {
                                    "name": tool_call_dict["function"].name,
                                    "args": tool_call_dict["function"].arguments,
                                    "id": tool_call_dict["id"],
                                    "type": tool_call_dict["type"],
                                }
                            ],
                        )
                    action: Action = agent.update_from_model(response.content)
                    action = action.action
                    start_time = time.time()
                    (
                        state["observation"],
                        state["reward"],
                        state["done"],
                        state["info"],
                    ) = env.calculate_llm_reward(action)
                    state["env_delta_time"] = time.time() - start_time
                    state["messages"] = [response]
                    state["tool_calls"] = response.tool_calls
                    return state
                return agent_step

            def wrap_tool_node(tools):
                tool_node = ToolNode(tools)

                async def wrapped_node(state: Dict[str, Any]) -> Dict[str, Any]:
                    start_time = time.time()
                    result = await tool_node.ainvoke(state)
                    state.update(result)
                    env = state["env"]
                    (
                        state["observation"],
                        state["reward"],
                        state["done"],
                        state["info"],
                    ) = env.calculate_tool_reward(
                        state["messages"][0].content, state["tool_calls"]
                    )
                    state["env_delta_time"] = time.time() - start_time
                    return state

                return wrapped_node

            workflow = StateGraph(AgentState)
            workflow.add_node("agent", create_agent_step(llm_model))
            workflow.add_node("tools", wrap_tool_node([retriever_tool]))

            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges(
                "agent",
                tools_condition,
                {
                    "tools": "tools",
                    "agent": "agent",
                    "end": END,
                },
            )
            workflow.add_edge("tools", "agent")

            graph = workflow.compile()
            self.graphs[i] = graph

        logger.info(
            f"Successfully initialized {len(self.graphs)} agents of {task_num} tasks."
        )

    def generate_agent_trajectories_async(self, tasks: List[dict]):
        """Generates trajectories for multiple tasks asynchronously.

        Args:
            tasks: List of task dictionaries to process.

        Returns:
            List: Generated trajectories for all tasks.
        """
        self.init_envs_and_agents(tasks)
        result = asyncio.run(self._generate_agent_trajectories_async(tasks))
        return result

    async def _generate_agent_trajectories_async(self, tasks: List[dict]):
        """Internal method to generate trajectories asynchronously using asyncio.

        Args:
            tasks: List of task dictionaries to process.

        Returns:
            List: Generated trajectories.
        """
        trajectories = []

        async def launch_one_trajectory_task(env_idx: int):
            try:
                result = await self.run_search_agent(
                    env_idx, self.env_args.get("max_steps", 5)
                )
            except Exception as e:
                logger.error(f"Trajectory {env_idx} trajectory generation failed.")
                raise e
            return result

        tasks_to_run = [launch_one_trajectory_task(i) for i in range(len(self.envs))]

        tasks_completed = 0
        for future in asyncio.as_completed(tasks_to_run):
            try:
                result = await future
                tasks_completed += 1
                print(
                    f"{GREEN}Number of Trajectories {tasks_completed}/{len(self.envs)} completed"
                )
                trajectories.append(AgenticRlTrajectory(**result))
            except Exception as e:
                logger.error(
                    f"Trajectory generation failed. {tasks_completed} trajectories have been generated now."
                )
                raise e

        return trajectories
