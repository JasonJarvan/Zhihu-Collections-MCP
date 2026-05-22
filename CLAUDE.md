# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 重要规则
- **始终使用中文回答**
- 在处理此项目时，所有交流都应使用中文

## 项目概述

Export-Zhihu-Collections 是一个将知乎收藏夹导出为 Markdown 格式的 Python 工具。该工具支持公开和私密收藏夹，可批量处理多个收藏夹，支持自定义输出路径，可下载内嵌图片，并将 HTML 内容转换为 Obsidian 兼容的 Markdown 格式。

项目使用 **src-layout** 结构，以 **uv** 作为包管理器。

## 核心组件

### 主要架构
- **src/zhihu_collections/main.py**: 包含收藏夹导出逻辑的主脚本
  - `load_config()`: 加载和解析配置文件
  - `parse_output_path()`: 跨平台路径解析和处理
  - `get_article_urls_in_collection()`: 使用知乎 API 获取收藏夹中的所有 URL
  - `get_single_answer_content()`: 从问答页面提取回答内容（增强版，支持多种页面结构）
  - `get_single_post_content()`: 从专栏文章提取内容（增强版，支持多种页面结构）
  - `process_single_collection()`: 处理单个收藏夹的完整流程
  - `flush_logs()`: 实时日志刷新功能
  - `setup_debug_logging()`: 调试日志配置
  - `get_debug_path()`: 获取调试文件保存路径
  - `ObsidianStyleConverter`: 用于 Obsidian 风格输出的自定义 MarkdownConverter
- **src/zhihu_collections/fetch_collections.py**: 独立的收藏夹获取脚本
- **src/zhihu_collections/mcp_server.py**: MCP Server 入口
- **src/zhihu_collections/favorite_ops.py**: 收藏/取消收藏/移动操作
- **src/zhihu_collections/utils.py**: 包含用于文件名清理的 `filter_title_str()` 函数
- **config.json**: 主配置文件，包含收藏夹列表、输出路径和系统设置
- **cookies.json**: 访问私密收藏夹的认证 cookies
- **tests/**: 测试文件目录

### 数据流程
1. 加载配置文件 (config.json 或 zhihuUrls.json)
2. 解析和验证输出路径，支持多种操作系统格式
3. 批量处理多个收藏夹：
   - 解析收藏夹 URL 提取收藏夹 ID
   - 使用知乎 API 获取收藏夹中的所有项目（分页处理，使用 offset/limit）
   - 对每个项目，判断类型（回答或文章）并获取内容
   - 检查文件是否已存在，避免重复下载
   - 使用自定义转换器将 HTML 转换为 Markdown
   - 下载并保存图片到 assets 文件夹
   - 使用清理后的文件名保存 Markdown 文件
4. 生成详细的处理日志并保存到 logs 目录

## 常用命令

### 安装和设置
```bash
# 安装依赖（使用 uv）
uv sync

# 可编辑安装，使命令行入口可用
uv pip install -e .
```

### 配置和运行
```bash
# 1. 创建配置文件
cp config_examples.json config.json
# 编辑 config.json，添加你的收藏夹信息

# 2. 运行导出工具（批量处理）
uv run zhihu-export

# 3. 运行 MCP Server
uv run zhihu-mcp-server

# 4. 获取收藏夹列表
uv run zhihu-fetch
```

### 测试
```bash
uv run pytest
```

### 配置文件格式
```json
{
  "zhihuUrls": [
    {
      "name": "收藏夹名称",
      "url": "https://www.zhihu.com/collection/123456789"
    }
  ],
  "outputPath": "自定义输出路径（可选）",
  "os": "操作系统类型（可选，支持自动检测）"
}
```

### 依赖包
主要包（在 pyproject.toml 中声明）：
- `requests`: 向知乎 API 发送 HTTP 请求
- `beautifulsoup4`: HTML 解析
- `markdownify`: HTML 到 Markdown 转换
- `tqdm`: 进度条
- `lxml`: XML/HTML 解析器后端
- `mcp`: MCP 协议支持

## 文件结构

```
/
├── src/
│   └── zhihu_collections/  # Python 包
│       ├── __init__.py
│       ├── main.py         # 主导出脚本
│       ├── utils.py        # 工具函数
│       ├── fetch_collections.py
│       ├── get_collections.py
│       ├── mcp_server.py   # MCP Server
│       ├── export_all.py   # 批量导出
│       ├── favorite_ops.py # 收藏操作
│       ├── debug_page.py   # 调试脚本
│       └── analyze_issue.py
├── tests/                  # 测试文件目录
│   ├── README.md
│   ├── __init__.py
│   └── test_*.py
├── pyproject.toml          # uv 项目配置
├── config.json             # 主配置文件
├── config_examples.json    # 配置示例文件
├── zhihuUrls.json          # 旧版URL列表（向后兼容）
├── cookies.json            # 认证 cookies（可选）
└── downloads/              # 默认输出目录
    ├── 收藏夹名称1/         # 按收藏夹名称分类的输出目录
    │   ├── *.md            # 导出的 markdown 文件
    │   └── assets/         # 下载的图片
    ├── 收藏夹名称2/
    ├── logs/               # 处理日志文件
    │   ├── debug_*.log     # 调试日志
    │   └── *.json          # 处理结果日志
    └── debug/              # 调试HTML文件
        ├── debug_answer_*.html
        └── debug_post_*.html
```

## 认证

对于私密收藏夹，需要创建包含知乎会话 cookies 的 `cookies.json` 文件：
```json
[
  {"name": "cookie_name", "value": "cookie_value"},
  ...
]
```

如果 cookies 不可用，工具会优雅地回退到未认证模式。

## 功能特性

### 核心功能
- **批量处理**: 支持同时处理多个收藏夹
- **自定义输出**: 支持用户指定输出目录，支持多种操作系统路径格式
- **跨平台兼容**: 支持 Windows、Linux、macOS、FreeBSD、Solaris、Cygwin 等系统
- **智能去重**: 检查已存在文件，避免重复下载
- **详细日志**: 生成处理日志，记录每篇文章的下载状态
- **实时日志**: 支持实时日志刷新，立即显示处理进度
- **自动收藏夹获取**: 通过 `zhihu-fetch` 命令自动获取用户收藏夹列表

### 内容处理
- 图片使用 Obsidian 风格的 `![[filename]]` 语法下载和引用
- 链接卡片转换为带有卡片标题的纯文本
- 引用和脚注经过处理以符合正确的 Markdown 格式
- 文件名经过清理以兼容文件系统
- 每个导出的文件顶部都包含原始 URL 作为引用块
- 处理重复标题文件，自动添加URL ID后缀

### 错误处理和调试
- **健壮的错误处理**: 单个文章失败不影响整体处理流程
- **增强的HTML解析**: 支持多种知乎页面结构变化
- **调试文件生成**: 自动保存无法解析的页面HTML到 `downloads/debug/` 目录
- **详细错误日志**: 记录具体的错误信息和堆栈跟踪
- **自动重试机制**: 对网络错误进行适当的重试
