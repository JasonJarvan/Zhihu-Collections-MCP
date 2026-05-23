# -*- coding:utf-8 -*-
from __future__ import annotations

import os
import time
import random
import logging
from typing import Any

import requests
from tqdm import tqdm

from zhihu_collections._paths import get_output_path
from zhihu_collections._logging import flush_logs
from zhihu_collections._content import get_single_answer_content, get_single_post_content
from zhihu_collections._converter import markdownify
from zhihu_collections._export import (
    ExportContext,
    is_article_already_downloaded,
    get_unique_filename,
)


def get_article_nums_of_collection(
    collection_id: str,
    headers: dict[str, str],
    cookies: dict[str, str],
) -> int:
    """获取收藏夹中的文章总数

    :param collection_id: 知乎收藏夹 ID
    :return: 文章总数，失败返回 0
    """
    try:
        collection_url = (
            f"https://www.zhihu.com/api/v4/collections/{collection_id}/items"
        )
        html = requests.get(
            collection_url, headers=headers, cookies=cookies, timeout=30
        )
        html.raise_for_status()

        result = html.json()["paging"].get("totals")
        logging.info(f"收藏夹 {collection_id} 包含 {result} 个项目")
        return result
    except Exception as e:
        logging.error(f"获取收藏夹 {collection_id} 总数失败: {str(e)}")
        return 0


def get_article_urls_in_collection(
    collection_id: str,
    headers: dict[str, str],
    cookies: dict[str, str],
) -> tuple[list[str], list[str]]:
    """分页获取收藏夹中所有文章的 URL 和标题

    :return: (url_list, title_list) 两个等长列表
    """
    collection_id = collection_id.replace("\n", "")
    logging.info(f"开始获取收藏夹 {collection_id} 的文章列表")

    offset = 0
    limit = 20

    article_nums = get_article_nums_of_collection(collection_id, headers, cookies)

    if article_nums is None or article_nums == 0:
        logging.warning(f"收藏夹 {collection_id} 没有文章或获取失败")
        return [], []

    url_list: list[str] = []
    title_list: list[str] = []
    while offset < article_nums:
        collection_url = (
            f"https://www.zhihu.com/api/v4/collections/{collection_id}/items"
            f"?offset={offset}&limit={limit}"
        )
        try:
            logging.info(f"请求收藏夹API: offset={offset}, limit={limit}")
            html = requests.get(
                collection_url, headers=headers, cookies=cookies, timeout=30
            )
            html.raise_for_status()
            content = html.json()
            logging.info(f"成功获取 {len(content.get('data', []))} 个项目")
        except Exception as e:
            logging.error(f"请求收藏夹API失败: {str(e)}")
            return url_list, title_list

        for el in content.get("data", []):
            try:
                url_list.append(el["content"]["url"])
                if el["content"]["type"] == "answer":
                    title_list.append(el["content"]["question"]["title"])
                else:
                    title_list.append(el["content"]["title"])
                logging.debug(f"添加文章: {el['content'].get('title', '未知标题')}")
            except Exception as e:
                logging.warning(f"解析文章项目失败: {str(e)}")
                print("********")
                print("TBD 非回答, 非专栏, 想法类收藏暂时无法处理")
                for k, v in el["content"].items():
                    if k in ["type", "url"]:
                        print(k, v)
                print("********")
                if len(url_list) > len(title_list):
                    url_list.pop()

        offset += limit

    logging.info(
        f"收藏夹 {collection_id} 总共获取到 {len(url_list)} 个有效文章"
    )
    return url_list, title_list


def process_single_collection(
    collection_name: str,
    collection_url: str,
    context: ExportContext,
) -> None:
    """处理单个收藏夹：获取文章列表 → 逐篇下载 → 转换 Markdown → 保存

    :param collection_name: 收藏夹名称
    :param collection_url: 收藏夹 URL
    :param context: 导出上下文（headers、cookies、输出路径等）
    """
    logging.info(f"开始处理收藏夹: {collection_name}")
    logging.info(f"收藏夹URL: {collection_url}")
    flush_logs()

    try:
        collection_id = collection_url.split("?")[0].split("/")[-1]
        logging.info(f"解析得到收藏夹ID: {collection_id}")
        flush_logs()

        urls, titles = get_article_urls_in_collection(
            collection_id, context.headers, context.cookies
        )

        if not urls:
            logging.warning(f"收藏夹 '{collection_name}' 没有获取到任何文章")
            flush_logs()
            return

    except Exception as e:
        logging.error(f"处理收藏夹 '{collection_name}' 时发生错误: {str(e)}")
        flush_logs()
        return

    collection_log: dict[str, Any] = {
        "name": collection_name,
        "url": collection_url,
        "list": [],
    }

    if len(urls) != len(titles):
        error_msg = (
            f"地址标题列表长度不一致: urls={len(urls)}, titles={len(titles)}"
        )
        logging.error(error_msg)
        flush_logs()
        context.processing_log.append(collection_log)
        return

    print(f"收藏夹 '{collection_name}' 共获取 {len(urls)} 篇可导出回答或专栏")

    downloadDir = get_output_path(collection_name, context.base_output_path)
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)

    for i in tqdm(range(len(urls)), desc=f"处理 {collection_name}"):
        content = None
        url = urls[i]
        title = titles[i]

        file_path = get_unique_filename(downloadDir, title, url)

        article_log: dict[str, Any] = {"name": title, "url": url, "status": ""}

        if is_article_already_downloaded(file_path, url):
            article_log["status"] = "文章已存在,跳过下载"
            collection_log["list"].append(article_log)
            continue

        try:
            logging.info(f"开始下载文章: {title}")
            flush_logs()

            if url.find("zhuanlan") != -1:
                content = get_single_post_content(
                    url,
                    context.headers,
                    context.cookies,
                    context.api_headers,
                    context.base_output_path,
                )
            else:
                content = get_single_answer_content(
                    url,
                    context.headers,
                    context.cookies,
                    context.api_headers,
                    context.base_output_path,
                )

            if content == -1:
                article_log["status"] = "文章下载失败, 原因:获取内容失败"
                collection_log["list"].append(article_log)
                logging.warning(f"获取内容失败: {url}")
                flush_logs()
                continue

            markdown_fmt = context.markdown_format
            md = markdownify(
                content,
                collection_name,
                context,
                format=markdown_fmt,
                heading_style="ATX",
            )
            md = "> %s\n\n" % url + md

            with open(file_path, "w", encoding="utf-8") as md_file:
                md_file.write(md)

            article_log["status"] = "文章不存在,正常下载"
            collection_log["list"].append(article_log)
            logging.info(f"文章下载成功: {title}")
            flush_logs()

            time.sleep(random.randint(1, 5))

        except Exception as e:
            article_log["status"] = f"文章下载失败, 原因:{str(e)}"
            collection_log["list"].append(article_log)
            logging.error(f"下载文章时发生错误: {title}")
            logging.error(f"错误详情: {str(e)}")
            logging.error(f"URL: {url}")
            flush_logs()

    context.processing_log.append(collection_log)
    print(f"收藏夹 '{collection_name}' 下载完毕")


def remove_articles_from_collection(
    collection_url: str, article_urls: list[str]
) -> list[tuple[bool, str, str]]:
    """批量从收藏夹中移除多篇文章

    :return: [(success, message, url), ...]
    """
    from zhihu_collections.favorite_ops import remove_from_collection

    results: list[tuple[bool, str, str]] = []
    for url in article_urls:
        success, msg = remove_from_collection(collection_url, url)
        results.append((success, msg, url))
        time.sleep(random.uniform(0.5, 1.5))
    return results
