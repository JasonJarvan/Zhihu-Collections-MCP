# -*- coding:utf-8 -*-
"""
获取知乎收藏夹信息的模块
提供从知乎页面自动获取收藏夹列表的功能
"""
import os
import json
import requests
from bs4 import BeautifulSoup
import time
import random
import logging


def load_cookies():
    """
    加载cookies文件
    :return: cookies字典
    """
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies_list = json.load(f)
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        return cookies_dict
    except FileNotFoundError:
        print("未找到cookies.json文件，将使用无登录模式访问（部分内容可能无法获取）")
        return {}


def get_collections_from_page(page_num=1, cookies=None):
    """
    从知乎的收藏夹页面获取收藏夹信息
    :param page_num: 页码
    :param cookies: cookies字典
    :return: 收藏夹列表和是否有更多项目
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
        logging.error(f"获取第{page_num}页收藏夹失败: {str(e)}")
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
        logging.info(f"正在获取第{page}页收藏夹...")
        print(f"正在获取第{page}页收藏夹...")
        
        collections, has_items = get_collections_from_page(page, cookies)
        
        if not has_items:
            logging.info(f"第{page}页没有更多收藏夹，结束获取")
            print(f"第{page}页没有更多收藏夹，结束获取")
            break
            
        all_collections.extend(collections)
        logging.info(f"第{page}页获取到{len(collections)}个收藏夹")
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
    :return: 是否保存成功
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collections, f, ensure_ascii=False, indent=2)
        logging.info(f"收藏夹列表已保存到: {filename}")
        print(f"收藏夹列表已保存到: {filename}")
        return True
    except Exception as e:
        logging.error(f"保存文件失败: {str(e)}")
        print(f"保存文件失败: {str(e)}")
        return False


def process_open_collection_mode(cookies=None):
    """
    处理openCollection模式，从知乎页面获取收藏夹列表并生成zhihuUrls.json
    :param cookies: cookies字典，如果为None会自动加载
    :return: 是否成功
    """
    # 如果没有提供cookies，自动加载
    if cookies is None:
        cookies = load_cookies()
    
    print("开始从知乎页面获取收藏夹列表...")
    logging.info("开始从知乎页面获取收藏夹列表...")
    
    # 获取所有收藏夹
    all_collections = get_all_collections(cookies)
    
    if not all_collections:
        print("未获取到任何收藏夹")
        logging.warning("未获取到任何收藏夹")
        return False
    
    print(f"总共获取到{len(all_collections)}个收藏夹")
    logging.info(f"总共获取到{len(all_collections)}个收藏夹")
    
    # 保存到zhihuUrls.json
    success = save_collections_to_json(all_collections, 'zhihuUrls.json')
    
    if success:
        print("收藏夹列表已成功生成到zhihuUrls.json文件")
        print("您现在可以将config.json中的openCollection设为false，然后重新运行程序开始下载")
    
    return success


if __name__ == '__main__':
    # 模块测试代码
    print("测试get_collections模块...")
    
    # 测试加载cookies
    cookies = load_cookies()
    print(f"加载cookies: {'成功' if cookies else '失败'}")
    
    # 测试获取单页
    print("\n测试获取单页收藏夹...")
    collections, has_items = get_collections_from_page(1, cookies)
    print(f"获取到{len(collections)}个收藏夹，是否有更多项目: {has_items}")
    
    if collections:
        print("收藏夹示例:")
        for i, collection in enumerate(collections[:3]):
            print(f"  {i+1}. {collection['name']}: {collection['url']}")