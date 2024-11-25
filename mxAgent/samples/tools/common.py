import json
from samples.tools.web_summary_api import WebSummary

def get_website_summary(keys, prompt, llm):
    filtered = []
    for val in keys:
        if val is None or len(val) == 0:
            continue
        if '无' in val or '未' in val or '没' in val:
            continue
        filtered.append(val)
        if isinstance(val, list):
            it = flatten(val)
            filtered.append(it)
        filtered.append(val)

    if len(filtered) == 0:
        raise Exception("keywords has no been found")
                
    webs = WebSummary.web_summary(
        filtered, search_num=3, summary_num=3, summary_prompt=prompt, llm=llm)
    return json.dumps(webs, ensure_ascii=False)

def flatten(nested_list):
    """递归地扁平化列表"""
    for item in nested_list:
        if isinstance(item, list):
            return flatten(item)
        else:
            return item