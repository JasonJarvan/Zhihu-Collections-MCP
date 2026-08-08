# -*- coding:utf-8 -*-
"""
验证重构后的代码结构测试（v3.0）
"""
import sys
import os


def test_imports():
    """测试新模块导入"""
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
    functions = [
        list_collections, export_single_collection, get_collection_info,
        search_collections, add_article_to_collection,
        remove_article_from_collection, move_article_between_collections,
        resolve_output_path,
    ]
    for func in functions:
        assert callable(func)

    from zhihu_collections.cli import build_parser, COMMAND_HANDLERS
    assert callable(build_parser)
    assert isinstance(COMMAND_HANDLERS, dict)

    from zhihu_collections.fetch_collections import (
        get_collections_from_page,
        get_all_collections,
        update_config_with_collections,
    )
    assert callable(get_collections_from_page)

    from zhihu_collections.main import main
    assert callable(main)


def test_file_structure():
    """测试文件结构"""
    print("\n=== 测试文件结构 ===")

    src_dir = "src/zhihu_collections"
    expected_files = [
        f"{src_dir}/_operations.py",
        f"{src_dir}/cli.py",
        f"{src_dir}/mcp_server.py",
        f"{src_dir}/favorite_ops.py",
        f"{src_dir}/fetch_collections.py",
        f"{src_dir}/main.py",
        f"{src_dir}/__init__.py",
        f"{src_dir}/_common.py",
        f"{src_dir}/_logging.py",
        f"{src_dir}/_headers.py",
        f"{src_dir}/_paths.py",
        f"{src_dir}/_converter.py",
        f"{src_dir}/_content.py",
        f"{src_dir}/_collection.py",
        f"{src_dir}/_export.py",
        f"{src_dir}/utils.py",
    ]

    all_exist = True
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False

    # 确认已删除的模块不存在
    removed_files = [
        f"{src_dir}/get_collections.py",
        f"{src_dir}/export_all.py",
    ]
    for file_path in removed_files:
        if not os.path.exists(file_path):
            print(f"✓ {file_path} 已删除")
        else:
            print(f"✗ {file_path} 应该已删除但还存在")
            all_exist = False

    # 确认 scripts 目录存在
    moved_files = [
        "scripts/debug_page.py",
        "scripts/analyze_issue.py",
    ]
    for file_path in moved_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} 已移至 scripts/")
        else:
            print(f"✗ {file_path} 不存在")

    assert all_exist


def test_cli_subcommands():
    """验证 CLI 子命令完整性"""
    print("\n=== 测试 CLI 子命令完整性 ===")

    from zhihu_collections.cli import build_parser, COMMAND_HANDLERS

    import argparse
    parser = build_parser()
    sub_action = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
    subcommands = sub_action[0]._name_parser_map

    expected_commands = {
        "list", "export", "export-all", "info", "search",
        "add", "remove", "move", "fetch",
    }

    actual_commands = set(subcommands.keys())
    assert actual_commands == expected_commands, f"子命令不匹配: {actual_commands ^ expected_commands}"
    assert set(COMMAND_HANDLERS.keys()) == expected_commands, "COMMAND_HANDLERS 覆盖不完整"


def main():
    """主测试函数（独立运行用）"""
    print("开始验证 v3.0 重构后的代码结构...")
    # 这些函数现在用 assert，pytest 会自动捕获
    test_imports()
    test_file_structure()
    test_cli_subcommands()
    print("所有验证通过!")


if __name__ == "__main__":
    main()
