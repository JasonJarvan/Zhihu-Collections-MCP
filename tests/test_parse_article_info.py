import pytest
from zhihu_collections.favorite_ops import parse_article_info


class TestParseArticleInfo:
    def test_answer_url(self):
        content_id, content_type = parse_article_info(
            "https://www.zhihu.com/question/123456/answer/789012"
        )
        assert content_id == "789012"
        assert content_type == "answer"

    def test_answer_url_with_query(self):
        content_id, content_type = parse_article_info(
            "https://www.zhihu.com/question/123456/answer/789012?utm_source=test"
        )
        assert content_id == "789012"
        assert content_type == "answer"

    def test_post_url(self):
        content_id, content_type = parse_article_info(
            "https://zhuanlan.zhihu.com/p/386395767"
        )
        assert content_id == "386395767"
        assert content_type == "article"

    def test_post_url_with_query(self):
        content_id, content_type = parse_article_info(
            "https://zhuanlan.zhihu.com/p/386395767?utm_source=test"
        )
        assert content_id == "386395767"
        assert content_type == "article"

    def test_zvideo_url(self):
        content_id, content_type = parse_article_info(
            "https://www.zhihu.com/zvideo/1234567890"
        )
        assert content_id == "1234567890"
        assert content_type == "zvideo"

    def test_pin_url(self):
        content_id, content_type = parse_article_info(
            "https://www.zhihu.com/pin/987654321"
        )
        assert content_id == "987654321"
        assert content_type == "pin"

    def test_invalid_url(self):
        content_id, content_type = parse_article_info(
            "https://example.com/something"
        )
        assert content_id is None
        assert content_type is None

    def test_empty_url(self):
        content_id, content_type = parse_article_info("")
        assert content_id is None
        assert content_type is None

    def test_fallback_numeric_id(self):
        content_id, content_type = parse_article_info(
            "https://www.zhihu.com/column/123456"
        )
        assert content_id == "123456"
        assert content_type == "unknown"
