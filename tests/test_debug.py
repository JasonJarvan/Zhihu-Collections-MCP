#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 直接测试方法签名
try:
    # 模拟一个简单的元素对象
    class MockElement:
        def __init__(self, name, attrs=None):
            self.name = name
            self.attrs = attrs or {}
        
        def get(self, key, default=None):
            return self.attrs.get(key, default)
    
    # 创建一个最小化的转换器来测试签名
    from markdownify import MarkdownConverter
    
    class TestConverter(MarkdownConverter):
        def convert_a(self, el, text, convert_as_inline=None, **kwargs):
            print(f"convert_a called with: el={el}, text='{text}', convert_as_inline={convert_as_inline}, kwargs={kwargs}")
            return f"[{text}]({el.get('href', '')})"
        
        def convert_img(self, el, text, **kwargs):
            print(f"convert_img called with: el={el}, text='{text}', kwargs={kwargs}")
            return f"![{el.get('alt', '')}]({el.get('src', '')})"
        
        def convert_li(self, el, text, convert_as_inline=None, **kwargs):
            print(f"convert_li called with: el={el}, text='{text}', convert_as_inline={convert_as_inline}, kwargs={kwargs}")
            return f"- {text}\n"
    
    def test_markdownify(html, **options):
        return TestConverter(**options).convert(html)
    
    # 简单的HTML测试内容
    test_html = '''<a href="https://example.com">链接测试</a>'''
    
    print("开始测试markdownify转换...")
    result = test_markdownify(test_html, heading_style="ATX")
    print("转换成功!")
    print("结果:", result)
    
except Exception as e:
    print(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()