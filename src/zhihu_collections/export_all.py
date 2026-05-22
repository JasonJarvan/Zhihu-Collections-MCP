# -*- coding:utf-8 -*-
"""知乎收藏夹 — 批量导出入口（遍历所有收藏夹）"""
from zhihu_collections._common import load_config, parse_output_path
from zhihu_collections._export import create_export_context
from zhihu_collections._collection import process_single_collection


def main() -> None:
    """批量导出 config.json 中所有收藏夹"""
    config = load_config()
    base_output_path = None
    if config.get("outputPath"):
        base_output_path = str(
            parse_output_path(config["outputPath"], config.get("os", ""))
        )

    context = create_export_context(
        config=config, base_output_path=base_output_path
    )

    for c in config["zhihuUrls"]:
        print(f"========== {c['name']} ==========")
        process_single_collection(c["name"], c["url"], context)

    print("ALL DONE")


if __name__ == "__main__":
    main()
