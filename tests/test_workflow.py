# -*- coding:utf-8 -*-
"""
演示新的工作流程
"""
import json
import os

def demonstrate_workflow():
    """演示新的工作流程"""
    print("=" * 60)
    print("演示 Export-Zhihu-Collections 新工作流程")
    print("=" * 60)
    
    print("\n步骤1: 检查当前配置状态")
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"  当前配置:")
        print(f"  - zhihuUrls数量: {len(config.get('zhihuUrls', []))}")
        print(f"  - openCollection: {config.get('openCollection', False)}")
        
        if config.get('openCollection', False):
            print("\n步骤2: openCollection模式已启用")
            print("  需要执行的操作:")
            print("  1. 运行: python fetch_collections.py")
            print("     - 这将从知乎页面获取收藏夹列表")
            print("     - 自动更新config.json中的zhihuUrls")
            print("     - 自动将openCollection设为false")
            print("     - 生成日志文件到logs/目录")
            print("  2. 然后运行: python main.py")
            print("     - 这将开始下载收藏夹内容")
        else:
            zhihu_collections = config.get('zhihuUrls', [])
            if zhihu_collections:
                print("\n步骤2: 常规下载模式")
                print(f"  找到{len(zhihu_collections)}个收藏夹:")
                for i, collection in enumerate(zhihu_collections[:3], 1):
                    print(f"    {i}. {collection.get('name', '未命名')}")
                if len(zhihu_collections) > 3:
                    print(f"    ... 还有{len(zhihu_collections) - 3}个收藏夹")
                print("\n  可以直接运行: python main.py")
            else:
                print("\n步骤2: 需要获取收藏夹列表")
                print("  当前没有收藏夹配置，建议:")
                print("  1. 运行: python fetch_collections.py")
                print("  2. 然后运行: python main.py")
        
        print("\n步骤3: 日志和输出")
        print("  - fetch_collections.py 会生成:")
        print("    * logs/openCollection_{时间戳}.log")
        print("    * logs/openCollection_{时间戳}.json")
        print("  - main.py 会生成:")
        print("    * downloads/{收藏夹名称}/*.md")
        print("    * downloads/{收藏夹名称}/assets/*.jpg")
        print("    * logs/debug_{时间戳}.log")
        
    except FileNotFoundError:
        print("  ✗ 未找到config.json文件")
        print("  请先创建配置文件")
    except Exception as e:
        print(f"  ✗ 读取配置失败: {e}")

def demonstrate_file_structure():
    """演示文件结构"""
    print(f"\n{'-' * 60}")
    print("当前项目文件结构:")
    print(f"{'-' * 60}")
    
    structure = {
        "主要文件": [
            "main.py - 主下载程序",
            "fetch_collections.py - 独立的收藏夹获取脚本",
            "get_collections.py - 收藏夹获取模块",
            "utils.py - 工具函数",
            "config.json - 配置文件",
            "cookies.json - 认证cookies"
        ],
        "测试文件": [
            "test/test_config_logic.py - 配置逻辑测试",
            "test/test_fetch_simple.py - 独立脚本测试",
            "test/test_workflow.py - 工作流程演示",
            "test/README.md - 测试说明"
        ]
    }
    
    for category, files in structure.items():
        print(f"\n{category}:")
        for file_info in files:
            file_name = file_info.split(' - ')[0]
            description = file_info.split(' - ')[1] if ' - ' in file_info else ""
            
            if os.path.exists(file_name):
                status = "✓"
            else:
                status = "✗"
            
            print(f"  {status} {file_info}")

def demonstrate_commands():
    """演示命令使用"""
    print(f"\n{'-' * 60}")
    print("常用命令演示:")
    print(f"{'-' * 60}")
    
    commands = [
        {
            "场景": "首次使用/获取收藏夹列表",
            "命令": [
                "python fetch_collections.py",
                "python main.py"
            ],
            "说明": "先获取收藏夹列表，再下载内容"
        },
        {
            "场景": "已有收藏夹配置",
            "命令": [
                "python main.py"
            ],
            "说明": "直接下载收藏夹内容"
        },
        {
            "场景": "测试功能",
            "命令": [
                "python test/test_config_logic.py",
                "python test/test_fetch_simple.py",
                "python test/test_workflow.py"
            ],
            "说明": "运行各种测试"
        },
        {
            "场景": "语法检查",
            "命令": [
                "python test/test_syntax.py"
            ],
            "说明": "检查所有Python文件语法"
        }
    ]
    
    for cmd_info in commands:
        print(f"\n{cmd_info['场景']}:")
        print(f"  说明: {cmd_info['说明']}")
        for cmd in cmd_info['命令']:
            print(f"  $ {cmd}")

def main():
    """主函数"""
    demonstrate_workflow()
    demonstrate_file_structure()
    demonstrate_commands()
    
    print(f"\n{'=' * 60}")
    print("工作流程演示完成！")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()