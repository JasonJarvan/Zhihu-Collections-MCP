# -*- coding:utf-8 -*-
"""
独立的收藏夹获取脚本
从知乎页面获取用户的所有收藏夹，并更新到config.json文件中
"""
import os
import json
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime
import pathlib
import platform


def get_current_os():
    """获取当前操作系统类型"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def parse_output_path(path_str, os_type):
    """解析路径，根据操作系统类型处理"""
    if not path_str:
        return None
    
    # 如果没有指定os，则自动检测
    if not os_type:
        os_type = get_current_os()
    
    try:
        if os_type.lower() == "windows":
            # Windows路径处理
            # 支持 D:\path\to\folder 或 D:/path/to/folder 格式
            path_str = path_str.replace('/', '\\')
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["linux", "freebsd", "openbsd", "netbsd", "solaris", "aix"]:
            # Unix-like系统路径处理
            # 支持 /usr/local/lib 格式
            if path_str.startswith('~'):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["macos", "darwin"]:
            # macOS路径处理
            # 支持 /Users/username/Documents 或 ~/Documents 格式
            if path_str.startswith('~'):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["cygwin", "msys"]:
            # Cygwin/MSYS环境路径处理
            # 支持 /cygdrive/c/path 或 /c/path 格式
            if path_str.startswith('/cygdrive/'):
                # Cygwin格式: /cygdrive/c/path -> C:\path
                drive_path = path_str[10:]  # 移除 /cygdrive/
                if len(drive_path) >= 2 and drive_path[1] == '/':
                    path_str = drive_path[0].upper() + ':' + drive_path[1:].replace('/', '\\')
            elif path_str.startswith('/') and len(path_str) >= 3 and path_str[2] == '/':
                # MSYS格式: /c/path -> C:\path
                path_str = path_str[1].upper() + ':' + path_str[2:].replace('/', '\\')
            return pathlib.Path(path_str).resolve()
        else:
            # 其他系统，尝试通用处理
            logging.warning(f"未知操作系统类型: {os_type}，尝试通用路径处理")
            if path_str.startswith('~'):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
    except Exception as e:
        logging.error(f"路径解析失败: {path_str}, 错误: {str(e)}")
        return None


def setup_logging():
    """设置日志"""
    # 获取日志目录
    logs_dir = os.path.join(os.getcwd(), 'downloads', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"openCollection_{timestamp}.log"
    log_path = os.path.join(logs_dir, log_filename)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True
    )
    
    return log_path


def load_cookies():
    """加载cookies文件"""
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies_list = json.load(f)
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        return cookies_dict
    except FileNotFoundError:
        print("未找到cookies.json文件，将使用无登录模式访问（部分内容可能无法获取）")
        logging.warning("未找到cookies.json文件")
        return {}


def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        logging.error("未找到config.json文件")
        print("未找到config.json文件，请确保文件存在")
        return None


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


def update_config_with_collections(collections):
    """
    将获取到的收藏夹更新到config.json中
    :param collections: 收藏夹列表
    :return: 是否成功
    """
    try:
        # 读取当前配置
        config = load_config()
        if config is None:
            return False
        
        # 更新zhihuUrls
        config['zhihuUrls'] = collections
        
        # 将openCollection设为false，因为已经获取完成
        config['openCollection'] = False
        
        # 写回配置文件
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logging.info(f"配置文件已更新，包含{len(collections)}个收藏夹")
        print(f"配置文件已更新，包含{len(collections)}个收藏夹")
        return True
        
    except Exception as e:
        logging.error(f"更新配置文件失败: {str(e)}")
        print(f"更新配置文件失败: {str(e)}")
        return False


def save_collections_log(collections, log_path):
    """
    保存收藏夹获取日志
    :param collections: 收藏夹列表
    :param log_path: 日志文件路径
    """
    try:
        # 生成详细日志
        log_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_collections": len(collections),
            "collections": collections,
            "log_file": log_path
        }
        
        # 保存到logs目录
        logs_dir = os.path.dirname(log_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_log_path = os.path.join(logs_dir, f"openCollection_{timestamp}.json")
        
        with open(json_log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"详细日志已保存到: {json_log_path}")
        print(f"详细日志已保存到: {json_log_path}")
        
    except Exception as e:
        logging.error(f"保存详细日志失败: {str(e)}")


def main():
    """主函数"""
    print("=" * 60)
    print("知乎收藏夹获取工具")
    print("=" * 60)
    
    # 设置日志
    log_path = setup_logging()
    logging.info("开始执行收藏夹获取任务")
    print(f"日志文件: {log_path}")
    
    # 加载cookies
    cookies = load_cookies()
    if not cookies:
        print("警告: 未找到有效的cookies，可能无法获取私密收藏夹")
        logging.warning("未找到有效的cookies")
    
    # 获取所有收藏夹
    print("\n开始获取收藏夹列表...")
    logging.info("开始获取收藏夹列表")
    
    try:
        all_collections = get_all_collections(cookies)
        
        if not all_collections:
            print("未获取到任何收藏夹")
            logging.warning("未获取到任何收藏夹")
            return False
        
        print(f"\n总共获取到 {len(all_collections)} 个收藏夹:")
        logging.info(f"总共获取到 {len(all_collections)} 个收藏夹")
        
        # 显示获取到的收藏夹
        for i, collection in enumerate(all_collections, 1):
            print(f"  {i}. {collection['name']}")
            logging.info(f"收藏夹 {i}: {collection['name']} - {collection['url']}")
        
        # 更新配置文件
        print(f"\n正在更新config.json...")
        success = update_config_with_collections(all_collections)
        
        if success:
            print("✓ 配置文件更新成功")
            print("✓ openCollection已自动设为false")
            logging.info("配置文件更新成功")
            
            # 保存详细日志
            save_collections_log(all_collections, log_path)
            
            print(f"\n下一步:")
            print("1. 运行 python main.py 开始下载收藏夹内容")
            print("2. 如需重新获取收藏夹列表，将config.json中的openCollection设为true后重新运行此脚本")
            
            return True
        else:
            print("✗ 配置文件更新失败")
            logging.error("配置文件更新失败")
            return False
            
    except Exception as e:
        error_msg = f"获取收藏夹过程中发生错误: {str(e)}"
        print(f"✗ {error_msg}")
        logging.error(error_msg)
        return False


if __name__ == '__main__':
    success = main()
    if success:
        print(f"\n{'=' * 60}")
        print("收藏夹获取完成！")
        print(f"{'=' * 60}")
    else:
        print(f"\n{'=' * 60}")
        print("收藏夹获取失败！")
        print(f"{'=' * 60}")
        exit(1)