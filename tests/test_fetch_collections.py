# -*- coding:utf-8 -*-
"""
测试fetch_collections.py独立脚本
"""
import sys
import os
import json

def test_fetch_collections_import():
    """测试fetch_collections模块导入"""
    print("=== 测试fetch_collections模块导入 ===")
    
    try:
        from zhihu_collections import fetch_collections
        
        # 检查关键函数是否存在
        required_functions = [
            'load_cookies',
            'load_config',
            'get_collections_from_page',
            'get_all_collections',
            'update_config_with_collections',
            'save_collections_log',
            'setup_logging'
        ]
        
        all_functions_exist = True
        for func_name in required_functions:
            if hasattr(fetch_collections, func_name):
                print(f"✓ {func_name} 函数存在")
            else:
                print(f"✗ {func_name} 函数不存在")
                all_functions_exist = False
        
        return all_functions_exist
        
    except ImportError as e:
        print(f"✗ 导入fetch_collections失败: {e}")
        return False

def test_config_update_logic():
    """测试配置更新逻辑"""
    print("\n=== 测试配置更新逻辑 ===")
    
    try:
        import fetch_collections
        
        # 创建测试配置
        test_config = {
            "zhihuUrls": [
                {"name": "旧收藏夹", "url": "https://old.url"}
            ],
            "outputPath": "",
            "os": "",
            "openCollection": True
        }
        
        # 模拟收藏夹数据
        mock_collections = [
            {"name": "测试收藏夹1", "url": "https://www.zhihu.com/collection/123456"},
            {"name": "测试收藏夹2", "url": "https://www.zhihu.com/collection/789012"}
        ]
        
        # 创建临时配置文件
        test_config_path = 'test_config_temp.json'
        with open(test_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        # 备份原始配置
        original_config_path = 'config.json'
        backup_config_path = 'config_backup_temp.json'
        
        if os.path.exists(original_config_path):
            os.rename(original_config_path, backup_config_path)
        
        # 移动测试配置到正确位置
        os.rename(test_config_path, original_config_path)
        
        # 测试更新功能
        success = fetch_collections.update_config_with_collections(mock_collections)
        
        if success:
            # 验证更新结果
            with open(original_config_path, 'r', encoding='utf-8') as f:
                updated_config = json.load(f)
            
            if (updated_config['zhihuUrls'] == mock_collections and 
                updated_config['openCollection'] == False):
                print("✓ 配置更新逻辑正确")
                print(f"  - zhihuUrls已更新为{len(mock_collections)}个收藏夹")
                print("  - openCollection已设为false")
                result = True
            else:
                print("✗ 配置更新内容不正确")
                result = False
        else:
            print("✗ 配置更新失败")
            result = False
        
        # 恢复原始配置
        os.remove(original_config_path)
        if os.path.exists(backup_config_path):
            os.rename(backup_config_path, original_config_path)
        
        return result
        
    except Exception as e:
        print(f"✗ 配置更新测试失败: {e}")
        
        # 清理并恢复
        try:
            if os.path.exists('test_config_temp.json'):
                os.remove('test_config_temp.json')
            if os.path.exists('config_backup_temp.json'):
                if os.path.exists('config.json'):
                    os.remove('config.json')
                os.rename('config_backup_temp.json', 'config.json')
        except:
            pass
        
        return False

def test_logging_setup():
    """测试日志设置"""
    print("\n=== 测试日志设置 ===")
    
    try:
        import fetch_collections
        
        # 测试日志设置
        log_path = fetch_collections.setup_logging()
        
        if log_path and log_path.endswith('.log'):
            print(f"✓ 日志设置成功: {os.path.basename(log_path)}")
            print(f"  日志文件遵循命名规则: openCollection_{{时间戳}}.log")
            
            # 检查日志文件是否创建
            if os.path.exists(log_path):
                print("✓ 日志文件已创建")
                return True
            else:
                print("✗ 日志文件未创建")
                return False
        else:
            print("✗ 日志设置失败")
            return False
            
    except Exception as e:
        print(f"✗ 日志设置测试失败: {e}")
        return False

def test_main_py_openCollection_handling():
    """测试main.py对openCollection的处理"""
    print("\n=== 测试main.py的openCollection处理 ===")
    
    try:
        # 读取main.py内容
        with open('src/zhihu_collections/main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        # 检查是否包含正确的提示信息
        expected_messages = [
            'python fetch_collections.py',
            'openCollection设为false'
        ]
        
        all_messages_found = True
        for message in expected_messages:
            if message in main_content:
                print(f"✓ 找到提示信息: {message}")
            else:
                print(f"✗ 未找到提示信息: {message}")
                all_messages_found = False
        
        # 检查是否移除了process_open_collection_mode导入
        if 'from get_collections import process_open_collection_mode' not in main_content:
            print("✓ 已移除get_collections导入")
        else:
            print("✗ 仍包含get_collections导入")
            all_messages_found = False
        
        return all_messages_found
        
    except Exception as e:
        print(f"✗ main.py检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试fetch_collections独立脚本...")
    
    results = []
    
    # 运行各项测试
    results.append(test_fetch_collections_import())
    results.append(test_config_update_logic())
    results.append(test_logging_setup())
    results.append(test_main_py_openCollection_handling())
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("测试结果:")
    print(f"{'='*50}")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有测试通过 ({passed}/{total})")
        print("\n独立脚本创建成功！")
        print("- ✓ fetch_collections.py功能完整")
        print("- ✓ 配置更新逻辑正确")
        print("- ✓ 日志功能正常")
        print("- ✓ main.py已正确修改")
        
        print("\n使用方法:")
        print("1. 运行 python fetch_collections.py 获取收藏夹列表")
        print("2. 运行 python main.py 下载收藏夹内容")
    else:
        print(f"✗ 测试失败 ({passed}/{total})")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)