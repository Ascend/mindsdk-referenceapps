#!/bin/bash
set -ex

WIKI2018_WORK_DIR=/path

index_file=$WIKI2018_WORK_DIR/e5.index/e5_Flat.index
corpus_file=$WIKI2018_WORK_DIR/wiki_corpus.jsonl
retriever_name=e5
retriever_path=/path/to/e5-base-v2

python3  examples/agents/websearcher/retrieval_server/local_retrieval_server.py --index_path $index_file \
                                            --corpus_path $corpus_file \
                                            --topk 3 \
                                            --retriever_name $retriever_name \
                                            --retriever_model $retriever_path \
                                            --port $1 \
                                            --backend_count 8