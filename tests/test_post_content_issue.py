# -*- coding:utf-8 -*-
"""
测试专栏文章内容获取问题
重现用户报告的专栏文章链接可访问但返回404错误的问题
"""
import sys
import os
import requests
from bs4 import BeautifulSoup

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_url_accessibility():
    """测试URL的可访问性"""
    test_url = "https://zhuanlan.zhihu.com/p/684702206"
    
    print("=== 测试URL可访问性 ===")
    print(f"测试URL: {test_url}")
    
    # 模拟浏览器headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"
    }
    
    try:
        response = requests.get(test_url, headers=headers)
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应头Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"响应长度: {len(response.text)}")
        
        # 检查是否被重定向到登录页面
        if '登录' in response.text or 'login' in response.url.lower():
            print("⚠️  可能被重定向到登录页面")
        
        return response
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def test_content_parsing(response):
    """测试内容解析"""
    if not response:
        return None
        
    print("\n=== 测试内容解析 ===")
    
    soup = BeautifulSoup(response.text, "lxml")
    
    # 尝试当前代码使用的选择器
    current_selectors = [
        ('div', {'class': "Post-RichText"}),
        ('div', {'class': "RichContent"}),
        ('div', {'class': "RichContent-inner"}),
        ('div', {'class': "Post-content"}),
    ]
    
    found_content = False
    for tag, attrs in current_selectors:
        elements = soup.find_all(tag, attrs)
        if elements:
            print(f"✓ 找到 {len(elements)} 个 {tag} {attrs} 元素")
            found_content = True
            for i, elem in enumerate(elements[:2]):  # 只显示前2个
                print(f"  元素{i+1}: {str(elem)[:100]}...")
        else:
            print(f"✗ 未找到 {tag} {attrs} 元素")
    
    if not found_content:
        print("\n使用fallback选择器:")
        fallback_selectors = [
            "div.RichText",
            "div.Post-content", 
            "div.ContentItem-content",
            ".Post .RichContent",
        ]
        
        for selector in fallback_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"✓ 使用 {selector} 找到 {len(elements)} 个元素")
                found_content = True
                break
            else:
                print(f"✗ 使用 {selector} 未找到元素")
    
    return found_content

def analyze_page_structure(response):
    """分析页面结构，寻找可能的内容容器"""
    if not response:
        return
        
    print("\n=== 页面结构分析 ===")
    
    soup = BeautifulSoup(response.text, "lxml")
    
    # 查找包含文章内容的可能容器
    potential_containers = [
        'article',
        'main', 
        '.Post',
        '.Article',
        '.Content',
        '.ZhuanlanPost',
        '[data-reactroot]'
    ]
    
    print("可能的内容容器:")
    for container in potential_containers:
        if container.startswith('.') or container.startswith('['):
            elements = soup.select(container)
        else:
            elements = soup.find_all(container)
            
        if elements:
            print(f"✓ 找到 {len(elements)} 个 {container} 元素")
            # 显示第一个元素的class和部分内容
            if elements:
                elem = elements[0]
                classes = elem.get('class', [])
                print(f"  第一个元素classes: {classes}")
                print(f"  内容预览: {elem.get_text()[:100]}...")
        else:
            print(f"✗ 未找到 {container}")
    
    # 查找所有div标签，按class分类
    print(f"\n所有div标签的class统计:")
    all_divs = soup.find_all('div')
    class_counts = {}
    for div in all_divs:
        classes = div.get('class', [])
        if classes:
            class_str = ' '.join(classes)
            class_counts[class_str] = class_counts.get(class_str, 0) + 1
    
    # 显示最常见的class
    sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    print("最常见的div class (前10个):")
    for class_name, count in sorted_classes[:10]:
        print(f"  {class_name}: {count}个")

def test_with_cookies():
    """使用cookies测试"""
    print("\n=== 使用cookies测试 ===")
    
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            import json
            cookies_list = json.load(f)
        
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        
        print(f"加载了 {len(cookies_dict)} 个cookies")
        
        test_url = "https://zhuanlan.zhihu.com/p/684702206"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Connection": "keep-alive",
            "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8"
        }
        
        response = requests.get(test_url, headers=headers, cookies=cookies_dict)
        print(f"使用cookies后HTTP状态码: {response.status_code}")
        
        return response
        
    except FileNotFoundError:
        print("cookies.json文件不存在，跳过cookies测试")
        return None
    except Exception as e:
        print(f"cookies测试失败: {e}")
        return None

def simulate_main_function():
    """模拟main.py中的get_single_post_content函数"""
    print("\n=== 模拟main.py函数执行 ===")
    
    test_url = "https://zhuanlan.zhihu.com/p/684702206"
    
    # 尝试加载cookies
    cookies = {}
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            import json
            cookies_list = json.load(f)
            for cookie in cookies_list:
                cookies[cookie['name']] = cookie['value']
    except:
        pass
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"
    }
    
    try:
        # 发送请求
        html_content = requests.get(test_url, headers=headers, cookies=cookies)
        html_content.raise_for_status()
        print(f"HTTP请求成功，状态码: {html_content.status_code}")
        
        soup = BeautifulSoup(html_content.text, "lxml")
        
        # 尝试多种可能的选择器
        post_content = None
        selectors = [
            ('div', {'class': "Post-RichText"}),
            ('div', {'class': "RichContent"}),
            ('div', {'class': "RichContent-inner"}),
            ('div', {'class': "Post-content"}),
        ]
        
        for tag, attrs in selectors:
            post_content = soup.find(tag, attrs)
            if post_content:
                print(f"✓ 找到专栏内容: {tag} {attrs}")
                break
            else:
                print(f"✗ 未找到: {tag} {attrs}")
        
        # 如果还没找到，尝试CSS选择器
        if not post_content:
            print("尝试备用选择器...")
            fallback_selectors = [
                "div.RichText",
                "div.Post-content", 
                "div.ContentItem-content",
                ".Post .RichContent",
            ]
            
            for selector in fallback_selectors:
                post_content = soup.select_one(selector)
                if post_content:
                    print(f"✓ 使用备用选择器找到内容: {selector}")
                    break
                else:
                    print(f"✗ 备用选择器失败: {selector}")
        
        if post_content:
            print(f"✅ 成功找到内容，长度: {len(str(post_content))}")
            print(f"内容预览: {post_content.get_text()[:200]}...")
            return True
        else:
            print("❌ 未找到专栏内容容器")
            # 保存HTML进行调试
            with open('debug_684702206.html', 'w', encoding='utf-8') as f:
                f.write(html_content.text)
            print("页面HTML已保存到 debug_684702206.html")
            return False
            
    except Exception as e:
        print(f"❌ 模拟函数执行失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试专栏文章内容获取问题")
    print("=" * 60)
    
    # 1. 测试URL可访问性
    response = test_url_accessibility()
    
    # 2. 测试内容解析
    content_found = test_content_parsing(response)
    
    # 3. 分析页面结构
    analyze_page_structure(response)
    
    # 4. 使用cookies测试
    cookie_response = test_with_cookies()
    if cookie_response:
        print("\n=== 使用cookies后的内容解析 ===")
        cookie_content_found = test_content_parsing(cookie_response)
    
    # 5. 模拟主函数执行
    main_result = simulate_main_function()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)
    
    if response and response.status_code == 200:
        print("✓ URL可正常访问")
    else:
        print("✗ URL访问有问题")
    
    if content_found:
        print("✓ 找到了文章内容")
    else:
        print("✗ 未找到文章内容 - 这就是问题所在！")
    
    if main_result:
        print("✓ main.py函数执行成功")
    else:
        print("✗ main.py函数执行失败")
    
    if not content_found:
        print(f"\n💡 建议:")
        print("1. 检查生成的debug_684702206.html文件")
        print("2. 分析页面实际的HTML结构")
        print("3. 更新CSS选择器以匹配新的页面结构")

if __name__ == '__main__':
    main()