# -*- coding:utf-8 -*-
"""
调试知乎收藏夹页面结构
"""
import requests
from bs4 import BeautifulSoup
import json

def load_cookies():
    """加载cookies"""
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies_list = json.load(f)
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        return cookies_dict
    except FileNotFoundError:
        return {}

def debug_page_structure():
    """调试页面结构"""
    cookies = load_cookies()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"
    }
    
    url = "https://www.zhihu.com/collections/mine?page=1"
    
    try:
        print("正在获取页面...")
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")
        
        # 保存原始HTML以供分析
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("原始HTML已保存到 debug_page.html")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 检查各种可能的收藏夹元素
        print("\n=== 检查页面元素 ===")
        
        # 原始查找方式
        self_collection_items = soup.find_all(class_='SelfCollectionItem')
        print(f"SelfCollectionItem 元素数量: {len(self_collection_items)}")
        
        # 尝试其他可能的class名称
        possible_classes = [
            'CollectionItem',
            'Collection-item', 
            'collection-item',
            'self-collection-item',
            'UserCollection',
            'MyCollection'
        ]
        
        for class_name in possible_classes:
            elements = soup.find_all(class_=class_name)
            if elements:
                print(f"找到 {class_name} 元素: {len(elements)}个")
        
        # 查找包含"收藏夹"或"collection"的元素
        print("\n=== 查找包含关键词的元素 ===")
        collection_texts = soup.find_all(text=lambda text: text and ('收藏夹' in text or 'collection' in text.lower()))
        print(f"包含'收藏夹'或'collection'的文本元素: {len(collection_texts)}")
        
        if collection_texts:
            for i, text in enumerate(collection_texts[:5]):  # 只显示前5个
                parent = text.parent
                print(f"  {i+1}. 文本: '{text.strip()}'")
                print(f"     父元素: {parent.name}")
                if parent.get('class'):
                    print(f"     父元素类: {parent.get('class')}")
        
        # 查找所有链接
        print("\n=== 查找收藏夹链接 ===")
        all_links = soup.find_all('a', href=True)
        collection_links = [link for link in all_links if '/collection/' in link.get('href', '')]
        print(f"包含'/collection/'的链接: {len(collection_links)}")
        
        if collection_links:
            for i, link in enumerate(collection_links[:3]):  # 只显示前3个
                print(f"  {i+1}. 链接: {link.get('href')}")
                print(f"     文本: '{link.get_text(strip=True)}'")
                if link.get('class'):
                    print(f"     类: {link.get('class')}")
        
        # 检查是否是登录页面
        if '登录' in response.text or 'login' in response.text.lower():
            print("\n⚠️  可能未正确登录，页面包含登录相关内容")
        
        # 检查是否有错误信息
        error_indicators = ['404', '403', '500', '错误', 'error']
        for indicator in error_indicators:
            if indicator in response.text.lower():
                print(f"\n⚠️  页面可能包含错误信息: {indicator}")
        
        return True
        
    except Exception as e:
        print(f"调试失败: {str(e)}")
        return False

if __name__ == '__main__':
    debug_page_structure()