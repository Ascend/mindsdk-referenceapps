
def filter_website_keywords(keys):
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

    if len(filtered) == 0:
        raise Exception("keywords has no been found")
    return  filtered


def flatten(nested_list):
    """递归地扁平化列表"""
    for item in nested_list:
        if isinstance(item, list):
            return flatten(item)
        else:
            return item