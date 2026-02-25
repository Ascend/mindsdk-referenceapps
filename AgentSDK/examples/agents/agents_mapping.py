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

from examples.agents.agents_configuartion import MATH_AGENT_CONFIG, WEBSEARCHER_AGENT_CONFIG, AgentConfig

AGENTS_REGISTRY = {}


def get_agent_by_name(name: str):
    """
    Get an agent configuration by its name from the AGENTS_REGISTRY.

    Args:
        name (str): The name of the agent to retrieve.

    Returns:
        AgentConfig: The configuration of the requested agent.

    Raises:
        ValueError: If the agent_name is not found in the AGENTS_REGISTRY.
    """
    if name not in AGENTS_REGISTRY:
        raise ValueError(f"Agent {name} not found in AGENTS_REGISTRY")
    return AGENTS_REGISTRY[name]

def register_agent(agent_configs: list[AgentConfig]):
    """
    Register or update a list of agent configurations in the AGENTS_REGISTRY.

    For each AgentConfig in the list:
    - If the agent name already exists, it will be updated and a warning will be logged.
    - If the agent name does not exist, it will be registered.
    
    Args:
        agent_configs (list[AgentConfig]): A list of agent configurations to register.
    """
    required_attrs = ["name", "env_class", "env_args", "agent_class", "agent_args"]
    
    for agent_config in agent_configs:
        for attr in required_attrs:
            if not hasattr(agent_config, attr):
                raise ValueError(f"AgentConfig {agent_config.name} missing required attribute {attr}")
        
        if agent_config.name in AGENTS_REGISTRY:
            AGENTS_REGISTRY[agent_config.name] = agent_config
            print(f"Agent {agent_config.name} already exists in AGENTS_REGISTRY, will be updated")
        else:
            AGENTS_REGISTRY[agent_config.name] = agent_config
            print(f"Agent {agent_config.name} registered successfully")

register_agent([MATH_AGENT_CONFIG, WEBSEARCHER_AGENT_CONFIG])