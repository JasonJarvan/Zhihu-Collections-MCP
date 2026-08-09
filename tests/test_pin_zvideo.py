# -*- coding:utf-8 -*-
"""测试想法(pin) / 视频(zvideo) 的内容获取逻辑"""
import pytest
from unittest import mock

from zhihu_collections._content import (
    get_single_pin_content,
    get_single_zvideo_content,
    _build_pin_html_from_segments,
    _format_duration_seconds,
)


class MockResponse:
    """模拟 requests.Response"""

    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


# ── _build_pin_html_from_segments ──


class TestBuildPinHtmlFromSegments:
    def test_text_segment(self):
        html = _build_pin_html_from_segments(
            [{"type": "text", "content": "<p>hello <b>world</b></p>"}]
        )
        assert "<p>hello <b>world</b></p>" in html

    def test_text_own_text_fallback(self):
        html = _build_pin_html_from_segments(
            [{"type": "text", "own_text": "<p>own text</p>"}]
        )
        assert "<p>own text</p>" in html

    def test_image_segment(self):
        html = _build_pin_html_from_segments(
            [{"type": "image", "original_url": "https://pic1.zhimg.com/v2-abc.png"}]
        )
        assert '<img src="https://pic1.zhimg.com/v2-abc.png">' in html

    def test_image_url_fallback(self):
        html = _build_pin_html_from_segments(
            [{"type": "image", "url": "https://pic1.zhimg.com/v2-def.jpg"}]
        )
        assert '<img src="https://pic1.zhimg.com/v2-def.jpg">' in html

    def test_video_segment_thumbnail(self):
        html = _build_pin_html_from_segments(
            [{"type": "video", "thumbnail": "https://pic1.zhimg.com/v2-thumb.jpg"}]
        )
        assert '<img src="https://pic1.zhimg.com/v2-thumb.jpg">' in html

    def test_link_segment(self):
        html = _build_pin_html_from_segments(
            [{"type": "link", "url": "https://example.com", "title": "Example"}]
        )
        assert '<a href="https://example.com">Example</a>' in html

    def test_poll_segment_skipped(self):
        html = _build_pin_html_from_segments(
            [{"type": "poll"}, {"type": "text", "content": "<p>ok</p>"}]
        )
        assert "<p>ok</p>" in html

    def test_non_dict_segment_skipped(self):
        html = _build_pin_html_from_segments(["not-a-dict"])
        assert html == ""


# ── _format_duration_seconds ──


class TestFormatDurationSeconds:
    def test_minutes_seconds(self):
        assert _format_duration_seconds(415.225) == "6:55"

    def test_hours(self):
        assert _format_duration_seconds(3700) == "1:01:40"

    def test_under_minute(self):
        assert _format_duration_seconds(90) == "1:30"


# ── get_single_pin_content ──


class TestGetSinglePinContent:
    def test_uses_content_html(self):
        pin_data = {
            "content_html": '<p>hello <img src="https://pic1.zhimg.com/50/v2-thumb_b.jpg" data-original="https://pic1.zhimg.com/v2-original.png"></p>',
            "content": [],
        }
        with mock.patch(
            "zhihu_collections._content.requests.get",
            return_value=MockResponse(pin_data),
        ) as mock_get:
            result = get_single_pin_content(
                "https://www.zhihu.com/pin/12345",
                {},
                {},
                {},
                None,
            )
        assert isinstance(result, str)
        # 缩略图 src 被替换为 data-original 原图
        assert "v2-original.png" in result
        assert "50/v2-thumb_b.jpg" not in result
        # 请求的是 pin API
        mock_get.assert_called_once()
        url = mock_get.call_args[0][0]
        assert "/api/v4/pins/12345" in url

    def test_fallback_to_segments(self):
        pin_data = {
            "content_html": "",
            "content": [
                {"type": "text", "content": "<p>fallback text</p>"},
                {"type": "image", "original_url": "https://pic1.zhimg.com/v2-img.png"},
            ],
        }
        with mock.patch(
            "zhihu_collections._content.requests.get",
            return_value=MockResponse(pin_data),
        ):
            result = get_single_pin_content(
                "https://www.zhihu.com/pin/12345",
                {},
                {},
                {},
                None,
            )
        assert "<p>fallback text</p>" in result
        assert "v2-img.png" in result

    def test_api_failure_returns_minus_one(self):
        with mock.patch(
            "zhihu_collections._content.requests.get",
            side_effect=Exception("network error"),
        ):
            result = get_single_pin_content(
                "https://www.zhihu.com/pin/12345",
                {},
                {},
                {},
                None,
            )
        assert result == -1

    def test_empty_content_returns_minus_one(self):
        pin_data = {"content_html": "   ", "content": []}
        with mock.patch(
            "zhihu_collections._content.requests.get",
            return_value=MockResponse(pin_data),
        ):
            result = get_single_pin_content(
                "https://www.zhihu.com/pin/12345",
                {},
                {},
                {},
                None,
            )
        assert result == -1

    def test_invalid_url_returns_minus_one(self):
        result = get_single_pin_content(
            "https://www.zhihu.com/question/1/answer/2",
            {},
            {},
            {},
            None,
        )
        assert result == -1


# ── get_single_zvideo_content ──


class TestGetSingleZvideoContent:
    def _make_zvideo_data(self):
        return {
            "title": "测试视频标题",
            "description": "视频简介",
            "image_url": "https://pic1.zhimg.com/v2-cover.jpg",
            "play_count": 1000000,
            "voteup_count": 500,
            "comment_count": 10,
            "published_at": 1642744731,
            "author": {"name": "作者名"},
            "video": {
                "duration": 415.225,
                "thumbnail": "https://pic1.zhimg.com/v2-thumb.jpg",
                "playlist_v2": {
                    "fhd": {"play_url": "https://vdn1.example.com/fhd.mp4"},
                    "hd": {"play_url": "https://vdn1.example.com/hd.mp4"},
                },
            },
        }

    def test_builds_info_page(self):
        with mock.patch(
            "zhihu_collections._content.requests.get",
            return_value=MockResponse(self._make_zvideo_data()),
        ) as mock_get:
            result = get_single_zvideo_content(
                "https://www.zhihu.com/zvideo/9999",
                {},
                {},
                {},
                None,
            )
        assert isinstance(result, str)
        assert "测试视频标题" in result
        assert "作者名" in result
        assert "时长 6:55" in result
        assert "播放 1,000,000" in result
        assert '<img src="https://pic1.zhimg.com/v2-thumb.jpg">' in result
        assert "https://vdn1.example.com/fhd.mp4" in result
        assert "视频简介" in result
        # 请求的是 zvideo API
        url = mock_get.call_args[0][0]
        assert "/api/v4/zvideos/9999" in url

    def test_api_failure_returns_minus_one(self):
        with mock.patch(
            "zhihu_collections._content.requests.get",
            side_effect=Exception("network error"),
        ):
            result = get_single_zvideo_content(
                "https://www.zhihu.com/zvideo/9999",
                {},
                {},
                {},
                None,
            )
        assert result == -1

    def test_invalid_url_returns_minus_one(self):
        result = get_single_zvideo_content(
            "https://zhuanlan.zhihu.com/p/123",
            {},
            {},
            {},
            None,
        )
        assert result == -1
