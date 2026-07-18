# -*- coding:utf-8 -*-
"""知乎收藏夹导出 — 命令行入口"""
import argparse
import sys
from zhihu_collections._common import load_config, resolve_base_output_path
from zhihu_collections._logging import setup_debug_logging, reconfigure_logging
from zhihu_collections._export import create_export_context, save_processing_log
from zhihu_collections._collection import process_single_collection


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="zhihu-export",
        description="将知乎收藏夹批量导出为 Markdown 文件",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        metavar="PATH",
        help="输出目录(覆盖 config.json 中的 outputPath),支持 ~ 展开与绝对/相对路径",
    )
    return parser


def main() -> None:
    """主入口：加载配置 → 遍历收藏夹 → 批量导出 Markdown"""
    args = build_arg_parser().parse_args()

    config = load_config()

    base_output_path, source = resolve_base_output_path(args.output_path, config)

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

    open_collection_mode = config.get("openCollection", False)
    if open_collection_mode:
        print("检测到openCollection模式已启用")
        print("请先运行 zhihu-fetch 获取收藏夹列表")
        print("然后将config.json中的openCollection设为false，重新运行此程序")
        sys.exit(1)

    zhihu_collections = config.get("zhihuUrls", [])
    if not zhihu_collections:
        print("没有找到要处理的收藏夹配置")
        print("提示：请运行 zhihu-fetch 自动获取收藏夹列表")
        sys.exit(1)

    markdown_fmt = config.get("markdownFormat", "obsidian")
    print(
        f"Markdown 格式: {markdown_fmt} "
        f"({'Obsidian wiki-link' if markdown_fmt == 'obsidian' else '标准格式'})"
    )
    print(f"共找到 {len(zhihu_collections)} 个收藏夹待处理")

    context = create_export_context(
        config=config, base_output_path=base_output_path
    )

    for collection in zhihu_collections:
        collection_name = collection.get("name", "未命名收藏夹")
        collection_url = collection.get("url", "")

        if not collection_url:
            print(f"收藏夹 '{collection_name}' 缺少URL，跳过")
            continue

        print(f"\n开始处理收藏夹: {collection_name}")
        process_single_collection(collection_name, collection_url, context)

    print("\n所有收藏夹处理完毕!")
    save_processing_log(context.processing_log, context.base_output_path)


if __name__ == "__main__":
    main()
