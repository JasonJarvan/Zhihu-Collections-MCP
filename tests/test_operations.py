"""测试共享业务逻辑层 _operations.py"""

import os
from unittest import mock

import pytest

from zhihu_collections._operations import (
    list_collections,
    search_collections,
    resolve_output_path,
    add_article_to_collection,
    remove_article_from_collection,
    move_article_between_collections,
)


# ── list_collections ──


class TestListCollections:
    def test_list_with_data(self, sample_config):
        with mock.patch("zhihu_collections._operations.load_config", return_value=sample_config):
            result = list_collections()
            assert len(result) == 1
            assert result[0]["name"] == "测试收藏夹"
            assert result[0]["url"] == "https://www.zhihu.com/collection/123456"

    def test_list_empty(self):
        with mock.patch("zhihu_collections._operations.load_config", return_value={"zhihuUrls": []}):
            result = list_collections()
            assert result == []

    def test_list_no_key(self):
        with mock.patch("zhihu_collections._operations.load_config", return_value={}):
            result = list_collections()
            assert result == []

    def test_list_multiple(self):
        config = {
            "zhihuUrls": [
                {"name": "A", "url": "https://www.zhihu.com/collection/1"},
                {"name": "B", "url": "https://www.zhihu.com/collection/2"},
                {"name": "C", "url": "https://www.zhihu.com/collection/3"},
            ]
        }
        with mock.patch("zhihu_collections._operations.load_config", return_value=config):
            result = list_collections()
            assert len(result) == 3


# ── search_collections ──


class TestSearchCollections:
    def test_search_by_name(self):
        config = {
            "zhihuUrls": [
                {"name": "Python学习", "url": "https://www.zhihu.com/collection/1"},
                {"name": "Java入门", "url": "https://www.zhihu.com/collection/2"},
            ]
        }
        with mock.patch("zhihu_collections._operations.load_config", return_value=config):
            result = search_collections("Python")
            assert len(result) == 1
            assert result[0]["name"] == "Python学习"

    def test_search_by_url(self):
        config = {
            "zhihuUrls": [
                {"name": "收藏夹A", "url": "https://www.zhihu.com/collection/123456"},
                {"name": "收藏夹B", "url": "https://www.zhihu.com/collection/python"},
            ]
        }
        with mock.patch("zhihu_collections._operations.load_config", return_value=config):
            result = search_collections("python")
            assert len(result) == 1
            assert result[0]["name"] == "收藏夹B"

    def test_search_case_insensitive(self):
        config = {
            "zhihuUrls": [
                {"name": "PyThOn", "url": "https://www.zhihu.com/collection/1"},
            ]
        }
        with mock.patch("zhihu_collections._operations.load_config", return_value=config):
            result = search_collections("python")
            assert len(result) == 1

    def test_search_no_match(self):
        config = {
            "zhihuUrls": [
                {"name": "Python", "url": "https://www.zhihu.com/collection/1"},
            ]
        }
        with mock.patch("zhihu_collections._operations.load_config", return_value=config):
            result = search_collections("不存在的关键词")
            assert result == []

    def test_search_empty_config(self):
        with mock.patch("zhihu_collections._operations.load_config", return_value={}):
            result = search_collections("anything")
            assert result == []


# ── resolve_output_path ──


class TestResolveOutputPath:
    def test_cli_arg_priority(self):
        config = {"outputPath": "/tmp/config_path", "os": "linux"}
        result = resolve_output_path("/tmp/cli_path", config)
        assert result is not None
        assert "cli_path" in result

    def test_env_var_priority(self, monkeypatch):
        monkeypatch.setenv("ZHIHU_OUTPUT_PATH", "/tmp/env_path")
        config = {"outputPath": "/tmp/config_path", "os": "linux"}
        result = resolve_output_path("", config)
        assert result is not None
        assert "env_path" in result

    def test_config_priority(self):
        config = {"outputPath": "/tmp/config_path", "os": "linux"}
        result = resolve_output_path("", config)
        assert result is not None
        assert "config_path" in result

    def test_default_fallback(self, monkeypatch):
        monkeypatch.delenv("ZHIHU_OUTPUT_PATH", raising=False)
        config = {"outputPath": "", "os": "linux"}
        result = resolve_output_path("", config)
        assert result is None


# ── FavOps Wrappers ──


class TestFavOpsWrappers:
    def test_add_article_to_collection(self):
        with mock.patch(
            "zhihu_collections._operations.favorite_ops.add_to_collection",
            return_value=(True, "已添加"),
        ) as mock_add:
            success, msg = add_article_to_collection(
                "https://www.zhihu.com/collection/123",
                "https://www.zhihu.com/question/1/answer/456",
            )
            assert success is True
            assert msg == "已添加"
            mock_add.assert_called_once_with(
                "https://www.zhihu.com/collection/123",
                "https://www.zhihu.com/question/1/answer/456",
            )

    def test_add_article_failure(self):
        with mock.patch(
            "zhihu_collections._operations.favorite_ops.add_to_collection",
            return_value=(False, "添加失败: cookies 过期"),
        ) as mock_add:
            success, msg = add_article_to_collection(
                "https://www.zhihu.com/collection/123",
                "https://zhuanlan.zhihu.com/p/999",
            )
            assert success is False
            assert "cookies 过期" in msg

    def test_remove_article_from_collection(self):
        with mock.patch(
            "zhihu_collections._operations.favorite_ops.remove_from_collection",
            return_value=(True, "已取消收藏"),
        ) as mock_remove:
            success, msg = remove_article_from_collection(
                "https://www.zhihu.com/collection/123",
                "https://www.zhihu.com/question/1/answer/456",
            )
            assert success is True
            mock_remove.assert_called_once()

    def test_move_article_between_collections(self):
        with mock.patch(
            "zhihu_collections._operations.favorite_ops.move_to_collection",
            return_value=(True, "移动成功"),
        ) as mock_move:
            success, msg = move_article_between_collections(
                "https://www.zhihu.com/collection/111",
                "https://www.zhihu.com/collection/222",
                "https://www.zhihu.com/question/1/answer/456",
            )
            assert success is True
            assert msg == "移动成功"
            mock_move.assert_called_once_with(
                "https://www.zhihu.com/collection/111",
                "https://www.zhihu.com/collection/222",
                "https://www.zhihu.com/question/1/answer/456",
            )

    def test_move_article_failure(self):
        with mock.patch(
            "zhihu_collections._operations.favorite_ops.move_to_collection",
            return_value=(False, "添加失败，未执行移除操作"),
        ) as mock_move:
            success, msg = move_article_between_collections(
                "https://www.zhihu.com/collection/111",
                "https://www.zhihu.com/collection/222",
                "https://www.zhihu.com/question/1/answer/456",
            )
            assert success is False
            assert "添加失败" in msg


# ── export_single_collection ──


class TestExportSingleCollection:
    def test_export_basic(self):
        with mock.patch(
            "zhihu_collections._operations.create_export_context"
        ) as mock_ctx, mock.patch(
            "zhihu_collections._operations.process_single_collection"
        ) as mock_process:
            result = _call_export_single("https://www.zhihu.com/collection/123")
            assert "导出收藏夹" in result
            assert mock_process.called

    def test_export_with_all_options(self):
        with mock.patch(
            "zhihu_collections._operations.create_export_context"
        ), mock.patch(
            "zhihu_collections._operations.process_single_collection"
        ) as mock_process:
            result = _call_export_single(
                "https://www.zhihu.com/collection/123",
                name="测试",
                output_dir="/tmp",
                overwrite=True,
                max_articles=5,
            )
            assert "测试" in result
            assert "/tmp" in result
            assert mock_process.called

    def test_export_default_name(self):
        with mock.patch(
            "zhihu_collections._operations.create_export_context"
        ), mock.patch(
            "zhihu_collections._operations.process_single_collection"
        ):
            result = _call_export_single("https://www.zhihu.com/collection/123456789")
            assert "收藏夹_123456789" in result


def _call_export_single(url, name="", output_dir="", overwrite=False, max_articles=None):
    from zhihu_collections._operations import export_single_collection
    return export_single_collection(
        collection_url=url,
        collection_name=name,
        output_dir=output_dir,
        overwrite=overwrite,
        max_articles=max_articles,
    )
