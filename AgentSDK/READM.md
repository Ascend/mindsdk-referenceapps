# Agent SDK 基于工具调用的多模式LLM Agent框架
## 一、功能介绍
Agent SDK是一个基于LLMs的通用Agent框架，应用多种框架解决不同场景和复杂度的问题，并通过工具调用的方式允许LLMs与外部源进行交互来获取信息，使LLMs生成更加可靠和实际。Agent SDK通过构建DAG（Directed Acyclic Graph）的方式建立工具之间的依赖关系，通过并行执行的方式，提高多工具执行的效率，缩短Agent在复杂场景的执行时间。Agent SDK框架还在框架级别支持流式输出
提供一套Agent实现框架，让用户可以通过框架搭建自己的Agent应用
### 1.Router Agent
提供意图识别的能力，用户可预设意图的分类，通过Router Agent给出具体问题的分类结果，用于设别不同的问题场景。
使用示例：
```
cd AgentSDK
export PYTHONPATH=.
python samples/basic_demo/intent_router.py --model_name xxx --base_url xxx  --api_key xxxx
```
### 2.Recipe Agent
设置复杂问题执行的workflow，在解决具体问题时，将workflow翻译成有向无环图的的节点编排，通过并行的方式执行节点。
适用于有相对固定workflow的复杂问题场景。
1）通过自然语言描述复杂问题的workflow，
2）workflow中每一个步骤对应一次工具使用，并描述步骤间关系
3）recipe Agent将按照workflow的指导完成工具调用
4）使用模型总结工作流结果，解决复杂问题
Recipe Agent利用用户所提供的流程指导和工具，使用LLMs生成SOP，并构建DAG图描述Steps之间的依赖关系。agent识别那些可并行的step，通过并行执行提高agent的执行效率。
使用Recipe Agent，仅需要提供一段解决问题的SOP指导、用于提示最终答案生成的final prompt、解决问题可能使用的工具。
示例见[travelagent.py](.travel_agenttravelagent.py)运行方式如下：
```
cd AgentSDK
export PYTHONPATH=.
python samples/travel_agent_demo/travelagent.py --model_name xxx --base_url xxx  --api_key xxxx
```

### 3.ReAct Agent
使用Thought、Action、Action Input、Observation的循环流程，解决复杂问题：
1）ReAct通过大模型思考并给出下一步的工具调用，
2）执行工具调用，得到工具执行结果
3）将工具执行结果应用于下一次的模型思考
4）循环上述过程，直到模型认为问题得到解决
使用样例：
```
cd AgentSDK
export PYTHONPATH=.
python samples/basic_demo/test_react_agent.py --model_name xxx --base_url xxx  --api_key xxxx
```
样例执行过程的轨迹见目录`samples/basic_demo/trajs`下对应的文件
### 4.Single Action Agent

通过模型反思、调用工具执行，总结工具结果的执行轨迹，完成一次复杂问题的处理。Single Action Agent使用一次工具调用帮助完成复杂问题解决
使用示例：
```
cd AgentSDK
export PYTHONPATH=.
python samples/basic_demo/test_single_action_agent.py --model_name xxx --base_url xxx  --api_key xxxx
```
样例执行过程的轨迹见目录`samples/basic_demo/trajs`下对应的文件

### 5. Tooless Agent

未使用外部工具和知识库，通过prompt工程等技术指导大模型完成复杂问题规划，通过提供示例和指导等内容调优规划效果。
使用示例：
```
cd AgentSDK
export PYTHONPATH=.
python samples/basic_demo/test_toolless_agent.py --model_name xxx --base_url xxx  --api_key xxxx
```
## 

## 二、接口使用方法
### 1.模型使用
1.1. get_llm_backend

| 参数 | 含义 |
| ---- | ----- |
| backend | 推理模型后台类型，当前取值
| base_url | OpenAI客户端推理模型地址
| api_key |OpenAI客户端api key
| llm_name | 推理模型名称

1.2. run
| 参数 | 含义 | 取值
| ---- | ----- | ---|
| prompt |模型输入的prompt | 字符串或数组
| ismessage | 是否为对话信息是否为对话信息，默认值False | bool值

更多模型后处理参数可参考transformers文档

### 2.agent接口
2.1 初始化参数
| 参数| 含义 | 取值类型|
| ---- | -----| --- |
| llm  |模型客户端  |OpenAICompatibleLLM 
| prompt  |agent提示词  |字符串 
| tool_list | 工具列表 | 列表 
| max_steps | agent执行最大步数 | int 
| max_token_number | 模型生成最大token数 | int 
| max_context_len | 模型最大上下文token数 | int 
| max_retries | 最多重启次数 | int 
| example | agent推理生成示例 | 字符串 
| reflect_prompt | agent反思提示 | 字符串
| recipe | recipe agent参考的标准工作流 | 字符串
| intents | 分类的意图及含义 | dict 
| final_prompt | 最终生成总结的提示 | 字符串 




