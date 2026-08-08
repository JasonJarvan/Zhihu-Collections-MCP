# -*- coding:utf-8 -*-
"""知乎收藏夹导出 — 命令行批量导出（向后兼容模块）

从 v3.0 起，主要 CLI 入口已迁移至 zhihu_collections.cli。
此模块保留用于程序化导入场景，调用 cli 中的统一流程。
"""

from __future__ import annotations

import sys

from zhihu_collections.cli import _cmd_export_all


def main() -> None:
    """旧版批量导出入口 — 等效于 zhihu export-all"""
    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-o", "--output", dest="output_path", default=None)
    known_args, _ = parser.parse_known_args()

    args = argparse.Namespace(output=known_args.output_path)
    _cmd_export_all(args)


if __name__ == "__main__":
    main()
