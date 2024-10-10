# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
import json
import ast
import requests
import html2text
from paddle.base import libpaddle


LOG_PROMPT_FORMAT = '''
你是一名高级硬件测试工程师，下面会给你一份测试日志和一些历史问题。
测试日志中包含了该失败用例的相关日志信息，历史问题里每条记录由问题类型和问题描述组成。
请按照如下要求进行日志分析：
1、从测试日志中提取出断言失败之前的异常命令行；
2、提取导致上一条命令行失败的关键信息，关键信息往往是命令行之前的回显信息；
3、历史问题的记录由问题类型和问题描述组成，如果历史问题列表里存在与前面提取出来的关键信息相似的问题描述，请找出最相似的问题描述并且提取该条记录的问题类型；
4、如果历史问题列表里没有相似问题描述，则根据分析从环境问题、脚本问题、版本缺陷中选出一个问题类型，不要给出其他答案；
按json格式返回结果，其中包含以下json key：
    分析过程，问题类型
日志内容：
```{context}```
历史问题列表：
```{history_label}```
'''

GENERAL_PROMPT_FORMAT = "请基于给定的文章回答下述问题。\n\n##文章：{context}\n\n##请基于上述文章回答下面的问题。\n\n{question}\n##回答："


def run_unstructured_doc_qa(server_url, file_path, question, target_tokens, target_rate):
    with open(file_path, 'r', encoding='utf-8') as f:
        context = f.read()

    data = json.dumps(
        {
            'context': context,
            'question': question,
            'target_tokens': target_tokens,
            'target_rate': target_rate
        }
    )

    ret = requests.post(server_url, data)
    target_text = ast.literal_eval(ret.text)
    return target_text


def run_structured_doc_qa(server_url, file_path, question, topk):
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    data = json.dumps(
        {
            'context': raw_data,
            'question': question,
            'topk': topk
        }
    )

    ret = requests.post(server_url, data)
    target_text = ast.literal_eval(ret.text)
    return target_text


def run_log_analysis(server_url, file_path, question):
    data_list = []
    convertor = html2text.HTML2Text()
    with open(file_path, 'r') as f:
        for line in f:
            raw_data = json.loads(line)
            fail_log = raw_data['fail_log']
            major_type = raw_data['major_type']
            manual_description = raw_data['manual_description']
            content = convertor.handle(fail_log)
            data_list.append((content, major_type, manual_description))
            break

    data = json.dumps(
        {
            'context': data_list[0][0],
            'question': question
        }
    )

    ret = requests.post(server_url, data)
    lst = ast.literal_eval(ret.text)
    if len(lst) != 2:
        raise ValueError('The returned value does not meet the expectation.')
    target_text = lst[0]
    label_data = lst[1]
    return target_text, label_data


def run_summary(server_url, file_path, question, compress_rate, embedding_batch_size, min_cluster_size):
    with open(file_path, 'r') as f:
        context = f.read()

    data = json.dumps(
        {
            'context': context,
            'question': question,
            'compress_rate': compress_rate,
            'embedding_batch_size': embedding_batch_size,
            'min_cluster_size': min_cluster_size
        }
    )

    ret = requests.post(server_url, data)
    target_text = ast.literal_eval(ret.text)
    return target_text


if __name__ == '__main__':
    parse = argparse.ArgumentParser()

    parse.add_argument("--host", type=str, default="127.0.0.1")
    parse.add_argument("--port", type=int, default=8000)
    # scenes: doc_qa_unstructured, doc_qa_structured, log_analyse, doc_summary
    parse.add_argument("--scenes", type=str, default="doc_summary")

    parse.add_argument("--file_path", type=str, default="")
    parse.add_argument("--question", type=str, default="")

    parse.add_argument("--topk", type=int, default=5)

    parse.add_argument("--target_tokens", type=int, default=3000)
    parse.add_argument("--target_rate", type=float, default=0.5)

    parse.add_argument("--compress_rate", type=float, default=0.6)
    parse.add_argument("--embedding_batch_size", type=int, default=64)
    parse.add_argument("--min_cluster_size", type=int, default=2)

    args = parse.parse_args()

    url = f"http://{args.host}:{args.port}/{args.scenes}_compressor/"

    if args.scenes == 'doc_qa_unstructured':
        compressed_text = run_unstructured_doc_qa(url, args.file_path, args.question, args.target_tokens,
                                                  args.target_rate)
        prompt = GENERAL_PROMPT_FORMAT.format(context=compressed_text, question=args.question)
    elif args.scenes == 'doc_qa_structured':
        compressed_text = run_structured_doc_qa(url, args.file_path, args.question, args.topk)
        prompt = GENERAL_PROMPT_FORMAT.format(context=compressed_text, question=args.question)
    elif args.scenes == 'log_analyse':
        compressed_text, history_label = run_log_analysis(url, args.file_path, args.question)
        prompt = LOG_PROMPT_FORMAT.format(context=compressed_text, history_label=history_label)
    elif args.scenes == 'doc_summary':
        compressed_text = run_summary(url, args.file_path, args.question, args.compress_rate,
                                      args.embedding_batch_size, args.min_cluster_size)
        prompt = GENERAL_PROMPT_FORMAT.format(context=compressed_text, question=args.question)
    else:
        raise ValueError('Unrecognized scenes')

    print(f"文本压缩后的prompt为：{prompt}")
