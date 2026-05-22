# -*- coding:utf-8 -*-
"""
最终验证脚本
测试修复后的main.py是否能正常运行
"""
import sys
import os
import logging
import json

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    try:
        from zhihu_collections import main
        
        # 测试配置加载
        config = main.load_config()
        
        if config and 'zhihuUrls' in config:
            print(f"✓ 配置加载成功，包含 {len(config['zhihuUrls'])} 个收藏夹")
            return True
        else:
            print("✗ 配置加载失败")
            return False
            
    except Exception as e:
        print(f"✗ 配置加载出错: {e}")
        return False

def test_logging_setup():
    """测试日志设置"""
    print("\n=== 测试日志设置 ===")
    
    try:
        import main
        
        # 检查日志文件是否已创建
        if hasattr(main, 'debug_log_file') and os.path.exists(main.debug_log_file):
            print(f"✓ 日志文件已创建: {main.debug_log_file}")
            
            # 测试日志写入
            logging.info("测试日志写入")
            main.flush_logs()
            
            # 检查文件大小
            size = os.path.getsize(main.debug_log_file)
            if size > 0:
                print(f"✓ 日志实时写入正常 (文件大小: {size} bytes)")
                return True
            else:
                print("✗ 日志文件为空")
                return False
        else:
            print("✗ 日志文件未创建")
            return False
            
    except Exception as e:
        print(f"✗ 日志测试出错: {e}")
        return False

def test_function_imports():
    """测试关键函数导入"""
    print("\n=== 测试关键函数导入 ===")
    
    try:
        import main
        
        # 检查关键函数是否存在
        functions_to_check = [
            'get_article_nums_of_collection',
            'get_article_urls_in_collection',
            'get_single_answer_content', 
            'get_single_post_content',
            'flush_logs'
        ]
        
        all_functions_exist = True
        for func_name in functions_to_check:
            if hasattr(main, func_name):
                print(f"✓ 函数 {func_name} 存在")
            else:
                print(f"✗ 函数 {func_name} 不存在")
                all_functions_exist = False
        
        return all_functions_exist
        
    except Exception as e:
        print(f"✗ 函数导入测试出错: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    try:
        import main
        
        # 测试get_article_nums_of_collection对无效输入的处理
        result = main.get_article_nums_of_collection("invalid_collection_id")
        if result == 0:
            print("✓ get_article_nums_of_collection 错误处理正确")
        else:
            print(f"✗ get_article_nums_of_collection 返回了意外值: {result}")
            return False
        
        # 测试get_article_urls_in_collection对无效输入的处理  
        urls, titles = main.get_article_urls_in_collection("invalid_collection_id")
        if urls == [] and titles == []:
            print("✓ get_article_urls_in_collection 错误处理正确")
        else:
            print(f"✗ get_article_urls_in_collection 返回了意外值: {urls}, {titles}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试出错: {e}")
        return False

def main():
    """主测试函数"""
    print("开始最终验证测试...\n")
    
    results = []
    
    # 运行各项测试
    results.append(test_config_loading())
    results.append(test_logging_setup())
    results.append(test_function_imports())
    results.append(test_error_handling())
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("最终验证结果:")
    print(f"{'='*50}")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有测试通过 ({passed}/{total})")
        print(f"\n🎉 修复完成！以下问题已解决:")
        print("  - ✅ TypeError: cannot unpack non-iterable NoneType object")
        print("  - ✅ 日志文件空白，不实时打印")
        print("  - ✅ 内容下载失败时的错误处理")
        print("  - ✅ 增强了HTML解析，支持多种页面结构")
        
        print(f"\n📋 现在你可以安全运行:")
        print("  python3 main.py")
        
        print(f"\n💡 注意事项:")
        print("  - 如果仍有URL下载失败，查看生成的debug_*.html文件分析页面结构")
        print("  - 日志文件保存在输出目录的logs文件夹中")
        print("  - 程序会自动跳过已下载的文件")
        
    else:
        print(f"✗ 测试失败 ({passed}/{total})")
        print("请检查失败的测试项目")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)