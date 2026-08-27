# -*- coding:utf-8 -*-
from __future__ import annotations

import os
import re
import logging
import traceback
import hashlib
from typing import Any, Optional, Tuple

import requests
from markdownify import MarkdownConverter

from zhihu_collections._paths import get_output_path
from zhihu_collections._export import ExportContext


class _BaseStyleConverter(MarkdownConverter):
    """Markdown 转换器基类，支持图片下载和知乎特有元素处理"""

    def __init__(
        self, collection_name: str, context: ExportContext, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self._collection_name = collection_name
        self._ctx = context

    def chomp(self, text: str) -> tuple[str, str, str]:
        """去除文本前后的空白，返回 (prefix, suffix, text)"""
        prefix = " " if text and text[0] == " " else ""
        suffix = " " if text and text[-1] == " " else ""
        text = text.strip()
        return (prefix, suffix, text)

    def _download_image(self, src: str) -> tuple[Optional[str], Optional[str]]:
        """下载图片到 assets 目录，返回 (文件名, assets目录路径)"""
        downloadDir = get_output_path(self._collection_name, self._ctx.base_output_path)
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir)
        assetsDir = os.path.join(downloadDir, "assets")
        if not os.path.exists(assetsDir):
            os.makedirs(assetsDir)

        try:
            img_content = requests.get(
                url=src, headers=self._ctx.headers, cookies=self._ctx.cookies, timeout=30
            ).content
        except Exception as img_e:
            logging.warning(f"图片下载失败: {src} - {img_e}")
            return None, None

        img_content_name = src.split("?")[0].split("/")[-1]
        if "/equation" in src:
            url_hash = hashlib.sha256(src.encode()).hexdigest()[:12]
            img_content_name = f"equation_{url_hash}.svg"
            svg_str = img_content.decode("utf-8", errors="ignore")
            svg_str = re.sub(
                r'(<svg[^>]*>)',
                r'\1<rect width="100%" height="100%" fill="white"/>',
                svg_str,
                count=1,
            )
            img_content = svg_str.encode("utf-8")
        imgPath = os.path.join(assetsDir, img_content_name)
        with open(imgPath, "wb") as fp:
            fp.write(img_content)

        return img_content_name, assetsDir

    def _format_image(self, filename: str, alt: str) -> str:
        raise NotImplementedError

    def convert_img(self, *args: Any, **kwargs: Any) -> str:
        logging.debug(f"convert_img called with args: {args}, kwargs={kwargs}")
        el: Any = None
        try:
            if len(args) >= 2:
                el, text = args[0], args[1]
            else:
                el = kwargs.get("el")
                text = kwargs.get("text", "")

            alt = el.attrs.get("alt", None) or ""
            src = el.attrs.get("src", None) or ""

            filename, _ = self._download_image(src)
            if filename is None:
                return "![%s](%s)\n\n" % (alt, src)

            result = self._format_image(filename, alt)
            logging.debug(f"convert_img returning: {result}")
            return result
        except Exception as e:
            logging.error(f"convert_img error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            alt = el.attrs.get("alt", "") if hasattr(el, "attrs") else ""
            src = el.attrs.get("src", "") if hasattr(el, "attrs") else ""
            return "![%s](%s)\n\n" % (alt, src)

    def convert_a(self, *args: Any, **kwargs: Any) -> str:
        logging.debug(f"convert_a called with args: {args}, kwargs={kwargs}")
        try:
            if len(args) >= 2:
                el, text = args[0], args[1]
                convert_as_inline: Optional[Any] = args[2] if len(args) > 2 else None
            else:
                el = kwargs.get("el")
                text = kwargs.get("text", "")
                convert_as_inline = kwargs.get("convert_as_inline")

            prefix, suffix, text = self.chomp(text)
            if not text:
                return ""
            href = el.get("href")

            if el.get("aria-labelledby") and el.get("aria-labelledby").find("ref") > -1:
                text = text.replace("[", "[^")
                result = "%s" % text
                return result
            if (el.attrs and "data-reference-link" in el.attrs) or (
                "class" in el.attrs and ("ReferenceList-backLink" in el.attrs["class"])
            ):
                text = "[^{}]: ".format(href[5])
                result = "%s" % text
                return result

            try:
                if convert_as_inline is not None:
                    result = MarkdownConverter.convert_a(
                        self, el, text, convert_as_inline, **kwargs
                    )
                else:
                    result = MarkdownConverter.convert_a(
                        self, el, text, **kwargs
                    )
            except TypeError:
                try:
                    result = MarkdownConverter.convert_a(self, *args, **kwargs)
                except TypeError:
                    result = MarkdownConverter.convert_a(self, el, text)

            return result
        except Exception as e:
            logging.error(f"convert_a error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    def convert_li(self, *args: Any, **kwargs: Any) -> str:
        logging.debug(f"convert_li called with args: {args}, kwargs={kwargs}")
        try:
            if len(args) >= 2:
                el, text = args[0], args[1]
                convert_as_inline: Optional[Any] = args[2] if len(args) > 2 else None
            else:
                el = kwargs.get("el")
                text = kwargs.get("text", "")
                convert_as_inline = kwargs.get("convert_as_inline")

            if el and el.find("a", {"aria-label": "back"}) is not None:
                result = "%s\n" % ((text or "").strip())
                return result

            try:
                if convert_as_inline is not None:
                    result = MarkdownConverter.convert_li(
                        self, el, text, convert_as_inline, **kwargs
                    )
                else:
                    result = MarkdownConverter.convert_li(
                        self, el, text, **kwargs
                    )
            except TypeError:
                try:
                    result = MarkdownConverter.convert_li(self, *args, **kwargs)
                except TypeError:
                    result = MarkdownConverter.convert_li(self, el, text)

            return result
        except Exception as e:
            logging.error(f"convert_li error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise


class ObsidianStyleConverter(_BaseStyleConverter):
    """Obsidian 风格：图片使用 ![[filename]] wiki-link 语法"""

    def _format_image(self, filename: str, alt: str) -> str:
        return "![[%s]]\n(%s)\n\n" % (filename, alt)


class StandardStyleConverter(_BaseStyleConverter):
    """标准 Markdown 格式：!%5Balt%5D(assets/filename)"""

    def _format_image(self, filename: str, alt: str) -> str:
        return "![%s](assets/%s)\n\n" % (alt, filename)


def markdownify(
    html: str, collection_name: str, context: ExportContext, **options: Any
) -> str:
    """将 HTML 内容转换为 Markdown

    :param html: HTML 内容字符串
    :param collection_name: 收藏夹名称（用于图片路径）
    :param context: 导出上下文
    :param options: 传递给转换器的额外选项，支持 format="obsidian"|"standard"
    """
    fmt = options.pop("format", "obsidian")
    converter_cls = ObsidianStyleConverter if fmt == "obsidian" else StandardStyleConverter
    return converter_cls(collection_name, context, **options).convert(html)
