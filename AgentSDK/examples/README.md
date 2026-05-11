# AgentSDK example

[AgentSDK](https://gitcode.com/Ascend/AgentSDK) 提供分层解耦昇腾亲和的企业级智能体Agentic RL训推框架，帮助用户快速训练AI智能体。
这里提供agent实现参考用例和不同agent执行引擎的实现参考用例，便于快速接入agent。

## 主要目录结构与说明
| 目录                      | 说明                 |
|-------------------------|--------------------|
| [agents](./agents)   | 提供Agent实现参考样例，包括 math agent 和 websearcher agent|
| [langgraph](./langgraph) | 提供agent引擎langgraph的参考样例，实现 LangGraph 与 AgentSDK 对接 |
| [meta-are](./meta-are)    | 提供agent引擎Meta ARE的参考样例，实现 Meta ARE 与 AgentSDK 对接 |
| [rllm](./rllm)    | 提供agent引擎rllm的参考样例，实现 rLLM 与 AgentSDK 对接 |

### agents 目录
提供 Agent 实现参考样例，包含以下子目录：

| 子目录 | 说明 |
|-------|------|
| [math_agent](./agents/math_agent) | 数学推理智能体，基于 rLLM ToolAgent 实现，用于数学领域的问题求解 |
| [websearcher](./agents/websearcher) | 网络搜索智能体，支持多轮搜索、上下文压缩和本地RAG检索服务 |

### langgraph 目录
提供 [LangGraph](https://langchain-ai.github.io/langgraph/) 流程编排工具与 AgentSDK 对接的参考样例。通过 `LangGraphEngineWrapper` 类实现 BaseEngineWrapper 抽象接口，展示如何将 LangGraph 构建的 Agent 接入 AgentSDK 的训练流程。

### meta-are 目录
提供 [Meta ARE](https://github.com/facebookresearch/meta-agents-research-environments)与 AgentSDK 对接的参考样例。展示在 websearcher 场景下，使用 GAIA2 数据集（search 子集）上的 GRPO 训练示例。

### rllm 目录
提供 [rLLM](https://github.com/rllm-org/rllm) 与 AgentSDK 对接的参考样例。通过 `RllmEngineWrapper` 类实现 BaseEngineWrapper 抽象接口，支持两种运行模式：
- **Token 模式**：一次性生成完整轨迹,计算整个轨迹的advantage
- **Step 模式**：逐步生成轨迹数据，计算每个step的step-wise advantage
