# -*- coding:utf-8 -*-
"""
知乎收藏夹导出工具 - MCP Server
将知乎收藏夹导出功能封装为MCP服务，供AI Agent调用
"""

import os
import asyncio

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from zhihu_collections._operations import (
    list_collections,
    export_single_collection,
    get_collection_info,
    search_collections,
    add_article_to_collection,
    remove_article_from_collection,
    move_article_between_collections,
)


async def main():
    app = Server("zhihu-collections")

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_collections",
                description="列出配置文件中所有知乎收藏夹",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="export_collection",
                description="导出指定知乎收藏夹为Markdown文件",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_url": {
                            "type": "string",
                            "description": "收藏夹URL，如 https://www.zhihu.com/collection/123456789",
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "收藏夹名称（可选，用于命名输出目录）",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": (
                                "输出目录路径（可选）。优先级: 本参数 > ZHIHU_OUTPUT_PATH 环境变量"
                                " > config.json 的 outputPath > downloads/"
                            ),
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "是否覆盖已存在的文件（true=重新下载补全内容，false=跳过已存在的，默认false）",
                            "default": False,
                        },
                        "max_articles": {
                            "type": "integer",
                            "description": "只导出最新的N篇文章（按收藏时间排序，默认全部导出）",
                        },
                    },
                    "required": ["collection_url"],
                },
            ),
            Tool(
                name="get_collection_info",
                description="获取指定收藏夹的基本信息（文章数量等）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_url": {"type": "string", "description": "收藏夹URL"}
                    },
                    "required": ["collection_url"],
                },
            ),
            Tool(
                name="search_collections",
                description="在配置文件中搜索包含关键词的收藏夹",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "搜索关键词"}
                    },
                    "required": ["keyword"],
                },
            ),
            Tool(
                name="remove_from_collection",
                description="从指定知乎收藏夹中取消收藏一篇文章（取消收藏），支持回答、专栏文章、视频等类型",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_url": {
                            "type": "string",
                            "description": "收藏夹URL，如 https://www.zhihu.com/collection/123456789",
                        },
                        "article_url": {
                            "type": "string",
                            "description": "要取消收藏的文章URL，支持：\n- 回答: https://www.zhihu.com/question/xxx/answer/yyy\n- 专栏: https://zhuanlan.zhihu.com/p/xxx\n- 视频: https://www.zhihu.com/zvideo/xxx",
                        },
                    },
                    "required": ["collection_url", "article_url"],
                },
            ),
            Tool(
                name="add_to_collection",
                description="收藏一篇文章到指定知乎收藏夹。支持回答、专栏文章、视频、想法等类型。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_url": {
                            "type": "string",
                            "description": "目标收藏夹URL，如 https://www.zhihu.com/collection/123456789",
                        },
                        "article_url": {
                            "type": "string",
                            "description": "要收藏的文章URL，支持：\n- 回答: https://www.zhihu.com/question/xxx/answer/yyy\n- 专栏: https://zhuanlan.zhihu.com/p/xxx\n- 视频: https://www.zhihu.com/zvideo/xxx\n- 想法: https://www.zhihu.com/pin/xxx",
                        },
                    },
                    "required": ["collection_url", "article_url"],
                },
            ),
            Tool(
                name="move_to_collection",
                description="将一篇文章从一个收藏夹移动到另一个收藏夹（先添加后移除，保证内容不丢失）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_collection_url": {
                            "type": "string",
                            "description": "源收藏夹URL，如 https://www.zhihu.com/collection/123456789",
                        },
                        "to_collection_url": {
                            "type": "string",
                            "description": "目标收藏夹URL，如 https://www.zhihu.com/collection/987654321",
                        },
                        "article_url": {
                            "type": "string",
                            "description": "要移动的文章URL，支持：\n- 回答: https://www.zhihu.com/question/xxx/answer/yyy\n- 专栏: https://zhuanlan.zhihu.com/p/xxx\n- 视频: https://www.zhihu.com/zvideo/xxx\n- 想法: https://www.zhihu.com/pin/xxx",
                        },
                    },
                    "required": ["from_collection_url", "to_collection_url", "article_url"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "list_collections":
                return await _list_collections_handler()
            elif name == "export_collection":
                return await _export_collection_handler(arguments)
            elif name == "get_collection_info":
                return await _get_collection_info_handler(arguments)
            elif name == "search_collections":
                return await _search_collections_handler(arguments)
            elif name == "remove_from_collection":
                return await _remove_from_collection_handler(arguments)
            elif name == "add_to_collection":
                return await _add_to_collection_handler(arguments)
            elif name == "move_to_collection":
                return await _move_to_collection_handler(arguments)
            else:
                return [TextContent(type="text", text=f"未知工具: {name}")]
        except Exception as e:
            import traceback
            return [
                TextContent(type="text", text=f"错误: {str(e)}\n{traceback.format_exc()}")
            ]

    async def _list_collections_handler() -> list[TextContent]:
        collections = list_collections()

        if not collections:
            return [
                TextContent(
                    type="text", text="未找到配置的收藏夹，请在config.json中添加收藏夹信息"
                )
            ]

        result = "📚 已配置的收藏夹列表：\n\n"
        for i, coll in enumerate(collections, 1):
            name = coll.get("name", "未命名")
            url = coll.get("url", "")
            result += f"{i}. **{name}**\n"
            result += f"   URL: {url}\n\n"

        return [TextContent(type="text", text=result)]

    async def _export_collection_handler(args: dict) -> list[TextContent]:
        collection_url = args.get("collection_url")
        if not collection_url:
            return [TextContent(type="text", text="错误: 需要提供collection_url参数")]

        result = export_single_collection(
            collection_url=collection_url,
            collection_name=args.get("collection_name", ""),
            output_dir=args.get("output_dir", ""),
            overwrite=args.get("overwrite", False),
            max_articles=args.get("max_articles", None),
        )

        emoji_result = (
            result.replace("导出收藏夹", "🚀 导出收藏夹")
            .replace("导出完成", "✅ 导出完成")
            .replace("导出失败", "❌ 导出失败")
        )
        return [TextContent(type="text", text=emoji_result)]

    async def _get_collection_info_handler(args: dict) -> list[TextContent]:
        collection_url = args.get("collection_url")
        if not collection_url:
            return [TextContent(type="text", text="错误: 需要提供collection_url参数")]

        try:
            result = get_collection_info(collection_url)
            return [TextContent(type="text", text=f"📊 收藏夹信息\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"获取收藏夹信息失败: {str(e)}")]

    async def _search_collections_handler(args: dict) -> list[TextContent]:
        keyword = args.get("keyword", "")
        if not keyword:
            return [TextContent(type="text", text="错误: 需要提供keyword参数")]

        matched = search_collections(keyword)

        if not matched:
            return [TextContent(type="text", text=f"没有找到包含 '{keyword}' 的收藏夹")]

        result = f"🔍 搜索结果（关键词：{keyword}）：\n\n"
        for i, coll in enumerate(matched, 1):
            name = coll.get("name", "未命名")
            url = coll.get("url", "")
            result += f"{i}. **{name}**\n"
            result += f"   URL: {url}\n\n"

        return [TextContent(type="text", text=result)]

    async def _remove_from_collection_handler(args: dict) -> list[TextContent]:
        collection_url = args.get("collection_url", "").strip()
        article_url = args.get("article_url", "").strip()

        if not collection_url:
            return [TextContent(type="text", text="错误: 需要提供 collection_url 参数")]
        if not article_url:
            return [TextContent(type="text", text="错误: 需要提供 article_url 参数")]

        result = f"🗑️ 正在取消收藏...\n"
        result += f"📂 收藏夹: {collection_url}\n"
        result += f"📄 文章: {article_url}\n\n"

        success, msg = remove_article_from_collection(collection_url, article_url)
        result += msg
        return [TextContent(type="text", text=result)]

    async def _add_to_collection_handler(args: dict) -> list[TextContent]:
        collection_url = args.get("collection_url", "").strip()
        article_url = args.get("article_url", "").strip()

        if not collection_url:
            return [TextContent(type="text", text="错误: 需要提供 collection_url 参数")]
        if not article_url:
            return [TextContent(type="text", text="错误: 需要提供 article_url 参数")]

        result = f"⭐ 正在收藏文章...\n"
        result += f"📂 目标收藏夹: {collection_url}\n"
        result += f"📄 文章: {article_url}\n\n"

        success, msg = add_article_to_collection(collection_url, article_url)
        result += msg
        return [TextContent(type="text", text=result)]

    async def _move_to_collection_handler(args: dict) -> list[TextContent]:
        from_url = args.get("from_collection_url", "").strip()
        to_url = args.get("to_collection_url", "").strip()
        article_url = args.get("article_url", "").strip()

        if not from_url:
            return [TextContent(type="text", text="错误: 需要提供 from_collection_url 参数")]
        if not to_url:
            return [TextContent(type="text", text="错误: 需要提供 to_collection_url 参数")]
        if not article_url:
            return [TextContent(type="text", text="错误: 需要提供 article_url 参数")]

        result = f"📦 正在移动文章...\n"
        result += f"📂 源收藏夹: {from_url}\n"
        result += f"📂 目标收藏夹: {to_url}\n"
        result += f"📄 文章: {article_url}\n\n"

        success, msg = move_article_between_collections(from_url, to_url, article_url)
        result += msg
        return [TextContent(type="text", text=result)]

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def cli():
    """Sync entry point for console_scripts."""
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
