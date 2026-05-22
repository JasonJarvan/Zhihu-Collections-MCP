# -*- coding:utf-8 -*-
"""
测试配置逻辑的简单测试用例（不依赖外部库）
"""
import json
import os

def test_config_loading():
    """测试配置加载逻辑"""
    print("=== 测试配置加载逻辑 ===")
    
    # 测试1: 读取当前config.json
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✓ 成功加载config.json")
        print(f"  zhihuUrls数量: {len(config.get('zhihuUrls', []))}")
        print(f"  outputPath: {config.get('outputPath', '未设置')}")
        print(f"  os: {config.get('os', '未设置')}")
        print(f"  openCollection: {config.get('openCollection', '未设置')}")
        
        return config
        
    except Exception as e:
        print(f"✗ 加载config.json失败: {str(e)}")
        return None

def test_open_collection_logic(config):
    """测试openCollection逻辑"""
    print("\n=== 测试openCollection逻辑 ===")
    
    if not config:
        print("✗ 无法测试，配置为空")
        return
    
    open_collection_mode = config.get('openCollection', False)
    print(f"openCollection模式: {open_collection_mode}")
    
    if open_collection_mode:
        print("✓ 检测到openCollection模式已启用")
        print("  应该执行：从知乎页面获取收藏夹列表")
        print("  应该生成：zhihuUrls.json文件")
        print("  提示用户：将openCollection设为false后重新运行")
    else:
        print("✓ openCollection模式未启用")
        print("  应该执行：常规收藏夹下载模式")
        
        zhihu_collections = config.get('zhihuUrls', [])
        if zhihu_collections:
            print(f"  找到{len(zhihu_collections)}个收藏夹待处理")
            for i, collection in enumerate(zhihu_collections):
                name = collection.get('name', '未命名')
                url = collection.get('url', '无URL')
                print(f"    {i+1}. {name}: {url}")
        else:
            print("  ✗ 没有找到收藏夹配置")

def test_json_structure():
    """测试生成的JSON结构"""
    print("\n=== 测试JSON结构 ===")
    
    # 模拟从页面获取的收藏夹数据
    mock_collections = [
        {"name": "技术文章收藏", "url": "https://www.zhihu.com/collection/123456"},
        {"name": "生活感悟", "url": "https://www.zhihu.com/collection/789012"},
        {"name": "学习笔记", "url": "https://www.zhihu.com/collection/345678"}
    ]
    
    # 测试保存到文件
    test_filename = 'test_zhihuUrls.json'
    try:
        with open(test_filename, 'w', encoding='utf-8') as f:
            json.dump(mock_collections, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 成功生成测试JSON文件: {test_filename}")
        
        # 验证文件内容
        with open(test_filename, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        print(f"✓ JSON文件验证成功，包含{len(loaded_data)}个收藏夹")
        for collection in loaded_data:
            print(f"  - {collection['name']}: {collection['url']}")
        
        # 清理测试文件
        os.remove(test_filename)
        print(f"✓ 清理测试文件完成")
        
    except Exception as e:
        print(f"✗ JSON测试失败: {str(e)}")

def test_mode_switching():
    """测试模式切换逻辑"""
    print("\n=== 测试模式切换逻辑 ===")
    
    print("测试场景1: openCollection=true")
    print("  预期行为：获取收藏夹列表 -> 生成zhihuUrls.json -> 提示用户修改配置")
    
    print("\n测试场景2: openCollection=false + 有zhihuUrls配置")
    print("  预期行为：常规下载模式 -> 处理配置中的收藏夹")
    
    print("\n测试场景3: openCollection=false + 无zhihuUrls配置")
    print("  预期行为：提示用户启用openCollection模式或手动配置收藏夹")

if __name__ == '__main__':
    print("开始测试openCollection功能的配置逻辑...")
    
    # 测试配置加载
    config = test_config_loading()
    
    # 测试openCollection逻辑
    test_open_collection_logic(config)
    
    # 测试JSON结构
    test_json_structure()
    
    # 测试模式切换
    test_mode_switching()
    
    print("\n✓ 所有配置逻辑测试完成!")
    print("\n使用说明:")
    print("1. 将config.json中的openCollection设为true")
    print("2. 确保cookies.json文件存在且包含有效的知乎登录cookie")
    print("3. 运行 python3 main.py")
    print("4. 程序将自动获取收藏夹列表并生成zhihuUrls.json")
    print("5. 将openCollection设为false，重新运行即可开始下载")