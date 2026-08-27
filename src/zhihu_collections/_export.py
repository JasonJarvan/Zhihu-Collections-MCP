# -*- coding:utf-8 -*-
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
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
        started_at: Optional[float] = None,
    ) -> None:
        self.base_output_path = base_output_path
        self.headers = headers
        self.api_headers = api_headers
        self.cookies = cookies
        self.markdown_format = markdown_format
        # 整个导出会话的开始时间(单调钟),main() 会覆盖
        self.started_at: float = started_at if started_at is not None else 0.0
        self.processing_log: list[dict[str, Any]] = []


def create_export_context(
    config: Optional[dict[str, Any]] = None,
    base_output_path: Optional[str] = None,
    started_at: Optional[float] = None,
) -> ExportContext:
    """工厂函数：从配置构建 ExportContext

    :param config: 配置字典，不传则自动加载 config.json
    :param base_output_path: 基础输出路径
    :param started_at: 导出会话开始时间(单调钟秒数)
    """
    if config is None:
        config = load_config()

    return ExportContext(
        base_output_path=base_output_path,
        headers=build_page_headers(),
        api_headers=build_api_headers(),
        cookies=load_cookies(),
        markdown_format=config.get("markdownFormat", "obsidian"),
        started_at=started_at,
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


# 状态文本中包含的关键字(用于从 article_log["status"] 反向聚合)
_STATUS_EXISTING = "已存在"
_STATUS_DOWNLOADED = "正常下载"
_STATUS_FAILED = "下载失败"


def _format_duration(seconds: float) -> str:
    """把秒数格式化为人类可读的字符串,例如 1m 23s / 2h 5m"""
    if seconds < 0:
        return "0s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    total_secs = int(seconds)
    minutes, secs = divmod(total_secs, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s"


def _classify_collection(total: int, downloaded: int, existing: int, failed: int) -> str:
    """根据文章统计判定收藏夹级状态"""
    if total == 0:
        return "空"
    if failed == 0:
        return "成功"
    if downloaded == 0 and existing == 0:
        return "失败"
    return "部分成功"


def summarize_export(
    processing_log: list[dict[str, Any]],
    base_output_path: Optional[str],
    started_at: float,
    finished_at: float,
) -> dict[str, Any]:
    """汇总整个导出过程的统计信息并打印到终端

    :return: 结构化汇总字典,供 save_summary 持久化
    """
    duration = max(0.0, finished_at - started_at)

    cols_total = len(processing_log)
    cols_ok = 0
    cols_failed = 0
    cols_empty = 0

    arts_total = 0
    arts_existing = 0
    arts_downloaded = 0
    arts_failed = 0

    by_collection: list[dict[str, Any]] = []

    for col in processing_log:
        items = col.get("list") or []
        existing = 0
        downloaded = 0
        failed = 0
        for item in items:
            status = item.get("status", "")
            if _STATUS_EXISTING in status:
                existing += 1
            elif _STATUS_DOWNLOADED in status:
                downloaded += 1
            elif _STATUS_FAILED in status:
                failed += 1
        total = len(items)

        if total == 0:
            cols_empty += 1
        status_label = _classify_collection(total, downloaded, existing, failed)
        if status_label == "成功" or status_label == "部分成功":
            cols_ok += 1
        elif status_label == "失败":
            cols_failed += 1

        arts_total += total
        arts_existing += existing
        arts_downloaded += downloaded
        arts_failed += failed

        by_collection.append(
            {
                "name": col.get("name", "未命名"),
                "url": col.get("url", ""),
                "total": total,
                "downloaded": downloaded,
                "existing": existing,
                "failed": failed,
                "status": status_label,
            }
        )

    output_root = (
        str(base_output_path)
        if base_output_path
        else os.path.join(os.getcwd(), "downloads")
    )

    summary: dict[str, Any] = {
        "duration_seconds": round(duration, 2),
        "duration_human": _format_duration(duration),
        "started_at": (
            datetime.fromtimestamp(started_at, tz=timezone.utc).isoformat()
            if started_at
            else None
        ),
        "finished_at": (
            datetime.fromtimestamp(finished_at, tz=timezone.utc).isoformat()
            if finished_at
            else None
        ),
        "output_path": output_root,
        "collections": {
            "total": cols_total,
            "ok": cols_ok,
            "failed": cols_failed,
            "empty": cols_empty,
        },
        "articles": {
            "total": arts_total,
            "downloaded": arts_downloaded,
            "existing": arts_existing,
            "failed": arts_failed,
        },
        "by_collection": by_collection,
    }

    _print_summary(summary)
    return summary


def _print_summary(summary: dict[str, Any]) -> None:
    """把汇总信息打印到终端"""
    cols = summary["collections"]
    arts = summary["articles"]
    width = 60
    print()
    print("=" * width)
    print("导出汇总")
    print("=" * width)
    print(f"  耗时        : {summary['duration_human']} ({summary['duration_seconds']}s)")
    print(f"  输出根目录  : {summary['output_path']}")
    print()
    print(
        f"  收藏夹      : 总 {cols['total']} | 成功 {cols['ok']}"
        f" | 失败 {cols['failed']} | 空 {cols['empty']}"
    )
    print(
        f"  文章        : 总 {arts['total']} | 新下载 {arts['downloaded']}"
        f" | 已存在跳过 {arts['existing']} | 失败 {arts['failed']}"
    )
    if summary["by_collection"]:
        print()
        print("  -- 详情 --")
        for col in summary["by_collection"]:
            name = col["name"]
            if len(name) > 28:
                name = name[:25] + "..."
            print(
                f"    [{col['status']}] {name:<28} "
                f"新 {col['downloaded']} / 跳 {col['existing']}"
                f" / 败 {col['failed']} / 共 {col['total']}"
            )
    print("=" * width)


def save_summary(summary: dict[str, Any], base_output_path: Optional[str]) -> None:
    """把汇总信息单独保存为 logs/summary_{timestamp}.json(与 processing_log 并列)"""
    logs_dir = get_logs_path(base_output_path)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(logs_dir, f"summary_{timestamp}.json")

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"汇总报告已保存到: {log_path}")
