"""测试向后兼容入口 main.py 和别名函数"""

import argparse
from unittest import mock


class TestMainModule:
    def test_main_imports(self):
        from zhihu_collections.main import main
        assert callable(main)


class TestExportAllMain:
    def test_export_all_main_exists(self):
        from zhihu_collections.cli import export_all_main
        assert callable(export_all_main)

    def test_export_all_main_with_output_flag(self):
        with mock.patch(
            "zhihu_collections.cli._cmd_export_all"
        ) as mock_handler:
            from zhihu_collections.cli import export_all_main
            export_all_main()

            mock_handler.assert_called_once()
            args = mock_handler.call_args[0][0]
            assert isinstance(args, argparse.Namespace)


class TestFetchMain:
    def test_fetch_main_exists(self):
        from zhihu_collections.cli import fetch_main
        assert callable(fetch_main)

    def test_fetch_main_calls_fetch_impl(self):
        with mock.patch(
            "zhihu_collections.cli.fetch_main_impl"
        ) as mock_impl:
            from zhihu_collections.cli import fetch_main
            fetch_main()
            mock_impl.assert_called_once()
