# -*- coding:utf-8 -*-
"""
知乎收藏夹管理 - 收藏/取消收藏/移动操作

独立模块，不依赖 main.py 的全局状态。
所有 cookie 和 HTTP 请求自包含。

通过浏览器抓包确定的 API 端点：
  - 收藏(添加): POST   /api/v4/collections/contents/{type}/{id}
  - 取消收藏:    DELETE /api/v4/collections/contents/{type}/{id}
  - 添加到指定:  POST   /api/v4/collections/{collection_id}/contents

延迟策略（参照 main.py: random.randint(1,5) for downloads）：
  - 单次收藏/取消后延迟: 1.0 ~ 3.0 秒
  - 移动操作内部步骤间: 1 ~ 5 秒
"""

import json
import logging
import os
import random
import re
import time

import requests

# ──────────────────────────────────────────────
# 请求延迟常量
# ──────────────────────────────────────────────

# 单次收藏/取消操作后的延迟（比 GET 更保守，写操作更易触发反爬）
_OP_DELAY_MIN = 1.0
_OP_DELAY_MAX = 3.0

# 移动操作内部步骤间延迟（参照 main.py 的 random.randint(1, 5)）
_MOVE_DELAY_MIN = 1
_MOVE_DELAY_MAX = 5

# ──────────────────────────────────────────────
# Cookie 加载
# ──────────────────────────────────────────────


def _load_cookies():
    """加载 cookies.json，返回 dict"""
    try:
        cookies_file = os.path.join(os.path.dirname(__file__), "cookies.json")
        with open(cookies_file, "r", encoding="utf-8") as f:
            cookies_list = json.load(f)
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie["name"]] = cookie["value"]
        return cookies_dict
    except FileNotFoundError:
        logging.warning("未找到 cookies.json，收藏/取消收藏操作可能失败")
        return {}


# 模块级 cookies 缓存（延迟加载，支持 MCP server 热重载）
_cookies = None


def get_cookies():
    global _cookies
    if _cookies is None:
        _cookies = _load_cookies()
    return _cookies


# ──────────────────────────────────────────────
# URL 解析
# ──────────────────────────────────────────────


def parse_article_info(url):
    """
    解析文章URL，提取 content_id 和 content_type

    支持格式：
      - https://www.zhihu.com/question/xxx/answer/yyy   → answer, yyy
      - https://zhuanlan.zhihu.com/p/xxx                  → article, xxx
      - https://www.zhihu.com/zvideo/xxx                  → zvideo, xxx
      - https://www.zhihu.com/pin/xxx                     → pin, xxx
    """
    # 匹配回答: /question/xxx/answer/yyy 或 /question/xxx/answer/yyy?...
    m = re.search(r"/question/\d+/answer/(\d+)", url)
    if m:
        return m.group(1), "answer"

    # 匹配专栏文章: /p/xxx
    m = re.search(r"zhuanlan\.zhihu\.com/p/(\d+)", url)
    if m:
        return m.group(1), "article"

    # 匹配视频: /zvideo/xxx
    m = re.search(r"/zvideo/(\d+)", url)
    if m:
        return m.group(1), "zvideo"

    # 匹配想法: /pin/xxx
    m = re.search(r"/pin/(\d+)", url)
    if m:
        return m.group(1), "pin"

    # 兜底：取URL最后一段数字
    m = re.search(r"/(\d+)(?:\?|#|$)", url)
    if m:
        return m.group(1), "unknown"

    return None, None


# ──────────────────────────────────────────────
# 核心操作
# ──────────────────────────────────────────────


def _op_delay():
    """单次收藏/取消操作后的延迟，避免触发频率限制"""
    time.sleep(random.uniform(_OP_DELAY_MIN, _OP_DELAY_MAX))


def _move_step_delay():
    """移动操作内部步骤间延迟，参照 main.py 下载间隔"""
    time.sleep(random.randint(_MOVE_DELAY_MIN, _MOVE_DELAY_MAX))


def favorite_content(content_type, content_id, collection_id=None):
    """
    收藏指定内容（添加到收藏夹）

    方式1（添加到默认收藏夹）：
      POST /api/v4/collections/contents/{content_type}/{content_id}
      返回: {"collection":{...}, "success":true}

    方式2（添加到指定收藏夹）：
      POST /api/v4/collections/{collection_id}/contents?content_type=...&content_id=...
      注意: 使用 query params 而非 JSON body，避免触发反爬虫 (x-zse-96 签名验证)
      返回: {"success":true}

    :param content_type: 内容类型 (answer/article/zvideo/pin)
    :param content_id: 内容ID
    :param collection_id: 目标收藏夹ID（可选，不传则添加到默认收藏夹）
    :return: (success: bool, message: str)
    """
    cookies = get_cookies()
    xsrf_token = cookies.get("_xsrf", "")

    # 专用请求头（从浏览器拦截复制）
    fav_headers = {
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
        fav_headers["X-Xsrftoken"] = xsrf_token

    if collection_id:
        # 方式2：添加到指定收藏夹（使用 query params，不使用 JSON body 避免反爬虫）
        api_url = (
            f"https://www.zhihu.com/api/v4/collections/{collection_id}/contents"
            f"?content_type={content_type}&content_id={content_id}"
        )
        logging.info(f"添加收藏(指定收藏夹): POST {api_url}")

        try:
            # 注意: 不发送 JSON body，也不设置 Content-Type: application/json
            # query params 的方式不会触发 x-zse-96 签名验证
            qp_headers = {k: v for k, v in fav_headers.items() if k != "Content-Type"}
            resp = requests.post(
                api_url,
                headers=qp_headers,
                cookies=cookies,
                timeout=30,
            )
            _op_delay()  # 请求后延迟，避免频率限制

            if resp.status_code == 200:
                try:
                    result = resp.json()
                    if result.get("success"):
                        return True, (
                            f"✅ 已添加到收藏夹 {collection_id} "
                            f"(content_id={content_id})"
                        )
                    return True, (f"✅ 内容已在收藏夹中 (content_id={content_id})")
                except json.JSONDecodeError:
                    return True, (f"✅ 已添加到收藏夹 (content_id={content_id})")

            if resp.status_code in (201, 204):
                return True, (f"✅ 已添加到收藏夹 (content_id={content_id})")

            # 403 处理：可能是已收藏或反爬虫
            if resp.status_code == 403:
                try:
                    err = resp.json()
                    err_msg = str(err.get("error", {}))
                    # "您已经收藏过该内容" → 视为成功
                    if (
                        "已收藏" in err_msg
                        or "already" in err_msg.lower()
                        or err.get("error", {}).get("code") == 106
                    ):
                        return True, (f"✅ 内容已在收藏夹中 (content_id={content_id})")
                except Exception:
                    pass

            error_body = resp.text[:300] if resp.text else "无响应体"
            return False, (
                f"❌ 添加收藏失败 (HTTP {resp.status_code})\n"
                f"   响应: {error_body}\n"
                f"   提示: 可能是Cookies已过期，请重新登录获取 cookies.json"
            )

        except requests.exceptions.Timeout:
            return False, "❌ 请求超时（30s），请检查网络连接"
        except requests.exceptions.ConnectionError as e:
            return False, f"❌ 网络连接失败: {str(e)}"
        except Exception as e:
            logging.error(f"添加收藏异常: {str(e)}")
            return False, f"❌ 操作异常: {str(e)}"

    else:
        # 方式1：添加到默认收藏夹
        api_url = (
            f"https://www.zhihu.com/api/v4/collections/contents/"
            f"{content_type}/{content_id}"
        )
        logging.info(f"添加收藏(默认收藏夹): POST {api_url}")

        try:
            resp = requests.post(
                api_url,
                headers=fav_headers,
                cookies=cookies,
                timeout=30,
            )
            _op_delay()  # 请求后延迟，避免频率限制

            if resp.status_code == 200:
                try:
                    result = resp.json()
                    if result.get("success"):
                        collection_info = result.get("collection", {})
                        coll_name = collection_info.get("title", "默认收藏夹")
                        return True, (
                            f"✅ 已收藏到「{coll_name}」(content_id={content_id})"
                        )
                    return True, (f"✅ 已收藏 (content_id={content_id})")
                except json.JSONDecodeError:
                    return True, (f"✅ 已收藏 (content_id={content_id})")

            if resp.status_code in (201, 204):
                return True, f"✅ 已收藏 (content_id={content_id})"

            if resp.status_code == 403:
                try:
                    err = resp.json()
                    err_msg = str(err.get("error", {}))
                    if "已收藏" in err_msg or "already" in err_msg.lower():
                        return True, (f"✅ 内容已在收藏夹中 (content_id={content_id})")
                except Exception:
                    pass

            error_body = resp.text[:300] if resp.text else "无响应体"
            return False, (
                f"❌ 添加收藏失败 (HTTP {resp.status_code})\n"
                f"   响应: {error_body}\n"
                f"   提示: 可能是Cookies已过期，请重新登录获取 cookies.json"
            )

        except requests.exceptions.Timeout:
            return False, "❌ 请求超时（30s），请检查网络连接"
        except requests.exceptions.ConnectionError as e:
            return False, f"❌ 网络连接失败: {str(e)}"
        except Exception as e:
            logging.error(f"添加收藏异常: {str(e)}")
            return False, f"❌ 操作异常: {str(e)}"


def unfavorite_content(content_type, content_id):
    """
    取消收藏指定内容（从收藏夹中移除）

    DELETE /api/v4/collections/contents/{content_type}/{content_id}

    :param content_type: 内容类型 (answer/article/zvideo/pin)
    :param content_id: 内容ID
    :return: (success: bool, message: str)
    """
    cookies = get_cookies()
    xsrf_token = cookies.get("_xsrf", "")

    api_url = (
        f"https://www.zhihu.com/api/v4/collections/contents/{content_type}/{content_id}"
    )

    unfav_headers = {
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
        unfav_headers["X-Xsrftoken"] = xsrf_token

    logging.info(f"取消收藏: DELETE {api_url}")

    try:
        resp = requests.delete(
            api_url,
            headers=unfav_headers,
            cookies=cookies,
            timeout=30,
        )
        _op_delay()  # 请求后延迟，避免频率限制

        if resp.status_code == 200:
            try:
                result = resp.json()
                # data 可能是 list 或 dict
                favlists_count = result.get("favlists_count", "?")
                logging.info(f"取消收藏成功, 当前收藏数: {favlists_count}")
            except json.JSONDecodeError:
                pass
            return True, f"✅ 已取消收藏 (content_id={content_id})"

        if resp.status_code in (201, 204):
            return True, f"✅ 已取消收藏 (content_id={content_id})"

        # 如果是403且错误是"未收藏"，也算成功
        if resp.status_code == 403:
            try:
                err = resp.json()
                if "未收藏" in str(err.get("error", {})):
                    return True, (f"✅ 本来就没有收藏该内容 (content_id={content_id})")
            except Exception:
                pass

        error_body = resp.text[:300] if resp.text else "无响应体"
        return False, (
            f"❌ 取消收藏失败 (HTTP {resp.status_code})\n"
            f"   响应: {error_body}\n"
            f"   提示: 可能是Cookies已过期，请重新登录获取 cookies.json"
        )

    except requests.exceptions.Timeout:
        return False, "❌ 请求超时（30s），请检查网络连接"
    except requests.exceptions.ConnectionError as e:
        return False, f"❌ 网络连接失败: {str(e)}"
    except Exception as e:
        logging.error(f"取消收藏异常: {str(e)}")
        return False, f"❌ 操作异常: {str(e)}"


# ──────────────────────────────────────────────
# 高层封装
# ──────────────────────────────────────────────


def add_to_collection(collection_url, article_url):
    """
    将一篇文章添加到知乎收藏夹

    :param collection_url: 目标收藏夹URL
                           如 https://www.zhihu.com/collection/123456789
    :param article_url: 要收藏的文章URL
                        如 https://zhuanlan.zhihu.com/p/2017496853827060720
    :return: (success: bool, message: str)
    """
    collection_id = collection_url.split("?")[0].split("/")[-1]
    content_id, content_type = parse_article_info(article_url)

    if not content_id:
        return False, f"❌ 无法从URL中解析文章ID: {article_url}"

    logging.info(
        f"添加收藏: 收藏夹={collection_id}, "
        f"content_id={content_id}, type={content_type}"
    )

    return favorite_content(content_type, content_id, collection_id=collection_id)


def remove_from_collection(collection_url, article_url):
    """
    从知乎收藏夹中取消收藏一篇文章

    :param collection_url: 收藏夹URL（仅用于日志）
    :param article_url: 要取消收藏的文章URL
    :return: (success: bool, message: str)
    """
    content_id, content_type = parse_article_info(article_url)

    if not content_id:
        return False, f"❌ 无法从URL中解析文章ID: {article_url}"

    collection_id = collection_url.split("?")[0].split("/")[-1]
    logging.info(
        f"取消收藏: 收藏夹={collection_id}, "
        f"content_id={content_id}, type={content_type}"
    )

    return unfavorite_content(content_type, content_id)


def move_to_collection(from_collection_url, to_collection_url, article_url):
    """
    将文章从一个收藏夹移动到另一个收藏夹

    策略：先添加到目标收藏夹，再从源收藏夹移除。
    如果移除操作同时清除了目标收藏夹中的内容，会自动重新添加。

    :param from_collection_url: 源收藏夹URL
    :param to_collection_url: 目标收藏夹URL
    :param article_url: 要移动的文章URL
    :return: (success: bool, message: str)
    """
    from_id = from_collection_url.split("?")[0].split("/")[-1]
    to_id = to_collection_url.split("?")[0].split("/")[-1]
    content_id, content_type = parse_article_info(article_url)

    if not content_id:
        return False, f"❌ 无法从URL中解析文章ID: {article_url}"

    logging.info(
        f"移动收藏: {from_id} → {to_id}, content_id={content_id}, type={content_type}"
    )

    result_parts = []
    all_success = True

    # 第一步：添加到目标收藏夹
    add_success, add_msg = favorite_content(
        content_type, content_id, collection_id=to_id
    )
    result_parts.append(f"【添加至目标】{add_msg}")

    if not add_success:
        return (
            False,
            "\n".join(result_parts) + "\n⚠️ 添加失败，未执行移除操作",
        )

    # 给服务器一点时间处理（参照 main.py: random.randint(1,5)）
    _move_step_delay()

    # 第二步：从源收藏夹移除
    remove_success, remove_msg = unfavorite_content(content_type, content_id)
    result_parts.append(f"【从源移除】{remove_msg}")

    if not remove_success:
        all_success = False
        result_parts.append("⚠️ 移除失败，内容可能同时存在于两个收藏夹")

    # 第三步：验证 —— 重新添加到目标（防止移除操作清空了所有收藏）
    time.sleep(random.uniform(0.5, 1.0))
    verify_success, verify_msg = favorite_content(
        content_type, content_id, collection_id=to_id
    )
    result_parts.append(f"【验证/修复】{verify_msg}")

    summary = "✅ 移动成功" if all_success else "⚠️ 移动部分成功"
    return all_success, f"{summary}\n" + "\n".join(result_parts)
