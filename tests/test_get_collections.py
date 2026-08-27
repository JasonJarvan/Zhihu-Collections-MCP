# -*- coding:utf-8 -*-
"""
测试 fetch_collections 模块的功能
"""
try:
    import sys
    import os
    from zhihu_collections._common import load_cookies
    from zhihu_collections.fetch_collections import (
        get_collections_from_page,
        get_all_collections,
        update_config_with_collections,
        save_collections_log,
    )
    import json
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在项目根目录运行测试")
    sys.exit(1)


def test_load_cookies():
    """测试加载cookies功能"""
    print("=== 测试加载cookies ===")
    try:
        cookies = load_cookies()
        if cookies:
            print(f"✓ 成功加载cookies，包含{len(cookies)}个cookie")
            cookie_names = list(cookies.keys())[:5]
            print(f"  前5个cookie名称: {cookie_names}")
        else:
            print("✓ cookies文件不存在或为空，返回空字典")
        return cookies
    except Exception as e:
        print(f"✗ 加载cookies失败: {str(e)}")
        return {}


def test_update_config(tmp_dir, monkeypatch):
    """测试更新 config.json 功能（pytest 风格）"""
    print("\n=== 测试更新配置文件 ===")

    test_collections = [
        {"name": "测试收藏夹1", "url": "https://www.zhihu.com/collection/123456"},
        {"name": "测试收藏夹2", "url": "https://www.zhihu.com/collection/789012"},
    ]

    config_path = os.path.join(tmp_dir, "config.json")
    monkeypatch.setattr("zhihu_collections.fetch_collections.load_config", lambda: {
        "zhihuUrls": [],
        "openCollection": True,
    })

    import builtins
    original_open = builtins.open

    def mock_open(file, mode="r", **kwargs):
        if file == "config.json":
            return original_open(config_path, mode, **kwargs)
        return original_open(file, mode, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)

    try:
        config = {"zhihuUrls": [], "openCollection": True}
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f)

        success = update_config_with_collections(test_collections)

        with open("config.json", "r", encoding="utf-8") as f:
            updated = json.load(f)

        assert success
        assert updated["zhihuUrls"] == test_collections
        assert updated["openCollection"] is False
        print("✓ 更新配置文件成功，openCollection 已自动设为 false")

    finally:
        if os.path.exists("config.json"):
            os.remove("config.json")


def test_mock_collections():
    """模拟测试收藏夹获取（不进行真实网络请求）"""
    print("\n=== 模拟测试收藏夹获取 ===")

    mock_collections = [
        {"name": "技术学习", "url": "https://www.zhihu.com/collection/111111"},
        {"name": "投资理财", "url": "https://www.zhihu.com/collection/222222"},
        {"name": "生活感悟", "url": "https://www.zhihu.com/collection/333333"},
    ]

    print(f"✓ 模拟获取到{len(mock_collections)}个收藏夹")
    for i, collection in enumerate(mock_collections):
        print(f"  {i+1}. {collection['name']}: {collection['url']}")

    return mock_collections


def test_module_imports():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")

    functions_to_test = [
        "get_collections_from_page",
        "get_all_collections",
        "update_config_with_collections",
        "save_collections_log",
    ]

    for func_name in functions_to_test:
        try:
            func = globals()[func_name]
            print(f"✓ {func_name}: 导入成功")
        except KeyError:
            print(f"✗ {func_name}: 导入失败")


def main():
    """主测试函数"""
    print("开始测试 fetch_collections 模块...")

    test_module_imports()
    test_load_cookies()
    test_mock_collections()

    print(f"\n{'='*50}")
    print("测试完成!")
    print(f"{'='*50}")

    print("\n如何进行真实测试:")
    print("1. 确保cookies.json文件存在且包含有效的知乎登录信息")
    print("2. 运行: uv run zhihu fetch")
    print("3. 运行: uv run zhihu export-all")


if __name__ == "__main__":
    main()
