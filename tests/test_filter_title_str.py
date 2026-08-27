from zhihu_collections.utils import filter_title_str


class TestFilterTitleStr:
    def test_normal_title(self):
        assert filter_title_str("Python 编程入门") == "Python 编程入门"

    def test_slash_replacement(self):
        result = filter_title_str("A/B\\C")
        assert "/" not in result
        assert "\\" not in result
        assert " " in result

    def test_colon_replacement(self):
        result = filter_title_str("标题: 副标题")
        assert ":" not in result
        assert "：" in result

    def test_question_mark_replacement(self):
        result = filter_title_str("什么是机器学习？")
        assert "?" not in result
        assert "？" in result

    def test_angle_brackets(self):
        result = filter_title_str("<div>内容</div>")
        assert "<" not in result
        assert ">" not in result

    def test_double_quotes(self):
        result = filter_title_str('"引号"')
        assert '"' not in result

    def test_pipe_character(self):
        result = filter_title_str("a|b")
        assert "|" not in result

    def test_empty_string(self):
        result = filter_title_str("")
        assert result == ""

    def test_combined_special_chars(self):
        result = filter_title_str('文件: "A/B?<C>|D"')
        assert "/" not in result
        assert '"' not in result
        assert "?" not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result
        assert ":" not in result
