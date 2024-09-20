# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import argparse
import json
import requests
import html2text

DOC_QA_UNSTRUCTURED_COMPRESSOR_URL = "https://127.0.0.1:8000/doc_qa_unstructured_compressor/"
DOC_QA_STRUCTURED_COMPRESSOR_URL = "https://127.0.0.1:8000/doc_qa_structured_compressor/"
LOG_ANALYSE_COMPRESSOR_URL = "https://127.0.0.1:8000/log_analyse_compressor/"
DOC_SUMMARY_COMPRESSOR_URL = "https://127.0.0.1:8000/doc_summary_compressor/"


def run_unstructured_doc_qa(file_path, question, target_token, target_rate):
    with open(file_path, 'r', encoding='utf-8') as f:
        context = f.read()

    data = json.dumps(
        {
            'context': context,
            'question': question,
            'target_token': target_token,
            'target_rate': target_rate
        }
    )

    ret = requests.post(DOC_QA_UNSTRUCTURED_COMPRESSOR_URL, data=data)
    return ret.text


def run_structured_doc_qa(file_path, question, topk):
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    data = json.dumps(
        {
            'context': raw_data,
            'question': question,
            'topk': topk
        }
    )

    ret = requests.post(DOC_QA_STRUCTURED_COMPRESSOR_URL, data=data)
    return ret.text


def run_log_analysis(file_path, question):
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

    data = json.dumps(
        {
            'context': data_list[0][0],
            'question': question
        }
    )

    ret = requests.post(LOG_ANALYSE_COMPRESSOR_URL, data=data)
    return ret.text


def run_summary(file_path, question, compress_rate, embedding_batch_size, min_cluster_size):
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

    ret = requests.post(DOC_SUMMARY_COMPRESSOR_URL, data=data)
    return ret.text


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # scenes: unstructured_doc_qa, structured_doc_qa, log_analysis, summary
    parser.add_argument('--scenes', type=str, default='summary')

    parser.add_argument('--file_patch', type=str, default='')
    parser.add_argument('--question', type=str, default='')

    parser.add_argument('--topk', type=int, default=5)

    parser.add_argument('--target_tokens', type=int, default=3000)
    parser.add_argument('--target_rate', type=float, default=0.5)

    parser.add_argument('--compress_rate', type=float, default=0.6)
    parser.add_argument('--embedding_batch_size', type=int, default=64)
    parser.add_argument('--min_cluster_size', type=int, default=2)

    args = parser.parse_args()

    if args.scenes == 'unstructured_doc_qa':
        compressed_text = run_unstructured_doc_qa(args.file_patch, args.question, args.target_tokens, args.target_rate)
    elif args.scenes == 'structured_doc_qa':
        compressed_text = run_structured_doc_qa(args.file_patch, args.question, args.topk)
    elif args.scenes == 'log_analysis':
        compressed_text = run_log_analysis(args.file_patch, args.question)
    elif args.scenes == 'summary':
        compressed_text = run_summary(args.file_patch, args.question, args.compress_rate, args.embedding_batch_size,
                                      args.min_cluster_size)
    else:
        raise ValueError('Unrecognized scenes')