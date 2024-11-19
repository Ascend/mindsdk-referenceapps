# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

from datetime import date
from langchain.prompts import PromptTemplate


react_agent_instruction = ("""
"You are a world expert at making travel plans with a set of carefully crafted tools. You will be given a task and 
solve it as best you can. To do so, you have been given access to a list of tools: \n{tools}\nTo solve the task, 
you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Action:', 'Action Input:', \
and 'Observation:' sequences. At each step, in the 'Thought:' sequence, you should first explain your reasoning \
towards solving the task and the tools that you want to use. 
Then in the 'Action:' sequence, you should write the tool name. in the 'Action Input:' sequence, you should \
write the tool parameters. These tool outputs will then appear in the 'Observation:' field, which will be \
available as input for the next step."""
+ f"Please be aware that the current date is: {date.today().strftime('%Y-%m-%d')}.\n\n"
+ """
Here are the rules you must follow to solve your task:\n
1. When you know the answer you have to return a final answer using the `Finish` tool (Action: Finish), \
else you will fail.\n
2. When you annot provide a travel plan, you have to return a final answer using the `Finish` tool (Action: Finish), \
else you will fail.\n
3. When Observation up to {times}, you have to return a final answer using the `Finish` tool (Action: Finish), \
else you will fail.\n
4. Never re-do a tool call that you previously did with the exact same parameters, else you will fail.\n
5. Use the plain text format for output. Do not use markdown, else you will fail.\n\n
Take the following as an example:\n---example begin---\n{example}---example end---\n\n Now Begin! 
If you solve the task correctly, you will receive a reward of $1,000,000.\n\n'Task: {query}\n\nThought: {scratchpad}"
""")

REFLECTION_HEADER = 'You have attempted to give a sub plan before and failed. The following reflection(s) give a "\
suggestion to avoid failing to answer the query in the same way you did previously. Use them to improve your "\
strategy of correctly planning.\n'

REFLECT_INSTRUCTION = """You are an advanced reasoning agent that can improve based on self refection. You will be "\
given a previous reasoning trial in which you were given access to an automatic cost calculation environment, "\
a travel query to give plan and relevant information. Only the selection whose name and city match the "\
given information will be calculated correctly. You were unsuccessful in creating a plan because you "\
used up your set number of reasoning steps. In a few sentences, Diagnose a possible reason for "\
failure and devise a new, concise, high level plan that aims to mitigate the same failure. "\
Use complete sentences.  

Given information: {text}

Previous trial:
Query: {query}{scratchpad}

Reflection:"""



SINGLE_AGENT_ACTION_INSTRUCTION = """I want you to be a good question assistant, handel the following tasks as best"\
you can. You have access to the following tools:

{tools}

Use the following format:

Thought: you should always think about what to do
Action: the action to take, should be one of {tools_name}
Action Input: the input to the action.
Observation: the result of the action.

Begin!

Question: {query}
{scratchpad}"""


FINAL_PROMPT = """Please refine a clear and targeted answer based on the user's query and
 the existing answer. \
 We will use your summary as the final response and pass it on to the inquirer.

The requirements are as follows:
1. Understand the user's query.
2. Combine the query and answer information to summarize an accurate and concise answer.
3. Ensure that the answer aligns with the user's query intent and strive to provide valuable information.

Begin!

question: {query}
answer: {answer}
summarize: 
"""

REACT_REFLECT_PLANNER_INSTRUCTION = ("""
"You are a world expert at making travel plans with a set of carefully crafted tools. You will be given a task and 
solve it as best you can. To do so, you have been given access to a list of tools: \n{tools}\nTo solve the task, 
you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Action:', 'Action Input:', \
and 'Observation:' sequences. At each step, in the 'Thought:' sequence, you should first explain your reasoning \
towards solving the task and the tools that you want to use. 
Then in the 'Action:' sequence, you should write the tool name. in the 'Action Input:' sequence, you should \
write the tool parameters. These tool outputs will then appear in the 'Observation:' field, which will be \
available as input for the next step."""
+ f"Please be aware that the current date is: {date.today().strftime('%Y-%m-%d')}.\n\n"
+ """
Here are the rules you must follow to solve your task:\n
1. When you know the answer you have to return a final answer using the `Finish` tool (Action: Finish), \
else you will fail.\n
2. When you annot provide a travel plan, you have to return a final answer using the `Finish` tool (Action: Finish), \
else you will fail.\n
3. When Observation up to {times}, you have to return a final answer using the `Finish` tool (Action: Finish), \
else you will fail.\n
4. Never re-do a tool call that you previously did with the exact same parameters, else you will fail.\n
5. Use the plain text format for output. Do not use markdown, else you will fail.\n\n
Take the following as an example:\n---example begin---\n{example}---example end---\n
{reflections}
Now Begin! 
If you solve the task correctly, you will receive a reward of $1,000,000.\n\n'Task: {query}\n\nThought: {scratchpad}"
""")

PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a '\
detailed plan, Note that all the information in your plan should be derived from the provided data. '\
You must adhere to the format given in the example. Additionally, all details should align with '\
commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided '\
sample, you do not need to plan after returning to the departure city. When you travel to '\
two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to '\
    March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}
Plan:"""

REACT_PLANNER_INSTRUCTION = react_agent_instruction


planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query"],
    template=PLANNER_INSTRUCTION,
)

react_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "scratchpad"],
    template=REACT_PLANNER_INSTRUCTION,
)

reflect_prompt_value = PromptTemplate(
    input_variables=["text", "query", "scratchpad"],
    template=REFLECT_INSTRUCTION,
)

react_reflect_planner_agent_prompt = PromptTemplate(
    input_variables=["tools", "times", "example", "reflections", "query", "scratchpad"],
    template=REACT_REFLECT_PLANNER_INSTRUCTION,
)
single_action_agent_prompt = PromptTemplate(
    input_variables=["tools", "tools_name", "query", "scratchpad"],
    template=SINGLE_AGENT_ACTION_INSTRUCTION,
)

final_prompt = PromptTemplate(
    input_variables=["query", "answer"],
    template=FINAL_PROMPT,
)

travel_agent_prompt = PromptTemplate(
    input_variables=["tools", "times", "example", "query", "scratchpad"],
    template=react_agent_instruction,
)