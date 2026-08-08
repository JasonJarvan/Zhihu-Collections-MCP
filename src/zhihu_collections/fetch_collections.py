# -*- coding:utf-8 -*-
"""
知乎收藏夹获取工具
从知乎页面抓取用户所有收藏夹并更新 config.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from zhihu_collections._common import (
    load_cookies,
    load_config,
    resolve_base_output_path,
)
from zhihu_collections._headers import build_page_headers
from zhihu_collections._logging import setup_debug_logging, reconfigure_logging


def setup_collection_fetch_logging(logs_base: str | None = None) -> str:
    """配置获取收藏夹过程的日志

    :param logs_base: 日志根目录(绝对路径)。为 None 时回退到 ./downloads/
    :return: 日志文件路径
    """
    if logs_base:
        logs_dir = os.path.join(logs_base, "logs")
    else:
        logs_dir = os.path.join(os.getcwd(), "downloads", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"openCollection_{timestamp}.log"
    log_path = os.path.join(logs_dir, log_filename)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    return log_path


def get_collections_from_page(
    page_num: int = 1, cookies: dict[str, str] | None = None
) -> tuple[list[dict], bool]:
    """从知乎收藏夹页面解析收藏夹信息

    :param page_num: 页码
    :param cookies: 认证 cookies 字典
    :return: (收藏夹列表, 是否有更多项目)
    """
    url = f"https://www.zhihu.com/collections/mine?page={page_num}"
    headers = build_page_headers()

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        collection_items = soup.find_all(class_="SelfCollectionItem")
        collections: list[dict] = []

        for item in collection_items:
            title_element = item.find(class_="SelfCollectionItem-title")
            if not title_element:
                continue

            name = title_element.get_text(strip=True)
            link_element = title_element.find("a")
            if not link_element or not link_element.get("href"):
                continue

            href: str = link_element.get("href")
            if href.startswith("/"):
                href = "https://www.zhihu.com" + href

            collections.append({"name": name, "url": href})

        return collections, len(collection_items) > 0

    except Exception as e:
        logging.error(f"获取第{page_num}页收藏夹失败: {str(e)}")
        return [], False


def get_all_collections(cookies: dict[str, str] | None = None) -> list[dict]:
    """分页获取所有收藏夹

    :param cookies: 认证 cookies 字典
    :return: 所有收藏夹列表
    """
    all_collections: list[dict] = []
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
        time.sleep(random.randint(1, 3))

    return all_collections


def update_config_with_collections(collections: list[dict]) -> bool:
    """将收藏夹列表写回 config.json

    :return: 是否写入成功
    """
    try:
        config = load_config()
        config["zhihuUrls"] = collections
        config["openCollection"] = False

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logging.info(f"配置文件已更新，包含{len(collections)}个收藏夹")
        print(f"配置文件已更新，包含{len(collections)}个收藏夹")
        return True

    except Exception as e:
        logging.error(f"更新配置文件失败: {str(e)}")
        print(f"更新配置文件失败: {str(e)}")
        return False


def save_collections_log(collections: list[dict], log_path: str) -> None:
    """保存收藏夹获取的 JSON 日志"""
    try:
        logs_dir = os.path.dirname(log_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_log_path = os.path.join(logs_dir, f"openCollection_{timestamp}.json")

        log_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_collections": len(collections),
            "collections": collections,
            "log_file": log_path,
        }

        with open(json_log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        logging.info(f"详细日志已保存到: {json_log_path}")
        print(f"详细日志已保存到: {json_log_path}")

    except Exception as e:
        logging.error(f"保存详细日志失败: {str(e)}")


def main() -> bool:
    """自动获取收藏夹并更新 config.json 的主流程

    :return: 是否成功
    """
    print("=" * 60)
    print("知乎收藏夹获取工具")
    print("=" * 60)

    config = load_config()

    # 解析日志输出目录
    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-o", "--output", dest="output_path", default=None)
    known_args, _ = parser.parse_known_args()

    base_output_path, source = resolve_base_output_path(known_args.output_path, config)

    if base_output_path:
        logs_base = str(base_output_path)
        print(f"使用{source}日志根目录: {logs_base}")
        reconfigure_logging(logs_base)
    else:
        logs_base = None
        if source != "默认":
            print(f"{source}指定的输出路径解析失败，使用默认目录")
        else:
            print("使用默认日志根目录: downloads/")

    setup_debug_logging()
    log_path = setup_collection_fetch_logging(logs_base=logs_base)
    logging.info("开始执行收藏夹获取任务")
    print(f"日志文件: {log_path}")

    cookies = load_cookies()
    if not cookies:
        print("警告: 未找到有效的cookies，可能无法获取私密收藏夹")
        logging.warning("未找到有效的cookies")

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

        for i, collection in enumerate(all_collections, 1):
            print(f"  {i}. {collection['name']}")
            logging.info(f"收藏夹 {i}: {collection['name']} - {collection['url']}")

        print("\n正在更新config.json...")
        success = update_config_with_collections(all_collections)

        if success:
            print("✓ 配置文件更新成功")
            print("✓ openCollection已自动设为false")
            logging.info("配置文件更新成功")
            save_collections_log(all_collections, log_path)

            print("\n下一步:")
            print("1. 运行 zhihu export-all 开始下载收藏夹内容")
            print("2. 如需重新获取收藏夹列表，运行 zhihu fetch 即可")

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


if __name__ == "__main__":
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
