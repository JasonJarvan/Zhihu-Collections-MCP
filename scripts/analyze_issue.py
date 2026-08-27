# -*- coding:utf-8 -*-
"""
分析fetch_collections.py的问题
"""
import json

def analyze_cookies():
    """分析cookies情况"""
    print("=== 分析Cookies ===")
    
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies_list = json.load(f)
        
        print(f"✓ cookies.json文件存在，包含{len(cookies_list)}个cookie")
        
        # 检查关键cookies
        cookie_names = [cookie.get('name', '') for cookie in cookies_list]
        important_cookies = ['z_c0', 'd_c0', 'SESSIONID']
        
        for cookie_name in important_cookies:
            if cookie_name in cookie_names:
                print(f"✓ 找到重要cookie: {cookie_name}")
            else:
                print(f"✗ 缺少重要cookie: {cookie_name}")
        
        return True
        
    except FileNotFoundError:
        print("✗ 未找到cookies.json文件")
        return False
    except Exception as e:
        print(f"✗ 读取cookies失败: {e}")
        return False

def analyze_possible_issues():
    """分析可能的问题"""
    print("\n=== 可能的问题原因 ===")
    
    issues = [
        {
            "问题": "知乎页面结构变化",
            "描述": "SelfCollectionItem类名可能已经改变",
            "可能性": "高",
            "解决方案": "需要更新HTML解析逻辑"
        },
        {
            "问题": "登录状态失效",
            "描述": "cookies过期或无效，无法访问个人收藏夹",
            "可能性": "中",
            "解决方案": "更新cookies.json文件"
        },
        {
            "问题": "反爬虫机制",
            "描述": "知乎检测到自动化访问并阻止",
            "可能性": "中",
            "解决方案": "调整请求头或增加延时"
        },
        {
            "问题": "页面加载方式变化",
            "描述": "收藏夹内容可能通过JavaScript动态加载",
            "可能性": "高",
            "解决方案": "可能需要使用API接口而不是解析HTML"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['问题']} (可能性: {issue['可能性']})")
        print(f"   描述: {issue['描述']}")
        print(f"   解决方案: {issue['解决方案']}")

def suggest_solutions():
    """建议解决方案"""
    print(f"\n{'='*50}")
    print("建议的解决方案:")
    print(f"{'='*50}")
    
    solutions = [
        {
            "步骤": 1,
            "操作": "检查登录状态",
            "具体行动": [
                "在浏览器中访问 https://www.zhihu.com/collections/mine",
                "确认可以看到自己的收藏夹列表",
                "如果看不到，请先登录知乎"
            ]
        },
        {
            "步骤": 2,
            "操作": "更新cookies",
            "具体行动": [
                "在浏览器中登录知乎",
                "按F12打开开发者工具",
                "在Network标签中刷新页面",
                "找到对知乎的请求，复制最新的cookies",
                "更新cookies.json文件"
            ]
        },
        {
            "步骤": 3,
            "操作": "检查页面结构",
            "具体行动": [
                "在浏览器中访问收藏夹页面",
                "右键点击收藏夹项目，选择'检查元素'",
                "查看实际的HTML结构和class名称",
                "如果class名称变了，需要更新代码"
            ]
        },
        {
            "步骤": 4,
            "操作": "尝试API接口",
            "具体行动": [
                "知乎可能提供API接口获取收藏夹",
                "可以尝试分析浏览器的网络请求",
                "寻找JSON格式的API响应"
            ]
        }
    ]
    
    for solution in solutions:
        print(f"\n步骤{solution['步骤']}: {solution['操作']}")
        for action in solution['具体行动']:
            print(f"  - {action}")

def analyze_logs():
    """分析日志信息"""
    print(f"\n{'='*50}")
    print("日志分析:")
    print(f"{'='*50}")
    
    log_analysis = {
        "网络请求": "✓ 成功 (HTTP 200)",
        "页面访问": "✓ 成功 (能访问/collections/mine)",
        "HTML解析": "✗ 失败 (未找到SelfCollectionItem)",
        "结果": "页面结构可能发生变化"
    }
    
    for aspect, status in log_analysis.items():
        print(f"{aspect}: {status}")
    
    print(f"\n关键问题:")
    print("虽然网络请求成功，但HTML解析没有找到预期的元素。")
    print("这通常意味着:")
    print("1. 页面的CSS类名发生了变化")
    print("2. 收藏夹内容通过JavaScript动态加载")
    print("3. 页面重定向到了登录页面")

def main():
    """主函数"""
    print("分析fetch_collections.py执行失败的原因...")
    
    analyze_cookies()
    analyze_possible_issues()
    analyze_logs()
    suggest_solutions()
    
    print(f"\n{'='*50}")
    print("总结:")
    print(f"{'='*50}")
    print("最可能的原因是知乎页面结构发生了变化。")
    print("建议按照上述步骤检查页面结构并更新解析逻辑。")

if __name__ == '__main__':
    main()