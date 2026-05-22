# -*- coding:utf-8 -*-
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Optional, Any

from zhihu_collections._paths import get_logs_path
from zhihu_collections._headers import build_page_headers, build_api_headers
from zhihu_collections._common import load_config, load_cookies
from zhihu_collections.utils import filter_title_str


class ExportContext:
    """导出上下文，聚合一次导出操作所需的所有配置和状态"""

    def __init__(
        self,
        base_output_path: Optional[str],
        headers: dict[str, str],
        api_headers: dict[str, str],
        cookies: dict[str, str],
        markdown_format: str,
    ) -> None:
        self.base_output_path = base_output_path
        self.headers = headers
        self.api_headers = api_headers
        self.cookies = cookies
        self.markdown_format = markdown_format
        self.processing_log: list[dict[str, Any]] = []


def create_export_context(
    config: Optional[dict[str, Any]] = None,
    base_output_path: Optional[str] = None,
) -> ExportContext:
    """工厂函数：从配置构建 ExportContext

    :param config: 配置字典，不传则自动加载 config.json
    :param base_output_path: 基础输出路径
    """
    if config is None:
        config = load_config()

    return ExportContext(
        base_output_path=base_output_path,
        headers=build_page_headers(),
        api_headers=build_api_headers(),
        cookies=load_cookies(),
        markdown_format=config.get("markdownFormat", "obsidian"),
    )


def is_article_already_downloaded(file_path: str, target_url: str) -> bool:
    """检查 markdown 文件是否已存在且包含相同的目标 URL

    :param file_path: 要检查的 markdown 文件路径
    :param target_url: 目标 URL
    :return: True 如果文件存在且第一行引用块包含目标 URL
    """
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("> ") and target_url in first_line:
                return True
    except:
        pass

    return False


def get_unique_filename(base_dir: str, title: str, url: str) -> str:
    """生成唯一的文件名，标题重复时自动附加 URL ID 后缀

    :param base_dir: 基础目录
    :param title: 文章标题
    :param url: 文章 URL
    :return: 唯一的 .md 文件路径
    """
    base_filename = filter_title_str(title)
    file_path = os.path.join(base_dir, base_filename + ".md")

    if not os.path.exists(file_path):
        return file_path

    if is_article_already_downloaded(file_path, url):
        return file_path

    url_id = url.split("/")[-1]
    unique_filename = f"{base_filename}_{url_id}"
    return os.path.join(base_dir, unique_filename + ".md")


def save_processing_log(
    processing_log: list[dict[str, Any]], base_output_path: Optional[str]
) -> None:
    """保存处理日志到 logs 目录

    :param processing_log: 处理日志列表
    :param base_output_path: 基础输出路径
    """
    logs_dir = get_logs_path(base_output_path)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}.json"
    log_path = os.path.join(logs_dir, log_filename)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(processing_log, f, ensure_ascii=False, indent=2)

    print(f"处理日志已保存到: {log_path}")
