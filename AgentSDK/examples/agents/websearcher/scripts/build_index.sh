#!/bin/bash

WIKI2018_WORK_DIR=/path
save_dir=$WIKI2018_WORK_DIR

corpus_file=$WIKI2018_WORK_DIR/wiki_corpus.jsonl
save_dir=${save_dir}/e5.index
retriever_name=e5
retriever_model=/path/to/e5-base-v2

ASCEND_RT_VISIBLE_DEVICES=0 python3 examples/agents/websearcher/retrieval_server/index_builder.py \
    --retrieval_method $retriever_name \
    --model_path $retriever_model \
    --corpus_path $corpus_file \
    --save_dir $save_dir \
    --use_fp16 \
    --max_length 256 \
    --batch_size 512 \
    --pooling_method mean \
    --faiss_type Flat \
    --save_embedding