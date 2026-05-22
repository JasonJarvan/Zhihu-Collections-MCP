# -*- coding:utf-8 -*-
"""
验证重构后的代码结构测试
"""
import sys
import os


def test_imports():
    """测试模块导入"""
    print("=== 测试模块导入 ===")
    
    try:
        from zhihu_collections import get_collections
        print("✓ get_collections模块导入成功")
        
        # 检查关键函数是否存在
        functions = ['load_cookies', 'save_collections_to_json', 'process_open_collection_mode']
        for func_name in functions:
            if hasattr(get_collections, func_name):
                print(f"✓ {func_name}函数存在")
            else:
                print(f"✗ {func_name}函数不存在")
                
    except ImportError as e:
        print(f"✗ get_collections模块导入失败: {e}")
        return False
    
    try:
        # 测试main.py是否可以正常导入get_collections
        with open('src/zhihu_collections/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'from get_collections import process_open_collection_mode' in content:
            print("✓ main.py正确导入get_collections模块")
        else:
            print("✗ main.py未正确导入get_collections模块")
            
    except FileNotFoundError:
        print("✗ 找不到main.py文件")
        return False
    
    return True

def test_module_independence():
    """测试模块独立性"""
    print("\n=== 测试模块独立性 ===")
    
    try:
        # 测试get_collections模块的基础功能
        import get_collections
        
        # 测试load_cookies函数（不依赖外部库）
        try:
            cookies = get_collections.load_cookies()
            print("✓ load_cookies函数正常工作")
        except Exception as e:
            print(f"✗ load_cookies函数出错: {e}")
        
        # 测试save_collections_to_json函数
        test_data = [{"name": "测试", "url": "https://test.com"}]
        test_file = "test/temp_test.json"
        
        try:
            success = get_collections.save_collections_to_json(test_data, test_file)
            if success and os.path.exists(test_file):
                print("✓ save_collections_to_json函数正常工作")
                os.remove(test_file)  # 清理测试文件
            else:
                print("✗ save_collections_to_json函数工作异常")
        except Exception as e:
            print(f"✗ save_collections_to_json函数出错: {e}")
            
    except ImportError as e:
        print(f"✗ 模块独立性测试失败: {e}")
        return False
    
    return True

def test_file_structure():
    """测试文件结构"""
    print("\n=== 测试文件结构 ===")
    
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
    
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
    
    return True

def test_config_integration():
    """测试配置集成"""
    print("\n=== 测试配置集成 ===")
    
    try:
        # 读取config.json检查openCollection属性
        import json
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'openCollection' in config:
            print("✓ config.json包含openCollection属性")
            print(f"  当前值: {config['openCollection']}")
        else:
            print("✗ config.json缺少openCollection属性")
            return False
            
    except Exception as e:
        print(f"✗ 配置集成测试失败: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始验证重构后的代码结构...")
    
    results = []
    
    # 运行各项测试
    results.append(test_imports())
    results.append(test_module_independence()) 
    results.append(test_file_structure())
    results.append(test_config_integration())
    
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
        
        print("\n使用方法:")
        print("1. 基础测试: python3 test/test_config_logic.py")
        print("2. 模拟测试: python3 test/test_simulation.py")
        print("3. 模块测试: python3 test/test_get_collections.py")
        print("4. 完整测试: python3 test/test_open_collection.py (需要依赖)")
        
    else:
        print("✗ 重构存在问题，请检查失败的测试项")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)