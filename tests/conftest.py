import json
import os
import tempfile

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_cookies_dict():
    return {
        "_xsrf": "test_xsrf_token",
        "z_c0": "test_z_c0_value",
        "d_c0": "test_d_c0_value",
    }


@pytest.fixture
def sample_cookies_list(sample_cookies_dict):
    return [
        {"name": k, "value": v} for k, v in sample_cookies_dict.items()
    ]


@pytest.fixture
def sample_config():
    return {
        "zhihuUrls": [
            {"name": "测试收藏夹", "url": "https://www.zhihu.com/collection/123456"},
        ],
        "outputPath": "/tmp/test_output",
        "os": "linux",
        "openCollection": False,
        "markdownFormat": "obsidian",
    }


class MockElement:
    def __init__(self, tag="div", attrs=None, children=None, text=""):
        self.tag = tag
        self.attrs = attrs or {}
        self.text = text
        self._children = children or []

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    def get_text(self, strip=False):
        result = self.text
        for child in self._children:
            result += child.get_text()
        return result.strip() if strip else result

    def find(self, tag, attrs=None):
        for child in self._children:
            if child.tag == tag:
                if attrs:
                    match = all(child.get(k) == v for k, v in attrs.items())
                    if match:
                        return child
                else:
                    return child
        return None

    def find_all(self, tag, **kwargs):
        return [c for c in self._children if c.tag == tag]


@pytest.fixture
def mock_img_el():
    return MockElement("img", {"src": "https://example.com/test.png", "alt": "测试图片"})


@pytest.fixture
def mock_ref_a_el():
    return MockElement("a", {"aria-labelledby": "ref_1"}, text="参考链接")
