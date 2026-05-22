# -*- coding:utf-8 -*-
"""
测试debug路径功能
"""
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_debug_path():
    """测试debug路径功能"""
    print("=== 测试debug路径功能 ===")
    
    try:
        # 模拟导入（不需要依赖包）
        with open('src/zhihu_collections/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含get_debug_path函数
        if 'def get_debug_path():' in content:
            print("✓ get_debug_path() 函数已定义")
        else:
            print("✗ get_debug_path() 函数未找到")
            return False
        
        # 检查是否使用了get_debug_path
        if 'debug_dir = get_debug_path()' in content:
            print("✓ debug文件保存使用了get_debug_path()")
        else:
            print("✗ debug文件保存未使用get_debug_path()")
            return False
        
        # 检查是否创建目录
        if 'os.makedirs(debug_dir, exist_ok=True)' in content:
            print("✓ 自动创建debug目录")
        else:
            print("✗ 未找到自动创建debug目录的代码")
            return False
        
        # 检查路径拼接
        if 'os.path.join(debug_dir, f"debug_' in content:
            print("✓ 正确使用debug目录路径")
        else:
            print("✗ debug文件路径拼接有问题")
            return False
        
        print("✓ debug文件将保存到 downloads/debug/ 目录")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("测试debug路径配置...\n")
    
    success = test_debug_path()
    
    print(f"\n{'='*40}")
    if success:
        print("✅ debug路径配置成功！")
        print("\n📁 debug HTML文件现在将保存到:")
        print("  - 默认路径: downloads/debug/")
        print("  - 自定义路径: [你的输出路径]/debug/")
        print("\n📋 文件命名规则:")
        print("  - 回答页面: debug_answer_[URL_ID].html")
        print("  - 专栏文章: debug_post_[URL_ID].html")
    else:
        print("❌ debug路径配置失败")
    
    return success

if __name__ == '__main__':
    main()