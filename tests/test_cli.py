"""测试统一 CLI 参数解析和子命令路由"""

import argparse
import pytest

from zhihu_collections.cli import build_parser, COMMAND_HANDLERS


class TestBuildParser:
    def test_all_subcommands_exist(self):
        parser = build_parser()
        sub_action = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
        assert len(sub_action) > 0
        subcommands = set(sub_action[0]._name_parser_map.keys())

        expected = {"list", "export", "export-all", "info", "search", "add", "remove", "move", "fetch"}
        assert subcommands == expected

    def test_export_subcommand_has_required_args(self):
        parser = build_parser()
        args = parser.parse_args(["export", "https://www.zhihu.com/collection/123"])
        assert args.command == "export"
        assert args.collection_url == "https://www.zhihu.com/collection/123"

    def test_export_subcommand_with_options(self):
        parser = build_parser()
        args = parser.parse_args([
            "export",
            "https://www.zhihu.com/collection/123",
            "--name", "MyCollection",
            "--output", "/tmp/out",
            "--overwrite",
            "--max-articles", "10",
        ])
        assert args.name == "MyCollection"
        assert args.output == "/tmp/out"
        assert args.overwrite is True
        assert args.max_articles == 10

    def test_export_all_has_output_option(self):
        parser = build_parser()
        args = parser.parse_args(["export-all", "-o", "/tmp/test"])
        assert args.output == "/tmp/test"

    def test_export_all_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["export-all"])
        assert args.output is None

    def test_info_has_url_arg(self):
        parser = build_parser()
        args = parser.parse_args(["info", "https://www.zhihu.com/collection/123"])
        assert args.collection_url == "https://www.zhihu.com/collection/123"

    def test_info_missing_url(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["info"])

    def test_search_has_keyword_arg(self):
        parser = build_parser()
        args = parser.parse_args(["search", "Python"])
        assert args.keyword == "Python"

    def test_add_has_two_args(self):
        parser = build_parser()
        args = parser.parse_args([
            "add",
            "https://www.zhihu.com/collection/123",
            "https://www.zhihu.com/question/1/answer/456",
        ])
        assert args.collection_url == "https://www.zhihu.com/collection/123"
        assert args.article_url == "https://www.zhihu.com/question/1/answer/456"

    def test_add_missing_article_url(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["add", "https://www.zhihu.com/collection/123"])

    def test_remove_has_two_args(self):
        parser = build_parser()
        args = parser.parse_args([
            "remove",
            "https://www.zhihu.com/collection/123",
            "https://zhuanlan.zhihu.com/p/999",
        ])
        assert args.collection_url == "https://www.zhihu.com/collection/123"
        assert args.article_url == "https://zhuanlan.zhihu.com/p/999"

    def test_move_has_three_args(self):
        parser = build_parser()
        args = parser.parse_args([
            "move",
            "https://www.zhihu.com/collection/111",
            "https://www.zhihu.com/collection/222",
            "https://www.zhihu.com/question/1/answer/456",
        ])
        assert args.from_collection_url == "https://www.zhihu.com/collection/111"
        assert args.to_collection_url == "https://www.zhihu.com/collection/222"
        assert args.article_url == "https://www.zhihu.com/question/1/answer/456"

    def test_move_missing_args(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["move", "https://www.zhihu.com/collection/111"])

    def test_fetch_no_args_required(self):
        parser = build_parser()
        args = parser.parse_args(["fetch"])
        assert args.command == "fetch"

    def test_list_no_args_required(self):
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_no_command_shows_help(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestCommandHandlers:
    def test_all_commands_have_handler(self):
        expected = {"list", "export", "export-all", "info", "search", "add", "remove", "move", "fetch"}
        assert set(COMMAND_HANDLERS.keys()) == expected

    def test_handlers_are_callable(self):
        for name, handler in COMMAND_HANDLERS.items():
            assert callable(handler), f"{name} handler is not callable"
