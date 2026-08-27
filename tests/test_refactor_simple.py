# -*- coding:utf-8 -*-
"""
简化版重构验证测试（不依赖外部库）
"""
import os
import sys

def test_file_structure():
    """测试文件结构"""
    print("=== 测试文件结构 ===")
    
    expected_files = [
        'get_collections.py',
        'main.py', 
        'config.json',
        'test/test_config_logic.py',
        'test/test_simulation.py',
        'test/test_open_collection.py',
        'test/test_get_collections.py',
        'test/README.md',
        'test/__init__.py'
    ]
    
    all_exist = True
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist

def test_module_structure():
    """测试模块结构"""
    print("\n=== 测试模块结构 ===")
    
    try:
        # 检查get_collections.py内容
        with open('get_collections.py', 'r', encoding='utf-8') as f:
            get_collections_content = f.read()
        
        required_functions = [
            'def load_cookies(',
            'def get_collections_from_page(',
            'def get_all_collections(',
            'def save_collections_to_json(',
            'def process_open_collection_mode('
        ]
        
        all_functions_exist = True
        for func in required_functions:
            if func in get_collections_content:
                print(f"✓ get_collections.py包含{func.split('(')[0]}函数")
            else:
                print(f"✗ get_collections.py缺少{func.split('(')[0]}函数")
                all_functions_exist = False
        
        return all_functions_exist
        
    except FileNotFoundError:
        print("✗ get_collections.py文件不存在")
        return False

def test_main_imports():
    """测试main.py导入"""
    print("\n=== 测试main.py导入 ===")
    
    try:
        with open('src/zhihu_collections/main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        if 'from get_collections import process_open_collection_mode' in main_content:
            print("✓ main.py正确导入get_collections模块")
            return True
        else:
            print("✗ main.py未正确导入get_collections模块")
            return False
            
    except FileNotFoundError:
        print("✗ main.py文件不存在")
        return False

def test_config_integration():
    """测试配置集成"""
    print("\n=== 测试配置集成 ===")
    
    try:
        import json
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'openCollection' in config:
            print("✓ config.json包含openCollection属性")
            print(f"  当前值: {config['openCollection']}")
            return True
        else:
            print("✗ config.json缺少openCollection属性")
            return False
            
    except FileNotFoundError:
        print("✗ config.json文件不存在")
        return False
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def test_removed_functions():
    """测试main.py中是否已移除相关函数"""
    print("\n=== 测试函数移除情况 ===")
    
    try:
        with open('src/zhihu_collections/main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        removed_functions = [
            'def get_collections_from_page(',
            'def get_all_collections(',
            'def save_collections_to_json('
        ]
        
        all_removed = True
        for func in removed_functions:
            if func in main_content:
                print(f"✗ main.py仍包含{func.split('(')[0]}函数（应该已移除）")
                all_removed = False
            else:
                print(f"✓ main.py已移除{func.split('(')[0]}函数")
        
        return all_removed
        
    except FileNotFoundError:
        print("✗ main.py文件不存在")
        return False

def main():
    """主测试函数"""
    print("开始简化版重构验证...")
    
    results = []
    
    # 运行各项测试
    results.append(test_file_structure())
    results.append(test_module_structure())
    results.append(test_main_imports())
    results.append(test_config_integration())
    results.append(test_removed_functions())
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("重构验证结果:")
    print(f"{'='*50}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✓ 重构成功！所有测试都通过")
        print("\n重构成果:")
        print("- ✓ 成功创建get_collections.py模块")
        print("- ✓ 从main.py中移除相关函数，实现松耦合")
        print("- ✓ 正确设置模块导入")
        print("- ✓ 测试文件已移动到test/目录")
        print("- ✓ 创建了完整的测试文档")
    else:
        print("✗ 重构存在问题，请检查失败的测试项")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)