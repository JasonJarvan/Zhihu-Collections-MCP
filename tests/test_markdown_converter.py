import pytest
from zhihu_collections.main import ObsidianStyleConverter, StandardStyleConverter


class TestObsidianStyleConverter:
    def test_format_image(self):
        converter = ObsidianStyleConverter()
        result = converter._format_image("test.png", "alt text")
        assert "![[test.png]]" in result
        assert "(alt text)" in result

    def test_format_image_no_alt(self):
        converter = ObsidianStyleConverter()
        result = converter._format_image("image.jpg", "")
        assert "![[image.jpg]]" in result
        assert "()" in result

    def test_chomp_preserves_spaces(self):
        converter = ObsidianStyleConverter()
        prefix, suffix, text = converter.chomp(" hello ")
        assert prefix == " "
        assert suffix == " "
        assert text == "hello"

    def test_chomp_no_spaces(self):
        converter = ObsidianStyleConverter()
        prefix, suffix, text = converter.chomp("hello")
        assert prefix == ""
        assert suffix == ""
        assert text == "hello"

    def test_convert_a_ref_link(self):
        from tests.conftest import MockElement

        converter = ObsidianStyleConverter()
        el = MockElement("a", {"aria-labelledby": "ref_1"}, text="[1]")
        result = converter.convert_a(el, "[1]")
        assert "[^1]" in result or "[^" in result

    def test_convert_a_reference_backlink(self):
        from tests.conftest import MockElement

        converter = ObsidianStyleConverter()
        el = MockElement("a", {
            "data-reference-link": "true",
            "class": ["ReferenceList-backLink"],
            "href": "#ref_12345",
        }, text="返回")
        result = converter.convert_a(el, "返回")
        assert "[^" in result


class TestStandardStyleConverter:
    def test_format_image(self):
        converter = StandardStyleConverter()
        result = converter._format_image("test.png", "alt text")
        assert "![alt text](assets/test.png)" in result

    def test_format_image_no_alt(self):
        converter = StandardStyleConverter()
        result = converter._format_image("image.jpg", "")
        assert "![](assets/image.jpg)" in result

    def test_inherits_zhihu_conversions(self):
        from tests.conftest import MockElement

        converter = StandardStyleConverter()
        el = MockElement("a", {"aria-labelledby": "ref_1"}, text="[1]")
        result = converter.convert_a(el, "[1]")
        assert "[^" in result
