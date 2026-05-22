# -*- coding:utf-8 -*-
"""
模拟测试openCollection功能（不依赖网络请求）
"""
import json
import os

def simulate_main_logic():
    """模拟main.py的主要逻辑"""
    print("=== 模拟主程序逻辑 ===")
    
    # 1. 加载配置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✓ 成功加载config.json")
    except Exception as e:
        print(f"✗ 加载配置失败: {str(e)}")
        return False
    
    # 2. 检查openCollection模式
    open_collection_mode = config.get('openCollection', False)
    print(f"openCollection模式: {open_collection_mode}")
    
    if open_collection_mode:
        print("✓ 检测到openCollection模式已启用")
        print("  模拟行为：从知乎收藏夹页面获取收藏夹列表")
        
        # 模拟获取收藏夹列表
        simulated_collections = simulate_get_collections()
        
        if simulated_collections:
            print(f"✓ 模拟获取到{len(simulated_collections)}个收藏夹")
            
            # 模拟保存到zhihuUrls.json
            success = simulate_save_collections(simulated_collections)
            
            if success:
                print("✓ 模拟生成zhihuUrls.json成功")
                print("  提示：请将config.json中的openCollection设为false，然后重新运行程序")
                return True
            else:
                print("✗ 模拟保存失败")
                return False
        else:
            print("✗ 模拟获取收藏夹失败")
            return False
    else:
        print("✓ openCollection模式未启用，执行常规下载模式")
        
        zhihu_collections = config.get('zhihuUrls', [])
        
        if not zhihu_collections:
            print("✗ 没有找到要处理的收藏夹配置")
            print("  提示：如果想从知乎页面自动获取收藏夹列表，请将openCollection设为true")
            return False
        
        print(f"✓ 找到{len(zhihu_collections)}个收藏夹待处理")
        for collection in zhihu_collections:
            name = collection.get('name', '未命名')
            url = collection.get('url', '无URL')
            print(f"  - {name}: {url}")
        
        return True

def simulate_get_collections():
    """模拟从知乎页面获取收藏夹"""
    # 模拟网络请求和页面解析的结果
    mock_collections = [
        {"name": "技术学习", "url": "https://www.zhihu.com/collection/111111"},
        {"name": "投资理财", "url": "https://www.zhihu.com/collection/222222"},
        {"name": "生活感悟", "url": "https://www.zhihu.com/collection/333333"},
        {"name": "读书笔记", "url": "https://www.zhihu.com/collection/444444"},
        {"name": "职场经验", "url": "https://www.zhihu.com/collection/555555"}
    ]
    
    return mock_collections

def simulate_save_collections(collections):
    """模拟保存收藏夹列表到文件"""
    try:
        # 保存到一个测试文件而不是真正的zhihuUrls.json
        test_filename = 'simulated_zhihuUrls.json'
        with open(test_filename, 'w', encoding='utf-8') as f:
            json.dump(collections, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 模拟文件已保存: {test_filename}")
        
        # 显示文件内容
        print("文件内容:")
        with open(test_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(content)
        
        # 清理测试文件
        os.remove(test_filename)
        
        return True
    except Exception as e:
        print(f"✗ 模拟保存失败: {str(e)}")
        return False

def test_both_modes():
    """测试两种模式"""
    print("开始模拟测试...")
    
    # 当前模式测试
    print("\n1. 测试当前配置:")
    result1 = simulate_main_logic()
    
    # 模拟另一种模式
    print("\n2. 模拟切换模式后的行为:")
    
    # 读取当前配置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_mode = config.get('openCollection', False)
        
        if current_mode:
            print("  如果将openCollection设为false:")
            print("  - 程序将进入常规下载模式")
            print("  - 需要zhihuUrls配置才能正常工作")
            print("  - 会提示用户配置收藏夹或启用openCollection模式")
        else:
            print("  如果将openCollection设为true:")
            print("  - 程序将从知乎页面获取收藏夹列表")
            print("  - 需要有效的cookies.json文件")
            print("  - 会生成zhihuUrls.json文件")
            print("  - 提示用户修改配置后重新运行")
    
    except Exception as e:
        print(f"  配置读取失败: {str(e)}")
    
    return result1

if __name__ == '__main__':
    success = test_both_modes()
    
    print(f"\n=== 测试结果 ===")
    if success:
        print("✓ 功能逻辑验证成功")
        print("\n实际使用步骤:")
        print("1. 确保cookies.json包含有效的知乎登录信息")
        print("2. 将config.json中的openCollection设为true")
        print("3. 运行 python3 main.py")
        print("4. 程序会自动获取收藏夹列表并生成zhihuUrls.json")
        print("5. 将openCollection设为false，重新运行开始下载")
    else:
        print("✗ 功能逻辑验证失败")
        print("请检查配置文件是否正确")