# AGENTS.md

**重要规则：始终使用中文回答**

## 项目概述

Export-Zhihu-Collections 是一个将知乎收藏夹导出为 Markdown 格式的 Python 工具。支持公开和私密收藏夹、批量处理、自定义输出路径、图片下载，并提供 MCP Server 供 AI Agent 调用。

## Toolchain

- **包管理器**: `uv`（不用 pip）。安装: `uv sync`。开发依赖: `uv sync --group dev`。
- **测试**: `uv run pytest`（pytest 配置在 `pyproject.toml`，`testpaths = ["tests"]`）。
  部分 `tests/test_*.py` 是独立脚本，用 `python3 tests/test_*.py` 运行（非 pytest）。
- **构建**: hatchling (`pyproject.toml:build-system`)
- **Python**: >= 3.10

## CLI 命令

| 命令 | 说明 |
|------|------|
| `uv run zhihu list` | 列出所有收藏夹 |
| `uv run zhihu export <url>` | 导出单个收藏夹（支持 `--name`、`--output`、`--overwrite`、`--max-articles N`） |
| `uv run zhihu export-all` | 批量导出 config.json 中所有收藏夹（支持 `--output`） |
| `uv run zhihu info <url>` | 获取收藏夹信息（文章数量等） |
| `uv run zhihu search <keyword>` | 搜索收藏夹 |
| `uv run zhihu add <collection_url> <article_url>` | 收藏一篇文章 |
| `uv run zhihu remove <collection_url> <article_url>` | 取消收藏一篇文章 |
| `uv run zhihu move <from_url> <to_url> <article_url>` | 移动文章到另一个收藏夹 |
| `uv run zhihu fetch` | 自动获取收藏夹列表写入 config.json |
| `uv run zhihu-mcp-server` | 启动 MCP stdio server |

**向后兼容别名**（已重定向到新 CLI）:
- `uv run zhihu-export` → `zhihu export-all`
- `uv run zhihu-fetch` → `zhihu fetch`

`outputPath` 优先级: CLI `--output` > `ZHIHU_OUTPUT_PATH` 环境变量 > `config.json` `outputPath` > `downloads/`。

## 项目结构

- **src-layout**: 所有代码在 `src/zhihu_collections/`
- **私有模块**（前缀 `_`）: `_common`、`_logging`、`_headers`、`_paths`、`_converter`、`_content`、`_collection`、`_export`、`_operations`。这些是内部模块；优先从 `zhihu_collections` (`__init__.py`) 导入。
- **公共模块**: `main.py` (向后兼容)、`mcp_server.py`、`favorite_ops.py`、`fetch_collections.py`、`cli.py` (统一 CLI)、`utils.py`
- **开发工具**: `scripts/` 目录下的 `debug_page.py`、`analyze_issue.py`

```
src/zhihu_collections/
├── __init__.py          # 公共导出
├── _common.py           # 配置加载、路径解析
├── _logging.py          # 日志配置
├── _headers.py          # HTTP 请求头
├── _paths.py            # 输出路径管理
├── _converter.py        # Markdown 转换器 (Obsidian/标准)
├── _content.py          # 内容获取与 HTML 解析
├── _collection.py       # 收藏夹处理流程
├── _export.py           # 导出上下文与文件操作
├── _operations.py       # 共享业务逻辑（CLI + MCP 共用）
├── cli.py               # 统一 CLI 入口
├── main.py              # 向后兼容导出入口
├── mcp_server.py        # MCP Server
├── favorite_ops.py      # 收藏/取消收藏/移动操作
├── fetch_collections.py # 收藏夹列表获取
└── utils.py             # 文件名清理
```

## Config & auth

- `config.json` 已 gitignore；复制自 `config_examples.json`。字段: `zhihuUrls[]` (name + url)、`outputPath`、`os`、`openCollection` (bool)、`markdownFormat` (`"obsidian"` / `"standard"`)。
- `cookies.json` 已 gitignore；复制自 `cookies_examples.json`。接受简单 `[{name, value}]` 或完整浏览器导出格式（含 `domain`、`path` 等）。
- `downloads/` 和 `blogs/` 目录已 gitignore。

## MCP Server

- 异步 stdio 传输 (`mcp` 库 + `mcp.server.stdio.stdio_server`)。
- 入口: `zhihu_collections.mcp_server:main`（通过 `uv run zhihu-mcp-server` 启动）。
- 工具: `list_collections`、`export_collection`、`get_collection_info`、`search_collections`、`remove_from_collection`、`add_to_collection`、`move_to_collection`。
- 所有工具的业务逻辑在 `_operations.py` 中，MCP handlers 和 CLI 子命令共享同一实现。

## 架构说明

- 配置加载: `_common.load_config()`。输出路径解析: `_paths.get_output_path()`（默认 `downloads/`）。
- 收藏夹处理: `_collection.process_single_collection()`。内容获取: `_content`（支持回答页、专栏、403 时 API 回退）。
- Markdown 转换: `markdownify` 库；`_converter.markdownify()` 支持 Obsidian 风格 `![[image]]` 或标准图片语法。
- 图片保存: 每个收藏夹的 `assets/` 子目录。文件名经 `utils.filter_title_str()` 清理，重复标题追加 URL ID 后缀。
- 解析失败时保存调试 HTML: `downloads/debug/`。

### CLI 与 MCP 共享架构

```
_operations.py (纯业务逻辑)
    ├── cli.py (CLI 子命令)
    └── mcp_server.py (MCP handlers ~ 薄包装)
```

新增功能只需在 `_operations.py` 中添加函数，然后分别在 `cli.py` 和 `mcp_server.py` 中注册。

## 常用命令

```bash
# 安装
uv sync

# 创建配置文件
cp config_examples.json config.json

# 获取收藏夹列表
uv run zhihu fetch

# 批量导出所有收藏夹
uv run zhihu export-all

# 导出指定收藏夹
uv run zhihu export https://www.zhihu.com/collection/123456789 --name "我的收藏"

# 查看收藏夹信息
uv run zhihu info https://www.zhihu.com/collection/123456789

# 搜索收藏夹
uv run zhihu search "Python"

# 收藏管理
uv run zhihu add <collection_url> <article_url>
uv run zhihu remove <collection_url> <article_url>
uv run zhihu move <from_url> <to_url> <article_url>

# 启动 MCP Server
uv run zhihu-mcp-server

# 测试
uv run pytest
```

## Skill

本项目提供 `zhihu-cli` skill，让 OpenCode Agent 通过 CLI 直接调用 `zhihu` 命令管理知乎收藏夹，代替 MCP Server 来节约内存和 token。

- **源文件**: `.opencode/skills/zhihu-cli/SKILL.md`（纳入版本控制）
- **部署位置**: `~/.agents/skills/zhihu-cli/SKILL.md`

CLI 子命令（`cli.py`）有增删改时，**必须同步更新 `~/.agents/skills/zhihu-cli/SKILL.md`**，确保 Agent 看到的命令文档与 `zhihu --help` 一致。源文件在项目 repo 中，部署时复制即可：

```bash
cp .opencode/skills/zhihu-cli/SKILL.md ~/.agents/skills/zhihu-cli/
```
