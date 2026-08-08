# -*- coding:utf-8 -*-
"""共享业务逻辑层 — CLI 和 MCP Server 共用"""

from __future__ import annotations

import os
from typing import Optional

from zhihu_collections._common import load_config, load_cookies, parse_output_path
from zhihu_collections._headers import build_page_headers, build_api_headers
from zhihu_collections._paths import get_output_path
from zhihu_collections._export import create_export_context
from zhihu_collections._collection import (
    process_single_collection,
    get_article_urls_in_collection,
)
from zhihu_collections import favorite_ops


def resolve_output_path(
    output_dir: str = "",
    config: dict | None = None,
) -> Optional[str]:
    """按优先级解析输出路径

    优先级: output_dir 参数 > ZHIHU_OUTPUT_PATH 环境变量 > config.json outputPath > downloads/

    :return: 解析后的绝对路径字符串，或 None
    """
    if config is None:
        config = load_config()

    if output_dir:
        p = parse_output_path(output_dir, config.get("os", ""))
        return str(p) if p else None

    env_path = os.environ.get("ZHIHU_OUTPUT_PATH")
    if env_path:
        p = parse_output_path(env_path, config.get("os", ""))
        return str(p) if p else None

    if config.get("outputPath"):
        p = parse_output_path(config["outputPath"], config.get("os", ""))
        return str(p) if p else None

    return None


# ── list_collections ──


def list_collections() -> list[dict]:
    """列出配置文件中所有收藏夹

    :return: 收藏夹列表 [{"name": ..., "url": ...}, ...]
    """
    config = load_config()
    return config.get("zhihuUrls", [])


# ── export_collection ──


def export_single_collection(
    collection_url: str,
    collection_name: str = "",
    output_dir: str = "",
    overwrite: bool = False,
    max_articles: Optional[int] = None,
    config: dict | None = None,
) -> str:
    """导出单个收藏夹为 Markdown

    :param collection_url: 收藏夹 URL
    :param collection_name: 收藏夹名称（可选，用于命名输出目录）
    :param output_dir: 输出目录（可选）
    :param overwrite: 是否覆盖不完整文件（重新补全）
    :param max_articles: 只导出最新 N 篇文章
    :param config: 配置字典（不传则自动加载）
    :return: 结果消息
    """
    if config is None:
        config = load_config()

    if not collection_name:
        collection_id_from_url = collection_url.split("?")[0].split("/")[-1]
        collection_name = f"收藏夹_{collection_id_from_url}"

    output_path = resolve_output_path(output_dir, config)

    result_parts = [
        f"导出收藏夹：{collection_name}",
        f"URL: {collection_url}",
        f"输出目录: {get_output_path(collection_name, output_path)}",
    ]

    if overwrite:
        dir_path = get_output_path(collection_name, output_path)
        removed_count = 0
        if os.path.exists(dir_path):
            for fname in os.listdir(dir_path):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(dir_path, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        lines = fh.readlines()
                    if len(lines) < 5:
                        os.remove(fpath)
                        removed_count += 1
                except Exception:
                    pass
        result_parts.append(f"删除了 {removed_count} 个不完整文件，准备重新下载")

    try:
        context = create_export_context(config=config, base_output_path=output_path)
        process_single_collection(
            collection_name, collection_url, context, max_articles=max_articles
        )
        result_parts.append("导出完成！")
    except Exception as e:
        result_parts.append(f"导出失败: {str(e)}")

    return "\n".join(result_parts)


# ── get_collection_info ──


def get_collection_info(collection_url: str) -> str:
    """获取指定收藏夹的基本信息（文章数量等）

    :param collection_url: 收藏夹 URL
    :return: 信息文本
    """
    collection_id = collection_url.split("?")[0].split("/")[-1]
    urls, titles = get_article_urls_in_collection(
        collection_id,
        build_page_headers(),
        load_cookies(),
    )

    lines = [
        f"收藏夹ID: {collection_id}",
        f"文章数量: {len(urls)}",
    ]

    if titles:
        lines.append("文章标题（前5个）：")
        for i, title in enumerate(titles[:5], 1):
            lines.append(f"  {i}. {title}")
        if len(titles) > 5:
            lines.append(f"  ... 还有 {len(titles) - 5} 篇")

    return "\n".join(lines)


# ── search_collections ──


def search_collections(keyword: str) -> list[dict]:
    """在配置文件的收藏夹中搜索关键词

    :param keyword: 搜索关键词（大小写不敏感）
    :return: 匹配的收藏夹列表
    """
    config = load_config()
    collections = config.get("zhihuUrls", [])

    return [
        c
        for c in collections
        if keyword.lower() in c.get("name", "").lower()
        or keyword.lower() in c.get("url", "").lower()
    ]


# ── 收藏管理 ──


def add_article_to_collection(collection_url: str, article_url: str) -> tuple[bool, str]:
    """收藏一篇文章到指定收藏夹

    :return: (success, message)
    """
    return favorite_ops.add_to_collection(collection_url, article_url)


def remove_article_from_collection(
    collection_url: str, article_url: str
) -> tuple[bool, str]:
    """从收藏夹取消收藏一篇文章

    :return: (success, message)
    """
    return favorite_ops.remove_from_collection(collection_url, article_url)


def move_article_between_collections(
    from_collection_url: str,
    to_collection_url: str,
    article_url: str,
) -> tuple[bool, str]:
    """将文章从一个收藏夹移动到另一个

    :return: (success, message)
    """
    return favorite_ops.move_to_collection(
        from_collection_url, to_collection_url, article_url
    )
