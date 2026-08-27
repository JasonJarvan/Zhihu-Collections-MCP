# -*- coding:utf-8 -*-
from __future__ import annotations

from typing import Any


def build_page_headers() -> dict[str, str]:
    """构造知乎页面请求所需的 HTTP 头"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://www.zhihu.com/",
        "x-zse-93": "101_3_3.0",
        "x-zse-96": "2.0_3pMeV7de2ZCOYdR1sA1_MPH3NUYhNeCg9c2jOYKNOL3F2lnZg5HE02o0HSgWHX2aRdK5Oj8bSpSRRWM6IXefO0eQH2pD2LvjFFecfICcrswg8P0gMcPAqHrJ5kHeGYQBJQsr8q6NLTKcPHCqyGR9ov8kXFwGbe_LFNbqYpJTgYrKOLCuqA2ASU6pI-DNswzSqPcz8QdYnDkBMQf0KpLcJyftiBwOZzbfDNEFQAGAfCNWzIQzhNeRJdXqVFyGqqLoDo8w2eBp6ZsfgxHtEirXyBoWMV9FUSZHTY7msV7_VrK3e4ty5x0e7_LEu5",
        "sec-ch-ua": '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }


def build_api_headers() -> dict[str, str]:
    """构造知乎 API 请求所需的 HTTP 头"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.zhihu.com/",
        "x-requested-with": "fetch",
        "x-zse-93": "101_3_3.0",
        "x-zse-96": "2.0_3pMeV7de2ZCOYdR1sA1_MPH3NUYhNeCg9c2jOYKNOL3F2lnZg5HE02o0HSgWHX2aRdK5Oj8bSpSRRWM6IXefO0eQH2pD2LvjFFecfICcrswg8P0gMcPAqHrJ5kHeGYQBJQsr8q6NLTKcPHCqyGR9ov8kXFwGbe_LFNbqYpJTgYrKOLCuqA2ASU6pI-DNswzSqPcz8QdYnDkBMQf0KpLcJyftiBwOZzbfDNEFQAGAfCNWzIQzhNeRJdXqVFyGqqLoDo8w2eBp6ZsfgxHtEirXyBoWMV9FUSZHTY7msV7_VrK3e4ty5x0e7_LEu5",
        "sec-ch-ua": '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
