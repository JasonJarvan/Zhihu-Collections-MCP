# -*- coding:utf-8 -*-
"""
知乎收藏夹管理 — 收藏/取消收藏/移动操作

独立模块，通过 cookies.json 读取认证信息，所有 HTTP 请求自包含。

API 端点（浏览器抓包确定）：
  - 收藏(默认夹): POST   /api/v4/collections/contents/{type}/{id}
  - 收藏(指定夹): POST   /api/v4/collections/{collection_id}/contents
  - 取消收藏:     DELETE /api/v4/collections/contents/{type}/{id}

延迟策略：
  - 单次收藏/取消后: random.uniform(1.0, 3.0)
  - 移动步骤间:     random.randint(1, 5)
"""

import json
import logging
import random
import re
import time

import requests

from zhihu_collections._common import load_cookies as _load_cookies_raw


# ──────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────


def _op_delay(min_sec=1.0, max_sec=3.0):
    """基础操作后延迟，避免请求过快触发频率限制"""
    time.sleep(random.uniform(min_sec, max_sec))


def _move_step_delay(min_sec=1, max_sec=5):
    """移动操作步骤间延迟"""
    time.sleep(random.randint(min_sec, max_sec))


def get_cookies():
    """读取 cookies.json 并返回字典格式的 cookies"""
    return _load_cookies_raw()


def _build_auth_headers():
    """构造带 xsrf token 的通用请求头"""
    cookies = get_cookies()
    xsrf_token = cookies.get("_xsrf", "")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.zhihu.com/",
        "x-requested-with": "fetch",
        "x-zse-93": "101_3_3.0",
        "Content-Type": "application/json",
    }
    if xsrf_token:
        headers["X-Xsrftoken"] = xsrf_token
    return headers


def _safe_request(method, url, headers, cookies):
    """执行 HTTP 请求并自动延迟

    :return: requests.Response 对象（异常由调用方处理）
    """
    resp = method(url, headers=headers, cookies=cookies, timeout=30)
    _op_delay()
    return resp


def _check_fav_403_response(resp, content_id):
    """处理 403 响应的特殊逻辑：检查是否为"已收藏/已存在"等可忽略错误

    :return: (success, message) 如果是可忽略的 403；否则 (False, error_msg)
    """
    try:
        err = resp.json()
        err_msg = str(err.get("error", {}))
        if "已收藏" in err_msg or "already" in err_msg.lower():
            return True, f"内容已在收藏夹中 (content_id={content_id})"
        if err.get("error", {}).get("code") == 106:
            return True, f"内容已在收藏夹中 (content_id={content_id})"
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────
# URL 解析
# ──────────────────────────────────────────────


def parse_article_info(url):
    """解析文章URL，提取 content_id 和 content_type

    支持格式：
      - https://www.zhihu.com/question/xxx/answer/yyy   → answer, yyy
      - https://zhuanlan.zhihu.com/p/xxx                   → article, xxx
      - https://www.zhihu.com/zvideo/xxx                   → zvideo, xxx
      - https://www.zhihu.com/pin/xxx                      → pin, xxx

    :return: (content_id, content_type) 或 (None, None)
    """
    m = re.search(r"/question/\d+/answer/(\d+)", url)
    if m:
        return m.group(1), "answer"

    m = re.search(r"zhuanlan\.zhihu\.com/p/(\d+)", url)
    if m:
        return m.group(1), "article"

    m = re.search(r"/zvideo/(\d+)", url)
    if m:
        return m.group(1), "zvideo"

    m = re.search(r"/pin/(\d+)", url)
    if m:
        return m.group(1), "pin"

    m = re.search(r"/(\d+)(?:\?|#|$)", url)
    if m:
        return m.group(1), "unknown"

    return None, None


# ──────────────────────────────────────────────
# 核心操作
# ──────────────────────────────────────────────


def favorite_content(content_type, content_id, collection_id=None):
    """收藏指定内容到收藏夹

    两种方式：
    - 不传 collection_id → 添加到默认收藏夹 (POST /api/v4/collections/contents/{type}/{id})
    - 传入 collection_id → 添加到指定收藏夹 (POST /api/v4/collections/{id}/contents)

    指定收藏夹时使用 query params 而非 JSON body，避免触发 x-zse-96 签名验证。

    :param content_type: 内容类型 (answer/article/zvideo/pin)
    :param content_id: 内容ID
    :param collection_id: 目标收藏夹ID（可选）
    :return: (success: bool, message: str)
    """
    cookies = get_cookies()
    headers = _build_auth_headers()

    try:
        if collection_id:
            api_url = (
                f"https://www.zhihu.com/api/v4/collections/{collection_id}/contents"
                f"?content_type={content_type}&content_id={content_id}"
            )
            qp_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
            logging.info(f"添加收藏(指定收藏夹): POST {api_url}")
            resp = _safe_request(requests.post, api_url, qp_headers, cookies)
        else:
            api_url = (
                f"https://www.zhihu.com/api/v4/collections/contents/"
                f"{content_type}/{content_id}"
            )
            logging.info(f"添加收藏(默认收藏夹): POST {api_url}")
            resp = _safe_request(requests.post, api_url, headers, cookies)
    except requests.exceptions.Timeout:
        return False, "请求超时（30s），请检查网络连接"
    except requests.exceptions.ConnectionError as e:
        return False, f"网络连接失败: {str(e)}"
    except Exception as e:
        logging.error(f"添加收藏异常: {str(e)}")
        return False, f"操作异常: {str(e)}"

    return _parse_fav_response(resp, content_id, collection_id)


def unfavorite_content(content_type, content_id):
    """取消收藏指定内容

    DELETE /api/v4/collections/contents/{type}/{id}

    :param content_type: 内容类型 (answer/article/zvideo/pin)
    :param content_id: 内容ID
    :return: (success: bool, message: str)
    """
    cookies = get_cookies()
    headers = _build_auth_headers()

    api_url = (
        f"https://www.zhihu.com/api/v4/collections/contents/{content_type}/{content_id}"
    )
    logging.info(f"取消收藏: DELETE {api_url}")

    try:
        resp = _safe_request(requests.delete, api_url, headers, cookies)
    except requests.exceptions.Timeout:
        return False, "请求超时（30s），请检查网络连接"
    except requests.exceptions.ConnectionError as e:
        return False, f"网络连接失败: {str(e)}"
    except Exception as e:
        logging.error(f"取消收藏异常: {str(e)}")
        return False, f"操作异常: {str(e)}"

    return _parse_unfav_response(resp, content_id)


def _parse_fav_response(resp, content_id, collection_id=None):
    """解析收藏 API 响应

    处理 200/201/204/403 等各种状态码，401 视为 cookies 过期。
    """
    if resp is None:
        return False, "请求失败，请检查网络连接"

    if resp.status_code == 401:
        return False, "Cookies已过期，请重新登录获取 cookies.json"

    if resp.status_code == 200:
        try:
            result = resp.json()
            if result.get("success") is False:
                return False, f"收藏失败: {result.get('error', '未知错误')}"

            if collection_id:
                return True, f"已添加到收藏夹 (collection_id={collection_id}, content_id={content_id})"
            else:
                coll_name = result.get("collection", {}).get("title", "默认收藏夹")
                return True, f"已收藏到「{coll_name}」(content_id={content_id})"
        except json.JSONDecodeError:
            return True, f"已收藏 (content_id={content_id})"

    if resp.status_code in (201, 204):
        label = f"收藏夹 {collection_id}" if collection_id else "收藏夹"
        return True, f"已添加到{label} (content_id={content_id})"

    if resp.status_code == 403:
        checked = _check_fav_403_response(resp, content_id)
        if checked is not None:
            return checked
        return False, "添加收藏被拒绝 (HTTP 403)，可能是反爬虫限制或 cookies 过期"

    error_body = resp.text[:300] if resp.text else "无响应体"
    return False, f"添加收藏失败 (HTTP {resp.status_code})\n响应: {error_body}"


def _parse_unfav_response(resp, content_id):
    """解析取消收藏 API 响应

    处理 200/201/204/403 等各种状态码。
    """
    if resp is None:
        return False, "请求失败，请检查网络连接"

    if resp.status_code == 401:
        return False, "Cookies已过期，请重新登录获取 cookies.json"

    if resp.status_code == 200:
        try:
            result = resp.json()
            favlists_count = result.get("favlists_count", "?")
            logging.info(f"取消收藏成功, 当前收藏数: {favlists_count}")
        except json.JSONDecodeError:
            pass
        return True, f"已取消收藏 (content_id={content_id})"

    if resp.status_code in (201, 204):
        return True, f"已取消收藏 (content_id={content_id})"

    if resp.status_code == 403:
        try:
            err = resp.json()
            if "未收藏" in str(err.get("error", {})):
                return True, f"本来就没有收藏该内容 (content_id={content_id})"
        except Exception:
            pass

    error_body = resp.text[:300] if resp.text else "无响应体"
    return False, f"取消收藏失败 (HTTP {resp.status_code})\n响应: {error_body}"


# ──────────────────────────────────────────────
# 高层封装
# ──────────────────────────────────────────────


def add_to_collection(collection_url, article_url):
    """将一篇文章添加到知乎收藏夹

    :param collection_url: 目标收藏夹URL，如 https://www.zhihu.com/collection/123456789
    :param article_url: 要收藏的文章URL
    :return: (success: bool, message: str)
    """
    collection_id = collection_url.split("?")[0].split("/")[-1]
    content_id, content_type = parse_article_info(article_url)

    if not content_id:
        return False, f"无法从URL中解析文章ID: {article_url}"

    logging.info(
        f"添加收藏: 收藏夹={collection_id}, "
        f"content_id={content_id}, type={content_type}"
    )

    return favorite_content(content_type, content_id, collection_id=collection_id)


def remove_from_collection(collection_url, article_url):
    """从知乎收藏夹中取消收藏一篇文章

    :param collection_url: 收藏夹URL
    :param article_url: 要取消收藏的文章URL
    :return: (success: bool, message: str)
    """
    content_id, content_type = parse_article_info(article_url)

    if not content_id:
        return False, f"无法从URL中解析文章ID: {article_url}"

    collection_id = collection_url.split("?")[0].split("/")[-1]
    logging.info(
        f"取消收藏: 收藏夹={collection_id}, "
        f"content_id={content_id}, type={content_type}"
    )

    return unfavorite_content(content_type, content_id)


def move_to_collection(from_collection_url, to_collection_url, article_url):
    """将文章从一个收藏夹移动到另一个收藏夹

    策略: 先添加至目标, 再从源移除, 最后验证。
    若移除操作意外清空了目标收藏中的内容，验证步骤会自动修复。

    :param from_collection_url: 源收藏夹URL
    :param to_collection_url: 目标收藏夹URL
    :param article_url: 要移动的文章URL
    :return: (success: bool, message: str)
    """
    from_id = from_collection_url.split("?")[0].split("/")[-1]
    to_id = to_collection_url.split("?")[0].split("/")[-1]
    content_id, content_type = parse_article_info(article_url)

    if not content_id:
        return False, f"无法从URL中解析文章ID: {article_url}"

    logging.info(
        f"移动收藏: {from_id} -> {to_id}, content_id={content_id}, type={content_type}"
    )

    result_parts = []
    all_success = True

    add_success, add_msg = favorite_content(content_type, content_id, collection_id=to_id)
    result_parts.append(f"[添加至目标] {add_msg}")

    if not add_success:
        return False, "\n".join(result_parts) + "\n添加失败，未执行移除操作"

    _move_step_delay()

    remove_success, remove_msg = unfavorite_content(content_type, content_id)
    result_parts.append(f"[从源移除] {remove_msg}")

    if not remove_success:
        all_success = False
        result_parts.append("移除失败，内容可能同时存在于两个收藏夹")

    time.sleep(random.uniform(0.5, 1.0))

    verify_success, verify_msg = favorite_content(content_type, content_id, collection_id=to_id)
    result_parts.append(f"[验证/修复] {verify_msg}")

    summary = "移动成功" if all_success else "移动部分成功"
    return all_success, f"{summary}\n" + "\n".join(result_parts)
