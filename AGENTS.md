# AGENTS.md

## Toolchain

- **Package manager**: `uv` (not pip). Install: `uv sync`. Dev deps: `uv sync --group dev`.
- **CLI entrypoints** (defined in `pyproject.toml`):
  - `uv run zhihu-export` — export collections to Markdown
  - `uv run zhihu-mcp-server` — start MCP stdio server
  - `uv run zhihu-fetch` — auto-fetch collection list into config
- **Test**: `uv run pytest` (pytest config in `pyproject.toml`, `testpaths = ["tests"]`). Some `tests/test_*.py` are standalone scripts run with `python3 tests/test_*.py` (not pytest).
- **Build**: hatchling (`pyproject.toml:build-system`)
- **Python**: >= 3.10

## Project structure

- **src-layout**: all code under `src/zhihu_collections/`
- **Private modules** (prefixed `_`): `_common`, `_logging`, `_headers`, `_paths`, `_converter`, `_content`, `_collection`, `_export`. These are internal; prefer importing from `zhihu_collections` (`__init__.py` re-exports the key APIs) or from the public modules directly.
- **Public modules**: `main.py`, `mcp_server.py`, `favorite_ops.py`, `fetch_collections.py`, `get_collections.py`, `utils.py`

## Config & auth

- `config.json` is gitignored; copy from `config_examples.json`. Fields: `zhihuUrls[]` (name + url), `outputPath`, `os`, `openCollection` (bool), `markdownFormat` (`"obsidian"` / `"standard"`).
- `outputPath` can be overridden in MCP client config via `ZHIHU_OUTPUT_PATH` env var (see MCP Server section).
- `cookies.json` is gitignored; copy from `cookies_example.json`. Accepts either simple `[{name, value}]` or full browser-export format (with `domain`, `path`, etc.).
- Both `downloads/` and `blogs/` directories are gitignored output artifacts.

## MCP Server

- Async, stdio transport (`mcp` library + `mcp.server.stdio.stdio_server`).
- Entry: `zhihu_collections.mcp_server:main` (invoked via `uv run zhihu-mcp-server`).
- Tools: `list_collections`, `export_collection`, `get_collection_info`, `search_collections`, `remove_from_collection`, `add_to_collection`, `move_to_collection`.
- `outputPath` priority for `export_collection`: tool arg `output_dir` > `ZHIHU_OUTPUT_PATH` env var > `config.json` `outputPath` > `downloads/`. In MCP client config, set `ZHIHU_OUTPUT_PATH` under the server's `env` field to override the default output directory.

## Architecture notes

- Config loaded by `_common.load_config()`. Output path resolved by `_paths.get_output_path()` (defaults to `downloads/`).
- Collection processing in `_collection.process_single_collection()`. Content fetching in `_content` (supports answer pages, posts, API fallback on 403).
- Markdown conversion uses `markdownify` library; `_converter.markdownify()` applies Obsidian-style `![[image]]` or standard image syntax.
- Image files saved to `assets/` subdirectory per collection. Filenames cleaned via `utils.filter_title_str()`. Duplicate titles get URL ID suffix appended.
- Debug HTML saved to `downloads/debug/` when parsing fails.
