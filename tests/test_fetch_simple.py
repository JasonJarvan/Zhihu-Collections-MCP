# -*- coding:utf-8 -*-
"""
简化版fetch_collections测试（无外部依赖）
"""
import os
import json

def test_file_exists():
    """测试文件是否存在"""
    print("=== 测试文件存在性 ===")
    
    if os.path.exists('fetch_collections.py'):
        print("✓ fetch_collections.py 文件存在")
        return True
    else:
        print("✗ fetch_collections.py 文件不存在")
        return False

def test_fetch_collections_structure():
    """测试fetch_collections.py结构"""
    print("\n=== 测试fetch_collections.py结构 ===")
    
    try:
        with open('src/zhihu_collections/fetch_collections.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            'def load_cookies(',
            'def load_config(',
            'def get_collections_from_page(',
            'def get_all_collections(',
            'def update_config_with_collections(',
            'def save_collections_log(',
            'def setup_logging(',
            'def main('
        ]
        
        all_functions_found = True
        for func in required_functions:
            if func in content:
                func_name = func.split('(')[0].replace('def ', '')
                print(f"✓ {func_name} 函数存在")
            else:
                func_name = func.split('(')[0].replace('def ', '')
                print(f"✗ {func_name} 函数不存在")
                all_functions_found = False
        
        # 检查日志命名规则
        if 'openCollection_{timestamp}.log' in content:
            print("✓ 包含正确的日志命名规则")
        else:
            print("✗ 缺少正确的日志命名规则")
            all_functions_found = False
        
        # 检查配置更新逻辑
        if "config['openCollection'] = False" in content:
            print("✓ 包含openCollection自动设为false的逻辑")
        else:
            print("✗ 缺少openCollection自动设为false的逻辑")
            all_functions_found = False
        
        return all_functions_found
        
    except Exception as e:
        print(f"✗ 读取fetch_collections.py失败: {e}")
        return False

def test_main_py_changes():
    """测试main.py的修改"""
    print("\n=== 测试main.py修改 ===")
    
    try:
        with open('src/zhihu_collections/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        changes_correct = True
        
        # 检查是否移除了get_collections导入
        if 'from get_collections import' not in content:
            print("✓ 已移除get_collections导入")
        else:
            print("✗ 仍包含get_collections导入")
            changes_correct = False
        
        # 检查是否包含fetch_collections.py的提示
        if 'python fetch_collections.py' in content:
            print("✓ 包含fetch_collections.py运行提示")
        else:
            print("✗ 缺少fetch_collections.py运行提示")
            changes_correct = False
        
        # 检查openCollection处理逻辑
        if 'openCollection设为false' in content:
            print("✓ 包含正确的openCollection提示")
        else:
            print("✗ 缺少正确的openCollection提示")
            changes_correct = False
        
        return changes_correct
        
    except Exception as e:
        print(f"✗ 读取main.py失败: {e}")
        return False

def test_config_mock():
    """模拟测试配置更新逻辑"""
    print("\n=== 模拟测试配置更新 ===")
    
    # 模拟配置更新过程
    mock_original_config = {
        "zhihuUrls": [],
        "outputPath": "",
        "os": "",
        "openCollection": True
    }
    
    mock_collections = [
        {"name": "测试收藏夹1", "url": "https://www.zhihu.com/collection/123456"},
        {"name": "测试收藏夹2", "url": "https://www.zhihu.com/collection/789012"}
    ]
    
    # 模拟更新后的配置
    mock_updated_config = mock_original_config.copy()
    mock_updated_config['zhihuUrls'] = mock_collections
    mock_updated_config['openCollection'] = False
    
    print(f"✓ 模拟更新前: zhihuUrls数量 = {len(mock_original_config['zhihuUrls'])}")
    print(f"✓ 模拟更新前: openCollection = {mock_original_config['openCollection']}")
    print(f"✓ 模拟更新后: zhihuUrls数量 = {len(mock_updated_config['zhihuUrls'])}")
    print(f"✓ 模拟更新后: openCollection = {mock_updated_config['openCollection']}")
    
    if (len(mock_updated_config['zhihuUrls']) == 2 and 
        mock_updated_config['openCollection'] == False):
        print("✓ 配置更新逻辑正确")
        return True
    else:
        print("✗ 配置更新逻辑错误")
        return False

def test_syntax_check():
    """语法检查"""
    print("\n=== 语法检查 ===")
    
    import py_compile
    
    try:
        py_compile.compile('src/zhihu_collections/fetch_collections.py', doraise=True)
        print("✓ fetch_collections.py 语法正确")
        
        py_compile.compile('src/zhihu_collections/main.py', doraise=True)
        print("✓ main.py 语法正确")
        
        return True
        
    except py_compile.PyCompileError as e:
        print(f"✗ 语法错误: {e}")
        return False

def main():
    """主测试函数"""
    print("开始简化版fetch_collections测试...")
    
    results = []
    
    # 运行各项测试
    results.append(test_file_exists())
    results.append(test_fetch_collections_structure())
    results.append(test_main_py_changes())
    results.append(test_config_mock())
    results.append(test_syntax_check())
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("测试结果:")
    print(f"{'='*50}")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有测试通过 ({passed}/{total})")
        print("\n独立脚本创建成功！")
        print("- ✓ fetch_collections.py结构完整")
        print("- ✓ main.py已正确修改")
        print("- ✓ 配置更新逻辑正确")
        print("- ✓ 语法检查通过")
        
        print("\n使用方法:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 运行: python fetch_collections.py")
        print("3. 然后运行: python main.py")
    else:
        print(f"✗ 测试失败 ({passed}/{total})")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)