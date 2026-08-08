---
name: zhihu-cli
description: 管理知乎收藏夹 — 列出、导出、搜索、收藏/取消收藏/移动文章。用 zhihu <子命令> 操作。
allowed-tools: Bash(zhihu:*)
---

# 知乎收藏夹管理 CLI

用 `zhihu` 命令管理知乎收藏夹。支持导出为 Markdown、收藏/取消收藏/移动文章。

## 快速开始

```bash
zhihu list                                  # 列出所有收藏夹
zhihu export <收藏夹URL>                     # 导出单个收藏夹
zhihu fetch                                 # 自动获取收藏夹列表写入 config.json
```

## 前置条件

- `config.json` 存在（复制自 `config_examples.json`，含 `zhihuUrls`、`outputPath`、`markdownFormat` 等字段）
- `cookies.json` 存在（复制自 `cookies_examples.json`，含知乎登录 cookies）
- `outputPath` 优先级: CLI `--output` > `ZHIHU_OUTPUT_PATH` 环境变量 > `config.json` 的 `outputPath` > `downloads/`

## 子命令

### list — 列出收藏夹

```bash
zhihu list
```

### export — 导出单个收藏夹

```bash
zhihu export <url>                          # 基本用法
zhihu export <url> --name "收藏夹名"         # 指定输出目录名
zhihu export <url> -o ./output              # 指定输出目录
zhihu export <url> --overwrite              # 覆盖不完整文件
zhihu export <url> --max-articles 10        # 只导出最新10篇
zhihu export <url> -n "名称" -o ./out --overwrite --max-articles 20
```

### export-all — 批量导出所有收藏夹

```bash
zhihu export-all                            # 导出 config.json 中所有收藏夹
zhihu export-all -o ./output                # 指定输出目录
```

导出完成会打印汇总报告并保存日志到 `logs/` 目录。

### info — 查看收藏夹信息

```bash
zhihu info <url>                            # 显示文章数量、前5篇标题
```

### search — 搜索收藏夹

```bash
zhihu search "Python"                       # 按名称/URL搜索（不区分大小写）
zhihu search "技术"
```

### add — 收藏一篇文章

```bash
zhihu add <收藏夹URL> <文章URL>
# 支持: 回答 /question/xxx/answer/yyy、专栏 /p/xxx、视频 /zvideo/xxx、想法 /pin/xxx
```

### remove — 取消收藏一篇文章

```bash
zhihu remove <收藏夹URL> <文章URL>
```

### move — 移动文章到另一个收藏夹

```bash
zhihu move <源收藏夹URL> <目标收藏夹URL> <文章URL>
# 先添加至目标，再从源移除，最后验证（不丢失内容）
```

### fetch — 自动获取收藏夹列表

```bash
zhihu fetch                                 # 抓取所有收藏夹并更新 config.json
```

## 典型工作流

### 导出工作流

```bash
zhihu fetch                                 # 1. 获取收藏夹列表
zhihu list                                  # 2. 确认列表
zhihu export-all                            # 3. 批量导出
# 或单个导出
zhihu export <url> --name "名称" -o ./dir
```

### 整理收藏夹

```bash
zhihu list                                  # 1. 查看所有收藏夹
zhihu search "关键词"                        # 2. 搜索目标收藏夹
zhihu move <from> <to> <article_url>        # 3. 移动文章
zhihu remove <collection> <article_url>     # 4. 删除不需要的
```

### AI Agent 常见工作流

```bash
# 用户说"导出收藏夹"
zhihu fetch && zhihu export-all

# 用户说"搜索XX收藏夹并导出"
zhihu search "Python"                       # 找到 url
zhihu info <url>                            # 查看信息
zhihu export <url> --name "Python收藏"      # 导出

# 用户说"把这篇文章移到另一个收藏夹"
zhihu move <from> <to> <article_url>

# 用户说"收藏这篇文章"
zhihu add <collection> <article_url>
```

## 输出格式

```bash
<outputPath>/<收藏夹名>/
├── 文章1.md
├── 文章2.md
├── ...
└── assets/
    ├── image1.png
    └── image2.jpg
```

Markdown 格式由 `config.json` 的 `markdownFormat` 控制：`"obsidian"`（`![[image]]`）或 `"standard"`（`![alt](path)`）。

## 错误处理

- 网络失败 → 打印错误信息，exit code 非零
- 单篇文章失败 → 不影响其他文章，日志记录后继续
- 无 cookies → 无登录模式，仅能访问公开内容
- 无 config.json → 提示创建配置文件
