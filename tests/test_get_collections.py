# -*- coding:utf-8 -*-
"""
测试get_collections模块的功能
"""
try:
    import sys
    import os
    from zhihu_collections.get_collections import (
        load_cookies,
        get_collections_from_page,
        get_all_collections,
        save_collections_to_json,
        process_open_collection_mode
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
            # 显示部分cookie名称（不显示值保护隐私）
            cookie_names = list(cookies.keys())[:5]
            print(f"  前5个cookie名称: {cookie_names}")
        else:
            print("✓ cookies文件不存在或为空，返回空字典")
        return cookies
    except Exception as e:
        print(f"✗ 加载cookies失败: {str(e)}")
        return {}


def test_save_collections():
    """测试保存收藏夹列表功能"""
    print("\n=== 测试保存收藏夹列表 ===")
    
    # 测试数据
    test_collections = [
        {"name": "测试收藏夹1", "url": "https://www.zhihu.com/collection/123456"},
        {"name": "测试收藏夹2", "url": "https://www.zhihu.com/collection/789012"}
    ]
    
    test_filename = 'test/test_collections_output.json'
    
    try:
        success = save_collections_to_json(test_collections, test_filename)
        
        if success:
            print("✓ 保存测试收藏夹列表成功")
            
            # 验证文件内容
            with open(test_filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            if loaded_data == test_collections:
                print("✓ 文件内容验证成功")
            else:
                print("✗ 文件内容验证失败")
            
            # 清理测试文件
            os.remove(test_filename)
            print("✓ 清理测试文件完成")
        else:
            print("✗ 保存测试收藏夹列表失败")
            
    except Exception as e:
        print(f"✗ 测试保存功能失败: {str(e)}")


def test_mock_collections():
    """模拟测试收藏夹获取（不进行真实网络请求）"""
    print("\n=== 模拟测试收藏夹获取 ===")
    
    # 模拟收藏夹数据
    mock_collections = [
        {"name": "技术学习", "url": "https://www.zhihu.com/collection/111111"},
        {"name": "投资理财", "url": "https://www.zhihu.com/collection/222222"},
        {"name": "生活感悟", "url": "https://www.zhihu.com/collection/333333"}
    ]
    
    print(f"✓ 模拟获取到{len(mock_collections)}个收藏夹")
    for i, collection in enumerate(mock_collections):
        print(f"  {i+1}. {collection['name']}: {collection['url']}")
    
    return mock_collections


def test_module_imports():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    functions_to_test = [
        'load_cookies',
        'get_collections_from_page', 
        'get_all_collections',
        'save_collections_to_json',
        'process_open_collection_mode'
    ]
    
    for func_name in functions_to_test:
        try:
            func = globals()[func_name]
            print(f"✓ {func_name}: 导入成功")
        except KeyError:
            print(f"✗ {func_name}: 导入失败")


def test_integration():
    """集成测试（模拟完整流程）"""
    print("\n=== 集成测试 ===")
    
    print("模拟完整的openCollection流程:")
    print("1. 加载cookies...")
    cookies = test_load_cookies()
    
    print("\n2. 模拟获取收藏夹列表...")
    mock_collections = test_mock_collections()
    
    print("\n3. 测试保存功能...")
    test_save_collections()
    
    print("\n✓ 模拟流程完成")
    print("  实际使用时，get_collections_from_page 和 get_all_collections 会进行网络请求")


def main():
    """主测试函数"""
    print("开始测试get_collections模块...")
    
    # 测试模块导入
    test_module_imports()
    
    # 测试各个功能
    test_load_cookies()
    test_save_collections()
    test_mock_collections()
    
    # 集成测试
    test_integration()
    
    print(f"\n{'='*50}")
    print("测试完成!")
    print(f"{'='*50}")
    
    print("\n如何进行真实测试:")
    print("1. 确保cookies.json文件存在且包含有效的知乎登录信息")
    print("2. 运行: python3 -c \"from get_collections import process_open_collection_mode; process_open_collection_mode()\"")
    print("3. 或者直接运行: python3 get_collections.py")


if __name__ == '__main__':
    main()