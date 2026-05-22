import json
import os

from zhihu_collections._common import load_cookies, load_config, get_current_os, parse_output_path


class TestLoadCookies:
    def test_load_valid_cookies(self, temp_dir, sample_cookies_list):
        cookies_path = os.path.join(temp_dir, "cookies.json")
        with open(cookies_path, "w", encoding="utf-8") as f:
            json.dump(sample_cookies_list, f)

        result = load_cookies(cookies_path)
        assert result == {"_xsrf": "test_xsrf_token", "z_c0": "test_z_c0_value", "d_c0": "test_d_c0_value"}

    def test_load_missing_file(self):
        result = load_cookies("/nonexistent/path/cookies.json")
        assert result == {}

    def test_load_empty_cookies(self, temp_dir):
        cookies_path = os.path.join(temp_dir, "cookies.json")
        with open(cookies_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        result = load_cookies(cookies_path)
        assert result == {}


class TestLoadConfig:
    def test_load_valid_config(self, temp_dir, sample_config):
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(sample_config, f)

            config = load_config()
            assert config["zhihuUrls"] == sample_config["zhihuUrls"]
            assert config["markdownFormat"] == "obsidian"
        finally:
            os.chdir(old_cwd)

    def test_load_missing_config_returns_default(self, temp_dir):
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            config = load_config()
            assert config["zhihuUrls"] == []
        finally:
            os.chdir(old_cwd)

    def test_load_fallback_to_zhihuUrls(self, temp_dir):
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            zhihu_urls = [
                {"name": "fallback", "url": "https://www.zhihu.com/collection/999"},
            ]
            with open("zhihuUrls.json", "w", encoding="utf-8") as f:
                json.dump(zhihu_urls, f)

            config = load_config()
            assert config["zhihuUrls"] == zhihu_urls
        finally:
            os.chdir(old_cwd)


class TestGetCurrentOs:
    def test_returns_string(self):
        os_type = get_current_os()
        assert isinstance(os_type, str)
        assert os_type in ("windows", "macos", "linux", "unknown")


class TestParseOutputPath:
    def test_empty_path(self):
        assert parse_output_path("", "") is None

    def test_linux_absolute_path(self):
        path = parse_output_path("/tmp/test", "linux")
        assert path is not None
        assert str(path).startswith("/")

    def test_linux_tilde_expansion(self):
        path = parse_output_path("~/test", "linux")
        assert path is not None
        assert str(path).startswith("/")

    def test_windows_path(self):
        path = parse_output_path("D:/test/folder", "windows")
        assert path is not None

    def test_unknown_os_fallback(self):
        path = parse_output_path("/tmp/test", "unknown")
        assert path is not None
