# -*- coding:utf-8 -*-
from __future__ import annotations

import os
import re
import time
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from zhihu_collections._paths import get_debug_path
from zhihu_collections._logging import flush_logs


def smart_content_detection(soup: BeautifulSoup, url: str) -> Optional[BeautifulSoup]:
    """智能内容检测 — 当标准选择器失败时自动定位文章正文

    采用三级策略：
    1. 查找包含大量非链接文本的 div
    2. 查找 <article> 或 <main> 标签
    3. 查找包含多个 <p> 段落的容器
    """
    logging.debug(f"开始智能内容检测: {url}")

    all_divs = soup.find_all("div")
    text_length_threshold = 200

    candidates: list[dict] = []
    for div in all_divs:
        text_content = div.get_text(strip=True)
        if len(text_content) > text_length_threshold:
            link_count = len(div.find_all("a"))
            text_to_link_ratio = len(text_content) / max(link_count, 1)
            candidates.append(
                {
                    "element": div,
                    "text_length": len(text_content),
                    "text_to_link_ratio": text_to_link_ratio,
                    "classes": div.get("class", []),
                }
            )

    candidates.sort(key=lambda x: x["text_length"], reverse=True)

    if candidates:
        best_candidate = candidates[0]
        logging.debug(
            f"智能检测找到候选内容，长度: {best_candidate['text_length']}, classes: {best_candidate['classes']}"
        )
        if best_candidate["text_length"] > 500:
            return best_candidate["element"]

    article_containers = soup.find_all(["article", "main"])
    for container in article_containers:
        text_content = container.get_text(strip=True)
        if len(text_content) > text_length_threshold:
            logging.debug(f"找到文章容器: {container.name}")
            return container

    for div in all_divs:
        paragraphs = div.find_all("p")
        if len(paragraphs) >= 3:
            total_p_text = sum(len(p.get_text(strip=True)) for p in paragraphs)
            if total_p_text > text_length_threshold:
                logging.debug(f"找到多段落容器，段落数: {len(paragraphs)}")
                return div

    logging.debug("智能内容检测未找到合适的内容")
    return None


def analyze_page_error(
    soup: BeautifulSoup, response: requests.Response, url: str
) -> str:
    """分析页面错误类型，返回人类可读的错误描述"""
    page_text = response.text.lower()

    if "404" in page_text or "not found" in page_text or "页面不存在" in page_text:
        return "该文章链接被404, 无法直接访问"

    if "登录" in response.text or "login" in page_text or "请先登录" in response.text:
        return "该文章需要登录访问，请检查cookies配置"

    if "403" in page_text or "forbidden" in page_text or "访问被拒绝" in response.text:
        return "该文章访问被拒绝，可能需要特殊权限"

    if (
        "已删除" in response.text
        or "内容不存在" in response.text
        or "deleted" in page_text
    ):
        return "该文章内容已被删除或不存在"

    if response.url != url:
        return f"页面被重定向到: {response.url}, 可能是登录页面或错误页面"

    zhihu_indicators = ["知乎", "zhihu", "www.zhihu.com"]
    has_zhihu_structure = any(indicator in page_text for indicator in zhihu_indicators)

    if not has_zhihu_structure:
        return "页面结构异常，可能不是正常的知乎页面"

    return "页面结构可能发生变化，无法解析文章内容"


def html_template(data: str) -> str:
    """将 HTML 片段包装为完整的 HTML 文档"""
    return "<html><head></head><body>%s</body></html>" % data


def _clean_content_soup(soup: BeautifulSoup) -> None:
    """清理 BeautifulSoup 对象中的干扰元素：style 标签、空白 SVG、卡片链接、mailto"""
    for el in soup.find_all("style"):
        el.extract()

    for el in soup.select('img[src*="data:image/svg+xml"]'):
        el.extract()

    for el in soup.find_all("a"):
        aclass = el.get("class")
        if isinstance(aclass, list) and "LinkCard" in aclass:
            linkcard_name = el.get("data-text")
            el.string = linkcard_name if linkcard_name is not None else el.get("href")
        try:
            if el.get("href") and el.get("href").startswith("mailto"):
                el.name = "p"
        except:
            pass


def _save_debug_html(
    html_text: str, url: str, prefix: str, base_output_path: Optional[str]
) -> None:
    """保存调试 HTML 到 debug/ 目录"""
    debug_dir = get_debug_path(base_output_path)
    os.makedirs(debug_dir, exist_ok=True)
    debug_file = os.path.join(debug_dir, f"debug_{prefix}_{url.split('/')[-1]}.html")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(html_text)
    logging.debug(f"页面HTML已保存到: {debug_file}")
    flush_logs()


def get_single_answer_content(
    answer_url: str,
    headers: dict[str, str],
    cookies: dict[str, str],
    api_headers: dict[str, str],
    base_output_path: Optional[str],
) -> str | int:
    """获取知乎回答的 HTML 内容

    优先使用 HTML 页面解析，失败时回退到 API (/api/v4/answers/{id})。

    :return: HTML 内容字符串，失败返回 -1
    """
    if '/zvideo/' in answer_url or '/pin/' in answer_url:
        return -1

    logging.debug(f"开始获取回答内容: {answer_url}")
    flush_logs()

    answer_id_match = re.search(r"/answer/(\d+)", answer_url)
    answer_id = answer_id_match.group(1) if answer_id_match else None

    try:
        html_content = requests.get(
            answer_url, headers=headers, cookies=cookies, timeout=30
        )
        logging.debug(f"HTTP请求状态码: {html_content.status_code}")

        if html_content.status_code == 403:
            logging.warning(f"HTML请求返回403，尝试API备用方案: {answer_url}")
            flush_logs()

            if answer_id:
                api_url = (
                    f"https://www.zhihu.com/api/v4/answers/{answer_id}?include=content"
                )
                logging.debug(f"调用API: {api_url}")
                try:
                    api_response = requests.get(
                        api_url,
                        headers=api_headers,
                        cookies=cookies,
                        timeout=30,
                    )
                    api_response.raise_for_status()
                    api_data = api_response.json()

                    if api_data and "content" in api_data:
                        content_html = api_data["content"]
                        logging.info(
                            f"API备用方案成功获取内容，长度: {len(content_html)}"
                        )
                        flush_logs()

                        soup = BeautifulSoup(content_html, "lxml")
                        _clean_content_soup(soup)
                        return html_template(str(soup))

                except Exception as api_e:
                    logging.error(f"API备用方案失败: {str(api_e)}")
                    flush_logs()
            else:
                logging.error(f"无法从URL提取answer_id: {answer_url}")
                flush_logs()
                return -1

        html_content.raise_for_status()
        logging.debug(f"HTTP请求成功，状态码: {html_content.status_code}")

        soup = BeautifulSoup(html_content.text, "lxml")
        answer_content = None

        selectors: list[tuple[str, dict]] = [
            ("div", {"class": "AnswerCard"}),
            ("div", {"class": "QuestionAnswer-content"}),
            ("div", {"class": "RichContent"}),
            ("div", {"class": "ContentItem-expandButton"}),
        ]

        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs)
            if elements:
                logging.debug(f"找到{len(elements)}个 {tag} {attrs} 元素")
                for element in elements:
                    inner = element.find("div", class_="RichContent-inner")
                    if inner:
                        answer_content = inner
                        logging.debug("成功找到RichContent-inner元素")
                        break
                if answer_content:
                    break

        if not answer_content:
            answer_content = soup.find("div", class_="RichContent-inner")
            if answer_content:
                logging.debug("直接找到RichContent-inner元素")

        if not answer_content:
            fallback_selectors = [
                "div.RichText",
                "div.Post-RichText",
                "div.ContentItem-content",
                ".QuestionAnswer .RichContent",
            ]
            for selector in fallback_selectors:
                answer_content = soup.select_one(selector)
                if answer_content:
                    logging.debug(f"使用备用选择器找到内容: {selector}")
                    break

        if not answer_content:
            logging.error(f"未找到回答内容容器: {answer_url}")
            _save_debug_html(html_content.text, answer_url, "answer", base_output_path)
            return -1

        for el in answer_content.find_all("style"):
            el.extract()

    except Exception as e:
        logging.error(f"获取回答内容时发生错误: {str(e)}")
        logging.error(f"URL: {answer_url}")
        flush_logs()
        return -1

    for el in answer_content.select('img[src*="data:image/svg+xml"]'):
        el.extract()

    for el in answer_content.find_all("a"):
        aclass = el.get("class")
        if isinstance(aclass, list):
            if aclass[0] == "LinkCard":
                linkcard_name = el.get("data-text")
                el.string = (
                    linkcard_name if linkcard_name is not None else el.get("href")
                )
        else:
            pass
        try:
            if el.get("href").startswith("mailto"):
                el.name = "p"
        except:
            pass

    return html_template(str(answer_content))


def get_single_post_content(
    paper_url: str,
    headers: dict[str, str],
    cookies: dict[str, str],
    api_headers: dict[str, str],
    base_output_path: Optional[str],
) -> str:
    """获取知乎专栏文章的 HTML 内容

    优先使用 API (/api/v4/articles/{id})，失败后回退到 HTML 解析（含重试）。

    :return: HTML 内容字符串
    """
    logging.debug(f"开始获取专栏文章内容: {paper_url}")
    flush_logs()

    article_id_match = re.search(r"zhuanlan\.zhihu\.com/p/(\d+)", paper_url)
    article_id = article_id_match.group(1) if article_id_match else None

    if article_id:
        try:
            api_url = (
                f"https://www.zhihu.com/api/v4/articles/{article_id}?include=content"
            )
            api_response = requests.get(
                api_url, headers=api_headers, cookies=cookies, timeout=30
            )
            if api_response.status_code == 200:
                api_data = api_response.json()
                if api_data and "content" in api_data:
                    content_html = api_data["content"]
                    logging.info(
                        f"API备用方案成功获取专栏内容，长度: {len(content_html)}"
                    )
                    flush_logs()
                    soup = BeautifulSoup(content_html, "lxml")
                    _clean_content_soup(soup)
                    return html_template(str(soup))
        except Exception as api_e:
            logging.warning(f"专栏API备用方案失败: {str(api_e)}")
            flush_logs()

    max_retries = 2
    last_error: Optional[str] = None

    for retry in range(max_retries):
        post_content = None
        try:
            html_content = requests.get(
                paper_url,
                headers=headers,
                cookies=cookies,
                timeout=120,
                stream=True,
            )
            html_content.raise_for_status()
            logging.debug(f"HTTP请求成功，状态码: {html_content.status_code}")

            content_bytes = b""
            for chunk in html_content.iter_content(chunk_size=8192):
                if chunk:
                    content_bytes += chunk
            html_text = content_bytes.decode("utf-8", errors="ignore")
            logging.debug(f"内容长度: {len(html_text)} 字符")

            soup = BeautifulSoup(html_text, "lxml")

            selectors: list[tuple[str, dict]] = [
                ("div", {"class": "Post-RichText"}),
                ("div", {"class": "RichContent"}),
                ("div", {"class": "RichContent-inner"}),
                ("div", {"class": "Post-content"}),
                ("div", {"class": "Post-RichTextContainer"}),
                ("div", {"class": "ztext"}),
                ("div", {"class": "Post-Main"}),
                ("div", {"class": "Article-RichText"}),
            ]

            for tag, attrs in selectors:
                post_content = soup.find(tag, attrs)
                if post_content:
                    logging.debug(f"找到专栏内容: {tag} {attrs}")
                    break

            if not post_content:
                fallback_selectors = [
                    "div.RichText",
                    "div.Post-content",
                    "div.ContentItem-content",
                    ".Post .RichContent",
                    ".Post-RichTextContainer",
                    ".ztext",
                    ".Post-Main .RichContent",
                    "[data-zop-editor]",
                    ".Article-RichText",
                ]
                for selector in fallback_selectors:
                    post_content = soup.select_one(selector)
                    if post_content:
                        logging.debug(f"使用备用选择器找到内容: {selector}")
                        break

            if not post_content:
                post_content = smart_content_detection(soup, paper_url)
                if post_content:
                    logging.debug("使用智能内容检测找到内容")

            if not post_content:
                error_message = analyze_page_error(soup, html_content, paper_url)
                logging.error(
                    f"未找到专栏内容容器: {paper_url} - {error_message}"
                )
                _save_debug_html(html_text, paper_url, "post", base_output_path)
                post_content = error_message

            if post_content and hasattr(post_content, "find_all"):
                for el in post_content.find_all("style"):
                    el.extract()
                for el in post_content.select('img[src*="data:image/svg+xml"]'):
                    el.extract()
                for el in post_content.find_all("a"):
                    aclass = el.get("class")
                    if isinstance(aclass, list):
                        if aclass[0] == "LinkCard":
                            linkcard_name = el.get("data-text")
                            el.string = (
                                linkcard_name
                                if linkcard_name is not None
                                else el.get("href")
                            )
                    else:
                        pass
                    try:
                        if el.get("href").startswith("mailto"):
                            el.name = "p"
                    except:
                        logging.warning(f"处理链接时出现问题: {paper_url}, {el}")

            if post_content:
                break

        except Exception as e:
            last_error = str(e)
            logging.warning(
                f"获取专栏文章内容时发生错误 (尝试 {retry + 1}/{max_retries}): {str(e)}"
            )
            logging.warning(f"URL: {paper_url}")
            flush_logs()

            if retry < max_retries - 1:
                time.sleep(2)
                continue
            else:
                logging.error(f"达到最大重试次数，放弃: {paper_url}")
                flush_logs()
                post_content = f"该文章链接获取失败: {last_error}"

    return html_template(str(post_content))


# ──────────────────────────────────────────────
# 想法(pin) / 视频(zvideo)
# ──────────────────────────────────────────────


def _build_pin_html_from_segments(content_list: list) -> str:
    """从 pin 的 content 分段列表组装 HTML（content_html 字段缺失时的 fallback）

    pin content 每段是 dict，type 字段区分类型：
      - text:  含 content/own_text HTML 文本，可带 title
      - image: 含 original_url/url 原图地址
      - video: 含 thumbnail 封面地址
      - link:  含 url 和 title
      - poll:  投票，暂不支持，跳过
    """
    parts: list[str] = []
    for seg in content_list:
        if not isinstance(seg, dict):
            continue
        seg_type = seg.get("type", "")
        if seg_type == "text":
            html_text = seg.get("content") or seg.get("own_text") or ""
            if html_text:
                parts.append(html_text)
        elif seg_type == "image":
            src = seg.get("original_url") or seg.get("url") or ""
            if src:
                parts.append(f'<img src="{src}">')
        elif seg_type == "video":
            thumb = seg.get("thumbnail") or ""
            if thumb:
                parts.append(f'<img src="{thumb}">')
        elif seg_type == "link":
            link_url = seg.get("url") or seg.get("original_url") or ""
            link_title = seg.get("title") or link_url
            if link_url:
                parts.append(f'<p><a href="{link_url}">{link_title}</a></p>')
        # poll 等其他类型暂不支持，跳过
    return "".join(parts)


def get_single_pin_content(
    pin_url: str,
    headers: dict[str, str],
    cookies: dict[str, str],
    api_headers: dict[str, str],
    base_output_path: Optional[str],
) -> str | int:
    """获取知乎想法(pin)的 HTML 内容

    优先使用 API (/api/v4/pins/{id}) 的 content_html 字段；
    content_html 缺失时从 content 分段列表组装。
    想法中的图片若为缩略图(src 带 /50/)，会替换为 data-original 原图地址，
    从而走现有 markdownify 图片下载流程保存到 assets/。

    :return: HTML 内容字符串，失败返回 -1
    """
    logging.debug(f"开始获取想法内容: {pin_url}")
    flush_logs()

    pin_id_match = re.search(r"/pin/(\d+)", pin_url)
    pin_id = pin_id_match.group(1) if pin_id_match else None
    if not pin_id:
        logging.error(f"无法从URL提取pin_id: {pin_url}")
        flush_logs()
        return -1

    try:
        api_url = f"https://www.zhihu.com/api/v4/pins/{pin_id}"
        api_response = requests.get(
            api_url, headers=api_headers, cookies=cookies, timeout=30
        )
        api_response.raise_for_status()
        api_data = api_response.json()
    except Exception as e:
        logging.error(f"获取想法内容时发生错误: {str(e)}")
        logging.error(f"URL: {pin_url}")
        flush_logs()
        return -1

    content_html = (api_data.get("content_html") or "").strip()
    if not content_html:
        content_html = _build_pin_html_from_segments(api_data.get("content") or [])

    if not content_html.strip():
        logging.error(f"想法内容为空: {pin_url}")
        _save_debug_html(str(api_data), pin_url, "pin", base_output_path)
        flush_logs()
        return -1

    soup = BeautifulSoup(content_html, "lxml")
    # 缩略图替换为原图（content_html 中图片 src 常为 50px 缩略图）
    for img in soup.find_all("img"):
        original = img.get("data-original")
        if original:
            img["src"] = original
    _clean_content_soup(soup)
    return html_template(str(soup))


def _format_duration_seconds(seconds: float) -> str:
    """把秒数格式化为 mm:ss 或 h:mm:ss"""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def get_single_zvideo_content(
    zvideo_url: str,
    headers: dict[str, str],
    cookies: dict[str, str],
    api_headers: dict[str, str],
    base_output_path: Optional[str],
) -> str | int:
    """获取知乎视频(zvideo)的 HTML 内容

    视频本体无法转换为 Markdown 文本，因此生成一个"视频信息页"：
    标题、封面图、作者、统计数据、简介描述和各清晰度播放链接。
    封面图会走现有图片下载流程保存到 assets/。

    :return: HTML 内容字符串，失败返回 -1
    """
    logging.debug(f"开始获取视频内容: {zvideo_url}")
    flush_logs()

    zvideo_id_match = re.search(r"/zvideo/(\d+)", zvideo_url)
    zvideo_id = zvideo_id_match.group(1) if zvideo_id_match else None
    if not zvideo_id:
        logging.error(f"无法从URL提取zvideo_id: {zvideo_url}")
        flush_logs()
        return -1

    try:
        api_url = f"https://www.zhihu.com/api/v4/zvideos/{zvideo_id}"
        api_response = requests.get(
            api_url, headers=api_headers, cookies=cookies, timeout=30
        )
        api_response.raise_for_status()
        api_data = api_response.json()
    except Exception as e:
        logging.error(f"获取视频内容时发生错误: {str(e)}")
        logging.error(f"URL: {zvideo_url}")
        flush_logs()
        return -1

    parts: list[str] = []
    title = (api_data.get("title") or "").strip()
    if title:
        parts.append(f"<h1>{title}</h1>")

    # 封面图
    video = api_data.get("video") or {}
    thumbnail = video.get("thumbnail") or api_data.get("image_url") or ""
    if thumbnail:
        parts.append(f'<p><img src="{thumbnail}"></p>')

    # 作者
    author = api_data.get("author") or {}
    author_name = author.get("name") or ""
    if author_name:
        parts.append(f"<p><strong>作者:</strong> {author_name}</p>")

    # 统计信息
    stats: list[str] = []
    duration = video.get("duration")
    if duration:
        stats.append(f"时长 {_format_duration_seconds(duration)}")
    if api_data.get("play_count") is not None:
        stats.append(f"播放 {api_data['play_count']:,}")
    if api_data.get("voteup_count") is not None:
        stats.append(f"赞同 {api_data['voteup_count']:,}")
    if api_data.get("comment_count") is not None:
        stats.append(f"评论 {api_data['comment_count']:,}")
    if api_data.get("published_at"):
        stats.append(
            f"发布于 {time.strftime('%Y-%m-%d', time.localtime(api_data['published_at']))}"
        )
    if stats:
        parts.append(f"<p>{' | '.join(stats)}</p>")

    # 简介描述
    description = (api_data.get("description") or "").strip()
    if description:
        parts.append(f"<blockquote>{description}</blockquote>")

    # 播放链接（带时效性）
    playlist = video.get("playlist_v2") or video.get("playlist") or {}
    if playlist:
        parts.append("<p><strong>播放地址:</strong></p>")
        parts.append("<ul>")
        quality_labels = {
            "fhd": "超清 (FHD)",
            "hd": "高清 (HD)",
            "sd": "标清 (SD)",
            "ld": "流畅 (LD)",
        }
        for quality in ("fhd", "hd", "sd", "ld"):
            entry = playlist.get(quality)
            if not entry:
                continue
            play_url = entry.get("play_url") or entry.get("url") or ""
            if not play_url:
                continue
            label = quality_labels.get(quality, quality)
            parts.append(f'<li><a href="{play_url}">{label}</a></li>')
        parts.append("</ul>")
        parts.append("<p><em>播放链接带时效性，若失效请访问原始页面。</em></p>")

    return html_template("".join(parts))
