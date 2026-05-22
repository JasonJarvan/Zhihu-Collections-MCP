# -*- coding:utf-8 -*-
"""文件名清理工具"""
import re


def filter_title_str(raw: str) -> str:
    """清理字符串中的非法文件名字符

    替换规则：
    - \\ / \" < > | → 空格
    - ? → ？
    - : → ：

    :param raw: 原始标题字符串
    :return: 清理后的安全文件名
    """
    filtered = re.sub(r"[\/\\\"<>\|]", " ", raw)
    filtered = re.sub(r"\?", "？", filtered)
    filtered = re.sub(":", "：", filtered)
    return filtered
