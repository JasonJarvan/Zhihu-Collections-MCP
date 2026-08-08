# -*- coding:utf-8 -*-
"""统一 CLI 入口 — 所有功能都通过子命令暴露"""

from __future__ import annotations

import argparse
import sys
import time

from zhihu_collections._common import load_config, resolve_base_output_path
from zhihu_collections._logging import setup_debug_logging, reconfigure_logging
from zhihu_collections._export import (
    create_export_context,
    save_processing_log,
    save_summary,
    summarize_export,
)
from zhihu_collections._collection import process_single_collection
from zhihu_collections._operations import (
    list_collections,
    export_single_collection,
    get_collection_info,
    search_collections,
    add_article_to_collection,
    remove_article_from_collection,
    move_article_between_collections,
    resolve_output_path,
)
from zhihu_collections.fetch_collections import main as fetch_main_impl


def _cmd_list(_args: argparse.Namespace) -> None:
    """列出所有收藏夹"""
    collections = list_collections()
    if not collections:
        print("未找到配置的收藏夹，请在 config.json 中添加收藏夹信息")
        return

    print("已配置的收藏夹列表：\n")
    for i, coll in enumerate(collections, 1):
        name = coll.get("name", "未命名")
        url = coll.get("url", "")
        print(f"{i}. {name}")
        print(f"   URL: {url}\n")


def _cmd_export(args: argparse.Namespace) -> None:
    """导出一个收藏夹"""
    result = export_single_collection(
        collection_url=args.collection_url,
        collection_name=args.name or "",
        output_dir=args.output or "",
        overwrite=args.overwrite,
        max_articles=args.max_articles,
    )
    # 模拟 MCP 风格的输出格式
    emoji_result = result.replace("导出收藏夹", "🚀 导出收藏夹").replace("导出完成", "✅ 导出完成").replace("导出失败", "❌ 导出失败")
    print(emoji_result)


def _cmd_export_all(args: argparse.Namespace) -> None:
    """批量导出 config.json 中所有收藏夹"""
    config = load_config()

    base_output_path, source = resolve_base_output_path(args.output, config)

    if base_output_path:
        print(f"使用{source}输出路径: {base_output_path}")
        reconfigure_logging(base_output_path)
    else:
        if source != "默认":
            print(f"{source}指定的输出路径解析失败，使用默认路径")
        else:
            print("使用默认输出路径: downloads/")
        base_output_path = None

    setup_debug_logging()

    zhihu_collections = config.get("zhihuUrls", [])
    if not zhihu_collections:
        print("没有找到要处理的收藏夹配置")
        print("提示：请运行 zhihu fetch 自动获取收藏夹列表")
        sys.exit(1)

    markdown_fmt = config.get("markdownFormat", "obsidian")
    print(
        f"Markdown 格式: {markdown_fmt} "
        f"({'Obsidian wiki-link' if markdown_fmt == 'obsidian' else '标准格式'})"
    )
    print(f"共找到 {len(zhihu_collections)} 个收藏夹待处理")

    started_at = time.monotonic()
    context = create_export_context(
        config=config,
        base_output_path=str(base_output_path) if base_output_path else None,
        started_at=started_at,
    )

    for collection in zhihu_collections:
        collection_name = collection.get("name", "未命名收藏夹")
        collection_url = collection.get("url", "")

        if not collection_url:
            print(f"收藏夹 '{collection_name}' 缺少URL，跳过")
            continue

        print(f"\n开始处理收藏夹: {collection_name}")
        process_single_collection(collection_name, collection_url, context)

    finished_at = time.monotonic()
    print("\n所有收藏夹处理完毕!")
    save_processing_log(context.processing_log, context.base_output_path)

    summary = summarize_export(
        context.processing_log,
        context.base_output_path,
        started_at,
        finished_at,
    )
    save_summary(summary, context.base_output_path)


def _cmd_info(args: argparse.Namespace) -> None:
    """获取收藏夹信息"""
    try:
        result = get_collection_info(args.collection_url)
        print(result)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


def _cmd_search(args: argparse.Namespace) -> None:
    """搜索收藏夹"""
    if not args.keyword:
        print("错误: 需要提供搜索关键词")
        sys.exit(1)

    matched = search_collections(args.keyword)
    if not matched:
        print(f"没有找到包含 '{args.keyword}' 的收藏夹")
        return

    print(f"搜索结果（关键词：{args.keyword}）：\n")
    for i, coll in enumerate(matched, 1):
        name = coll.get("name", "未命名")
        url = coll.get("url", "")
        print(f"{i}. {name}")
        print(f"   URL: {url}\n")


def _cmd_add(args: argparse.Namespace) -> None:
    """收藏一篇文章"""
    success, msg = add_article_to_collection(
        collection_url=args.collection_url,
        article_url=args.article_url,
    )
    print(msg)
    if not success:
        sys.exit(1)


def _cmd_remove(args: argparse.Namespace) -> None:
    """取消收藏一篇文章"""
    success, msg = remove_article_from_collection(
        collection_url=args.collection_url,
        article_url=args.article_url,
    )
    print(msg)
    if not success:
        sys.exit(1)


def _cmd_move(args: argparse.Namespace) -> None:
    """移动一篇文章"""
    success, msg = move_article_between_collections(
        from_collection_url=args.from_collection_url,
        to_collection_url=args.to_collection_url,
        article_url=args.article_url,
    )
    print(msg)
    if not success:
        sys.exit(1)


def _cmd_fetch(args: argparse.Namespace) -> None:
    """自动获取收藏夹列表"""
    fetch_main_impl()


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="zhihu",
        description="知乎收藏夹管理工具 — CLI 与 MCP 共享同一业务层",
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    # zhihu list
    p_list = sub.add_parser("list", help="列出所有收藏夹")

    # zhihu export <url>
    p_export = sub.add_parser("export", help="导出单个收藏夹")
    p_export.add_argument("collection_url", help="收藏夹URL，如 https://www.zhihu.com/collection/123456789")
    p_export.add_argument("--name", "-n", help="收藏夹名称（用于命名输出目录）")
    p_export.add_argument("--output", "-o", metavar="PATH", help="输出目录路径")
    p_export.add_argument("--overwrite", action="store_true", help="覆盖不完整文件")
    p_export.add_argument("--max-articles", type=int, metavar="N", help="只导出最新N篇文章")

    # zhihu export-all
    p_export_all = sub.add_parser("export-all", help="批量导出 config.json 中所有收藏夹")
    p_export_all.add_argument("--output", "-o", metavar="PATH", help="输出目录路径 (覆盖 config.json)")

    # zhihu info <url>
    p_info = sub.add_parser("info", help="获取收藏夹信息")
    p_info.add_argument("collection_url", help="收藏夹URL")

    # zhihu search <keyword>
    p_search = sub.add_parser("search", help="搜索收藏夹")
    p_search.add_argument("keyword", help="搜索关键词")

    # zhihu add <collection_url> <article_url>
    p_add = sub.add_parser("add", help="收藏一篇文章")
    p_add.add_argument("collection_url", help="目标收藏夹URL")
    p_add.add_argument("article_url", help="要收藏的文章URL")

    # zhihu remove <collection_url> <article_url>
    p_remove = sub.add_parser("remove", help="取消收藏一篇文章")
    p_remove.add_argument("collection_url", help="收藏夹URL")
    p_remove.add_argument("article_url", help="要取消收藏的文章URL")

    # zhihu move <from_url> <to_url> <article_url>
    p_move = sub.add_parser("move", help="移动一篇文章到另一个收藏夹")
    p_move.add_argument("from_collection_url", help="源收藏夹URL")
    p_move.add_argument("to_collection_url", help="目标收藏夹URL")
    p_move.add_argument("article_url", help="要移动的文章URL")

    # zhihu fetch
    p_fetch = sub.add_parser("fetch", help="自动获取收藏夹列表并写入 config.json")

    return parser


COMMAND_HANDLERS = {
    "list": _cmd_list,
    "export": _cmd_export,
    "export-all": _cmd_export_all,
    "info": _cmd_info,
    "search": _cmd_search,
    "add": _cmd_add,
    "remove": _cmd_remove,
    "move": _cmd_move,
    "fetch": _cmd_fetch,
}


def main() -> None:
    """CLI 主入口"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    handler = COMMAND_HANDLERS.get(args.command)
    if handler:
        handler(args)


# 向后兼容的别名函数
def export_all_main() -> None:
    """zhihu export-all（旧 zhihu-export 入口）"""
    # 模拟从 sys.argv 中提取 --output
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-o", "--output", dest="output_path", default=None)
    known_args, _ = parser.parse_known_args()

    args = argparse.Namespace(output=known_args.output_path)
    _cmd_export_all(args)


def fetch_main() -> None:
    """zhihu fetch（旧 zhihu-fetch 入口）"""
    _cmd_fetch(None)


if __name__ == "__main__":
    main()
