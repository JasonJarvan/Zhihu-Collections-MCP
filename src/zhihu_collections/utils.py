import re

def filter_title_str(str):
    filterStr = re.sub(r"[\/\\\"<>\|]",' ',str)
    filterStr = re.sub(r"\?", '？', filterStr)
    filterStr = re.sub(":", '：', filterStr)
    return filterStr

