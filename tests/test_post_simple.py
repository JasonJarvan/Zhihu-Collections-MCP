# -*- coding:utf-8 -*-
"""
简化版专栏文章测试 - 分析get_single_post_content函数的问题
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_post_function():
    """分析get_single_post_content函数的逻辑"""
    print("=== 分析get_single_post_content函数 ===")
    
    try:
        with open('src/zhihu_collections/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找get_single_post_content函数
        start_marker = "def get_single_post_content("
        if start_marker in content:
            print("✓ 找到get_single_post_content函数")
            
            # 提取函数内容
            start_pos = content.find(start_marker)
            # 简单的函数结束判断（找下一个def或文件结束）
            next_def = content.find("\ndef ", start_pos + 1)
            if next_def == -1:
                func_content = content[start_pos:]
            else:
                func_content = content[start_pos:next_def]
            
            print(f"函数长度: {len(func_content)} 字符")
            
            # 分析问题点
            issues = []
            
            # 1. 检查错误返回值
            if 'post_content = "该文章链接被404, 无法直接访问"' in func_content:
                issues.append("发现硬编码的404错误消息")
            
            # 2. 检查选择器
            selectors_found = []
            if '"Post-RichText"' in func_content:
                selectors_found.append("Post-RichText")
            if '"RichContent"' in func_content:
                selectors_found.append("RichContent") 
            if '"RichContent-inner"' in func_content:
                selectors_found.append("RichContent-inner")
            if '"Post-content"' in func_content:
                selectors_found.append("Post-content")
                
            print(f"找到的CSS选择器: {selectors_found}")
            
            # 3. 检查fallback选择器
            fallback_found = []
            if '"div.RichText"' in func_content:
                fallback_found.append("div.RichText")
            if '"div.Post-content"' in func_content:
                fallback_found.append("div.Post-content")
            if '"div.ContentItem-content"' in func_content:
                fallback_found.append("div.ContentItem-content")
            if '".Post .RichContent"' in func_content:
                fallback_found.append(".Post .RichContent")
                
            print(f"找到的fallback选择器: {fallback_found}")
            
            # 4. 分析可能的问题
            print("\n可能的问题:")
            if len(selectors_found) < 4:
                issues.append("CSS选择器数量不足，可能无法匹配新的页面结构")
            
            if '"该文章链接被404, 无法直接访问"' in func_content:
                issues.append("当找不到内容时直接返回404消息，没有进一步尝试")
                
            # 5. 检查是否有调试信息保存
            if 'debug_file' in func_content and 'html_content.text' in func_content:
                print("✓ 函数会保存调试HTML文件")
            else:
                issues.append("缺少调试HTML文件保存功能")
            
            if issues:
                print("\n发现的问题:")
                for i, issue in enumerate(issues, 1):
                    print(f"  {i}. {issue}")
            else:
                print("✓ 函数逻辑看起来正常")
                
            return True
            
    except Exception as e:
        print(f"✗ 分析失败: {e}")
        return False

def suggest_improvements():
    """建议改进方案"""
    print(f"\n{'='*50}")
    print("改进建议:")
    print(f"{'='*50}")
    
    suggestions = [
        {
            "问题": "CSS选择器可能过时",
            "解决方案": "添加更多现代化的选择器，特别是知乎新版页面结构",
            "具体实现": [
                "添加 .Post-RichTextContainer",
                "添加 .ztext", 
                "添加 .Post-Main",
                "添加 [data-zop-editor]",
                "添加 .Article-RichText"
            ]
        },
        {
            "问题": "没有尝试不同的解析策略", 
            "解决方案": "当标准选择器失败时，尝试更宽泛的内容搜索",
            "具体实现": [
                "搜索包含大量文本的div",
                "搜索p标签集合",
                "使用文本长度判断主内容区域"
            ]
        },
        {
            "问题": "错误处理不够细致",
            "解决方案": "区分真正的404和解析失败",
            "具体实现": [
                "检查HTTP状态码",
                "检查页面是否包含错误信息",
                "检查是否被重定向到登录页"
            ]
        }
    ]
    
    for suggestion in suggestions:
        print(f"\n问题: {suggestion['问题']}")
        print(f"解决方案: {suggestion['解决方案']}")
        print("具体实现:")
        for impl in suggestion['具体实现']:
            print(f"  - {impl}")

def create_test_case():
    """创建具体的测试用例"""
    print(f"\n{'='*50}")
    print("测试用例设计:")
    print(f"{'='*50}")
    
    test_case = {
        "目标URL": "https://zhuanlan.zhihu.com/p/684702206",
        "预期行为": "成功获取文章内容",
        "当前行为": "返回'该文章链接被404, 无法直接访问'",
        "测试步骤": [
            "1. 使用requests获取页面内容",
            "2. 检查HTTP状态码(应该是200)",
            "3. 使用BeautifulSoup解析HTML", 
            "4. 尝试所有CSS选择器",
            "5. 如果都失败，分析页面实际结构",
            "6. 保存调试HTML文件"
        ],
        "验证点": [
            "HTTP请求成功",
            "页面包含文章内容", 
            "CSS选择器能找到内容",
            "返回的不是错误消息"
        ]
    }
    
    print(f"目标URL: {test_case['目标URL']}")
    print(f"预期行为: {test_case['预期行为']}")
    print(f"当前行为: {test_case['当前行为']}")
    
    print("\n测试步骤:")
    for step in test_case['测试步骤']:
        print(f"  {step}")
    
    print("\n验证点:")
    for point in test_case['验证点']:
        print(f"  ✓ {point}")

def main():
    """主函数"""
    print("开始分析专栏文章内容获取问题...")
    print("=" * 60)
    
    # 1. 分析当前函数
    success = analyze_post_function()
    
    if success:
        # 2. 提供改进建议
        suggest_improvements()
        
        # 3. 创建测试用例
        create_test_case()
        
        print(f"\n{'='*60}")
        print("下一步行动:")
        print(f"{'='*60}")
        print("1. 运行完整测试脚本(需要安装依赖): python3 test/test_post_content_issue.py")
        print("2. 检查生成的debug HTML文件") 
        print("3. 基于实际页面结构更新CSS选择器")
        print("4. 实现改进建议中的解决方案")
    else:
        print("❌ 分析失败，请检查main.py文件")

if __name__ == '__main__':
    main()