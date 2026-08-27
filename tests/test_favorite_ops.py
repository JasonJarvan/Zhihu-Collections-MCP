import json
from unittest import mock

import pytest
import requests

from zhihu_collections.favorite_ops import (
    parse_article_info,
    favorite_content,
    unfavorite_content,
    add_to_collection,
    remove_from_collection,
    move_to_collection,
)


class TestParseArticleInfo:
    def test_answer_url(self):
        cid, ctype = parse_article_info(
            "https://www.zhihu.com/question/123/answer/456"
        )
        assert cid == "456"
        assert ctype == "answer"

    def test_article_url(self):
        cid, ctype = parse_article_info("https://zhuanlan.zhihu.com/p/12345")
        assert cid == "12345"
        assert ctype == "article"

    def test_invalid_url(self):
        cid, ctype = parse_article_info("not a url")
        assert cid is None
        assert ctype is None


class TestFavoriteContent:
    @mock.patch("zhihu_collections.favorite_ops.get_cookies")
    @mock.patch("zhihu_collections.favorite_ops.requests.post")
    def test_favorite_success(self, mock_post, mock_get_cookies):
        mock_get_cookies.return_value = {"_xsrf": "test_xsrf"}
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "collection": {"title": "默认收藏夹"}}
        mock_post.return_value = mock_response

        success, msg = favorite_content("answer", "12345")
        assert success is True
        assert "已收藏" in msg

    @mock.patch("zhihu_collections.favorite_ops.get_cookies")
    @mock.patch("zhihu_collections.favorite_ops.requests.post")
    def test_favorite_to_specific_collection(self, mock_post, mock_get_cookies):
        mock_get_cookies.return_value = {"_xsrf": "test_xsrf"}
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        success, msg = favorite_content("article", "67890", collection_id="111")
        assert success is True

    @mock.patch("zhihu_collections.favorite_ops.get_cookies")
    @mock.patch("zhihu_collections.favorite_ops.requests.post")
    def test_favorite_already_collected(self, mock_post, mock_get_cookies):
        mock_get_cookies.return_value = {"_xsrf": "test_xsrf"}
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        success, msg = favorite_content("answer", "12345")
        assert success is True
        assert "已收藏" in msg

    @mock.patch("zhihu_collections.favorite_ops.get_cookies")
    @mock.patch("zhihu_collections.favorite_ops.requests.post")
    def test_favorite_failure(self, mock_post, mock_get_cookies):
        mock_get_cookies.return_value = {"_xsrf": "test_xsrf"}
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        success, msg = favorite_content("answer", "12345")
        assert success is False
        assert "失败" in msg


class TestUnfavoriteContent:
    @mock.patch("zhihu_collections.favorite_ops.get_cookies")
    @mock.patch("zhihu_collections.favorite_ops.requests.delete")
    def test_unfavorite_success(self, mock_delete, mock_get_cookies):
        mock_get_cookies.return_value = {"_xsrf": "test_xsrf"}
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "favlists_count": 5}
        mock_delete.return_value = mock_response

        success, msg = unfavorite_content("answer", "12345")
        assert success is True
        assert "已取消收藏" in msg

    @mock.patch("zhihu_collections.favorite_ops.get_cookies")
    @mock.patch("zhihu_collections.favorite_ops.requests.delete")
    def test_unfavorite_already_removed(self, mock_delete, mock_get_cookies):
        mock_get_cookies.return_value = {"_xsrf": "test_xsrf"}
        mock_response = mock.Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": {"message": "未收藏该内容"}}
        mock_delete.return_value = mock_response

        success, msg = unfavorite_content("answer", "12345")
        assert success is True

    @mock.patch("zhihu_collections.favorite_ops.get_cookies")
    @mock.patch("zhihu_collections.favorite_ops.requests.delete")
    def test_unfavorite_timeout(self, mock_delete, mock_get_cookies):
        mock_get_cookies.return_value = {"_xsrf": "test_xsrf"}
        mock_delete.side_effect = requests.exceptions.Timeout("Timeout")

        success, msg = unfavorite_content("answer", "12345")
        assert success is False
        assert "超时" in msg


class TestHighLevelWrappers:
    @mock.patch("zhihu_collections.favorite_ops.favorite_content")
    def test_add_to_collection(self, mock_fav):
        mock_fav.return_value = (True, "✅ 已添加到收藏夹")
        success, msg = add_to_collection(
            "https://www.zhihu.com/collection/123",
            "https://www.zhihu.com/question/1/answer/456",
        )
        assert success is True
        mock_fav.assert_called_once()

    @mock.patch("zhihu_collections.favorite_ops.unfavorite_content")
    def test_remove_from_collection(self, mock_unfav):
        mock_unfav.return_value = (True, "✅ 已取消收藏")
        success, msg = remove_from_collection(
            "https://www.zhihu.com/collection/123",
            "https://www.zhihu.com/question/1/answer/456",
        )
        assert success is True
        mock_unfav.assert_called_once()

    @mock.patch("zhihu_collections.favorite_ops.favorite_content")
    @mock.patch("zhihu_collections.favorite_ops.unfavorite_content")
    @mock.patch("zhihu_collections.favorite_ops._move_step_delay")
    @mock.patch("zhihu_collections.favorite_ops.time.sleep")
    def test_move_to_collection(self, mock_sleep, mock_delay, mock_unfav, mock_fav):
        mock_fav.return_value = (True, "✅ 已添加到目标收藏夹")
        mock_unfav.return_value = (True, "✅ 已取消收藏")

        success, msg = move_to_collection(
            "https://www.zhihu.com/collection/111",
            "https://www.zhihu.com/collection/222",
            "https://www.zhihu.com/question/1/answer/456",
        )
        assert success is True
        assert mock_fav.call_count >= 2
        assert mock_unfav.call_count >= 1

    @mock.patch("zhihu_collections.favorite_ops.favorite_content")
    @mock.patch("zhihu_collections.favorite_ops.unfavorite_content")
    @mock.patch("zhihu_collections.favorite_ops._move_step_delay")
    @mock.patch("zhihu_collections.favorite_ops.time.sleep")
    def test_move_to_collection_add_fails(self, mock_sleep, mock_delay, mock_unfav, mock_fav):
        mock_fav.return_value = (False, "❌ 添加失败")

        success, msg = move_to_collection(
            "https://www.zhihu.com/collection/111",
            "https://www.zhihu.com/collection/222",
            "https://www.zhihu.com/question/1/answer/456",
        )
        assert success is False
        assert "添加失败" in msg
        mock_unfav.assert_not_called()
