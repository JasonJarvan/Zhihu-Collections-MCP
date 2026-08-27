# -*- coding:utf-8 -*-
"""
测试openCollection功能的测试用例
"""
import os
import json
import requests
from bs4 import BeautifulSoup
import time
import random

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
        print("未找到cookies.json文件，无法访问私人收藏夹")
        return {}

def get_collections_from_page(page_num=1, cookies=None):
    """
    从知乎的收藏夹页面获取收藏夹信息
    :param page_num: 页码
    :param cookies: cookies字典
    :return: 收藏夹列表
    """
    url = f"https://www.zhihu.com/collections/mine?page={page_num}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有的SelfCollectionItem
        collection_items = soup.find_all(class_='SelfCollectionItem')
        collections = []
        
        for item in collection_items:
            # 查找标题元素
            title_element = item.find(class_='SelfCollectionItem-title')
            if title_element:
                # 获取收藏夹名称
                name = title_element.get_text(strip=True)
                
                # 获取href链接
                link_element = title_element.find('a')
                if link_element and link_element.get('href'):
                    href = link_element.get('href')
                    # 将相对链接转换为绝对链接
                    if href.startswith('/'):
                        href = 'https://www.zhihu.com' + href
                    
                    collections.append({
                        'name': name,
                        'url': href
                    })
        
        return collections, len(collection_items) > 0
        
    except Exception as e:
        print(f"获取第{page_num}页收藏夹失败: {str(e)}")
        return [], False

def get_all_collections(cookies=None):
    """
    获取所有收藏夹
    :param cookies: cookies字典
    :return: 所有收藏夹列表
    """
    all_collections = []
    page = 1
    
    while True:
        print(f"正在获取第{page}页收藏夹...")
        collections, has_items = get_collections_from_page(page, cookies)
        
        if not has_items:
            print(f"第{page}页没有更多收藏夹，结束获取")
            break
            
        all_collections.extend(collections)
        print(f"第{page}页获取到{len(collections)}个收藏夹")
        
        page += 1
        # 添加延时避免请求过快
        time.sleep(random.randint(1, 3))
    
    return all_collections

def save_collections_to_json(collections, filename='zhihuUrls.json'):
    """
    将收藏夹列表保存到JSON文件
    :param collections: 收藏夹列表
    :param filename: 输出文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collections, f, ensure_ascii=False, indent=2)
        print(f"收藏夹列表已保存到: {filename}")
        return True
    except Exception as e:
        print(f"保存文件失败: {str(e)}")
        return False

def test_single_page():
    """测试单页获取"""
    print("=== 测试单页获取 ===")
    cookies = load_cookies()
    
    collections, has_items = get_collections_from_page(1, cookies)
    
    print(f"是否有收藏夹项目: {has_items}")
    print(f"获取到收藏夹数量: {len(collections)}")
    
    for i, collection in enumerate(collections[:3]):  # 只显示前3个
        print(f"收藏夹 {i+1}: {collection['name']}")
        print(f"  链接: {collection['url']}")
    
    return collections

def test_all_pages():
    """测试获取所有页面"""
    print("\n=== 测试获取所有页面 ===")
    cookies = load_cookies()
    
    all_collections = get_all_collections(cookies)
    
    print(f"总共获取到收藏夹数量: {len(all_collections)}")
    
    # 保存到文件
    if all_collections:
        save_collections_to_json(all_collections)
    
    return all_collections

def test_json_output():
    """测试JSON输出格式"""
    print("\n=== 测试JSON输出格式 ===")
    
    # 模拟一些测试数据
    test_collections = [
        {"name": "测试收藏夹1", "url": "https://www.zhihu.com/collection/123456"},
        {"name": "测试收藏夹2", "url": "https://www.zhihu.com/collection/789012"}
    ]
    
    save_collections_to_json(test_collections, 'test_zhihuUrls.json')
    
    # 验证文件内容
    try:
        with open('test_zhihuUrls.json', 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print("JSON文件验证成功:")
        print(json.dumps(loaded_data, ensure_ascii=False, indent=2))
        
        # 清理测试文件
        os.remove('test_zhihuUrls.json')
    except Exception as e:
        print(f"JSON文件验证失败: {str(e)}")

if __name__ == '__main__':
    print("开始测试openCollection功能...")
    
    # 测试1: 单页获取
    collections = test_single_page()
    
    # 测试2: JSON输出格式
    test_json_output()
    
    # 测试3: 获取所有页面（如果单页测试成功）
    if collections:
        test_all_pages()
    else:
        print("由于单页测试失败，跳过所有页面测试")
    
    print("\n测试完成!")