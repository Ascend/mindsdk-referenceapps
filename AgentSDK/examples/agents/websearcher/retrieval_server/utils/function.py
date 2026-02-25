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

import datasets
from transformers import AutoTokenizer, AutoModel

def load_corpus(corpus_path: str):
    """Load dataset from JSON file.
    
    Args:
        corpus_path: Path to the JSON file containing the corpus
        
    Returns:
        datasets.Dataset: The loaded dataset object
    """
    corpus = datasets.load_dataset(
        'json', 
        data_files=corpus_path,
        split="train",
        num_proc=4
    )
    return corpus

def load_docs(corpus, doc_idxs):
    """Retrieve documents by indices from the corpus.
    
    Args:
        corpus: The loaded dataset corpus
        doc_idxs: List of document indices to retrieve
        
    Returns:
        list: List of retrieved documents
    """
    results = [corpus[int(idx)] for idx in doc_idxs]
    return results

def load_model(model_path: str, use_fp16: bool = False):
    """Load pre-trained model and tokenizer.
    
    Args:
        model_path: Path to the pre-trained model directory
        use_fp16: Whether to use half-precision (FP16) inference
        
    Returns:
        tuple: (model, tokenizer) where:
            - model: Loaded model instance on NPU
            - tokenizer: Corresponding tokenizer
    """
    model = AutoModel.from_pretrained(model_path, trust_remote_code=True)
    model.eval()
    model.npu()
    if use_fp16: 
        model = model.half()
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True, trust_remote_code=True)
    return model, tokenizer

def pooling(
    pooler_output,
    last_hidden_state,
    attention_mask = None,
    pooling_method = "mean"
):
    """Generate sentence embedding from token embeddings.
    
    Args:
        pooler_output: Model's pooler output
        last_hidden_state: Last layer hidden states
        attention_mask: Attention mask indicating valid tokens
        pooling_method: Pooling strategy, one of:
            - "mean": Mean pooling over valid tokens
            - "cls": Use [CLS] token representation
            - "pooler": Use model's pooler output
            
    Returns:
        torch.Tensor: Pooled sentence embeddings
    """    
    if pooling_method == "mean":
        last_hidden = last_hidden_state.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
    elif pooling_method == "cls":
        return last_hidden_state[:, 0]
    elif pooling_method == "pooler":
        return pooler_output
    else:
        raise NotImplementedError("Pooling method not implemented!")