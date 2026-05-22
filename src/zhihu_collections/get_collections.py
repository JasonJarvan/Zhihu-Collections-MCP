# -*- coding:utf-8 -*-
"""
获取知乎收藏夹信息的模块 (deprecated)
此模块的功能已被 fetch_collections.py 取代，保留仅供参考。
"""
import os
import json
import logging

from zhihu_collections._common import load_cookies
from zhihu_collections.fetch_collections import get_collections_from_page, get_all_collections


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