# -*- coding:utf-8 -*-
import os
import random
import sys
import time
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
from datetime import datetime
from utils import filter_title_str
import json
import logging
import traceback
import platform
import pathlib

from markdownify import MarkdownConverter


# 读取配置文件
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("未找到config.json文件，尝试读取旧版zhihuUrls.json文件")
        try:
            with open("zhihuUrls.json", "r", encoding="utf-8") as f:
                urls = json.load(f)
                return {"zhihuUrls": urls, "outputPath": "", "os": ""}
        except FileNotFoundError:
            print("未找到配置文件，请创建config.json文件并配置收藏夹信息")
            return {"zhihuUrls": [], "outputPath": "", "os": ""}


# 获取当前操作系统类型
def get_current_os():
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


# 解析路径，根据操作系统类型处理
def parse_output_path(path_str, os_type):
    if not path_str:
        return None

    # 如果没有指定os，则自动检测
    if not os_type:
        os_type = get_current_os()

    try:
        if os_type.lower() == "windows":
            # Windows路径处理
            # 支持 D:\path\to\folder 或 D:/path/to/folder 格式
            path_str = path_str.replace("/", "\\")
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in [
            "linux",
            "freebsd",
            "openbsd",
            "netbsd",
            "solaris",
            "aix",
        ]:
            # Unix-like系统路径处理
            # 支持 /usr/local/lib 格式
            if path_str.startswith("~"):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["macos", "darwin"]:
            # macOS路径处理
            # 支持 /Users/username/Documents 或 ~/Documents 格式
            if path_str.startswith("~"):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["cygwin", "msys"]:
            # Cygwin/MSYS环境路径处理
            # 支持 /cygdrive/c/path 或 /c/path 格式
            if path_str.startswith("/cygdrive/"):
                # Cygwin格式: /cygdrive/c/path -> C:\path
                drive_path = path_str[10:]  # 移除 /cygdrive/
                if len(drive_path) >= 2 and drive_path[1] == "/":
                    path_str = (
                        drive_path[0].upper() + ":" + drive_path[1:].replace("/", "\\")
                    )
            elif path_str.startswith("/") and len(path_str) >= 3 and path_str[2] == "/":
                # MSYS格式: /c/path -> C:\path
                path_str = path_str[1].upper() + ":" + path_str[2:].replace("/", "\\")
            return pathlib.Path(path_str).resolve()
        else:
            # 其他系统，尝试通用处理
            logging.warning(f"未知操作系统类型: {os_type}，尝试通用路径处理")
            if path_str.startswith("~"):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
    except Exception as e:
        logging.error(f"路径解析失败: {path_str}, 错误: {str(e)}")
        return None


# 读取cookies
def load_cookies():
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies_list = json.load(f)
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie["name"]] = cookie["value"]
        return cookies_dict
    except FileNotFoundError:
        print("未找到cookies.json文件，将使用无登录模式访问（部分内容可能无法获取）")
        return {}


# 全局变量存储当前处理的收藏夹名称
current_collection_name = ""

# 全局日志数据存储
processing_log = []

# 全局配置和路径管理
config = {}
base_output_path = None


# 设置调试日志
def setup_debug_logging():
    # 初始化时使用默认路径，稍后会在main中重新配置
    logs_dir = os.path.join(os.path.dirname(__file__), "downloads", "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_log_file = os.path.join(logs_dir, f"debug_{timestamp}.log")

    # 清除所有已存在的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建文件处理器，立即写入
    file_handler = logging.FileHandler(debug_log_file, encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 设置格式
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 配置根日志记录器
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 测试日志写入
    logging.info(f"日志系统初始化完成，日志文件: {debug_log_file}")

    # 强制刷新
    for handler in root_logger.handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    return debug_log_file


# 重新配置日志路径
def reconfigure_logging():
    logs_dir = get_logs_path()
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_log_file = os.path.join(logs_dir, f"debug_{timestamp}.log")

    # 清除已有的handler
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.flush()  # 确保刷新
        root_logger.removeHandler(handler)

    # 创建新的处理器
    file_handler = logging.FileHandler(debug_log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 设置格式
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 重新添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    return debug_log_file


# 获取输出路径的函数
def get_output_path(collection_name):
    """
    根据配置获取输出路径
    如果配置了outputPath，使用自定义路径
    否则使用默认的downloads路径
    """
    global base_output_path

    if base_output_path:
        # 使用自定义输出路径
        return os.path.join(str(base_output_path), collection_name)
    else:
        # 使用默认路径
        return os.path.join(os.path.dirname(__file__), "downloads", collection_name)


def get_logs_path():
    """
    获取日志路径
    """
    global base_output_path

    if base_output_path:
        # 使用自定义输出路径
        return os.path.join(str(base_output_path), "logs")
    else:
        # 使用默认路径
        return os.path.join(os.path.dirname(__file__), "downloads", "logs")


def get_debug_path():
    """
    获取调试文件路径
    """
    global base_output_path

    if base_output_path:
        # 使用自定义输出路径
        return os.path.join(str(base_output_path), "debug")
    else:
        # 使用默认路径
        return os.path.join(os.path.dirname(__file__), "downloads", "debug")


def smart_content_detection(soup, url):
    """
    智能内容检测 - 当标准选择器失败时的备用方案
    """
    logging.debug(f"开始智能内容检测: {url}")

    # 策略1: 查找包含大量文本的div元素
    all_divs = soup.find_all("div")
    text_length_threshold = 200  # 最少文本长度

    candidates = []
    for div in all_divs:
        text_content = div.get_text(strip=True)
        if len(text_content) > text_length_threshold:
            # 计算直接子节点中的文本密度
            direct_text_length = len("".join(div.find_all(text=True, recursive=False)))
            total_length = len(text_content)

            # 过滤掉主要是链接或导航的容器
            link_count = len(div.find_all("a"))
            text_to_link_ratio = total_length / max(link_count, 1)

            candidates.append(
                {
                    "element": div,
                    "text_length": total_length,
                    "text_to_link_ratio": text_to_link_ratio,
                    "classes": div.get("class", []),
                }
            )

    # 按文本长度排序，选择最长的
    candidates.sort(key=lambda x: x["text_length"], reverse=True)

    if candidates:
        best_candidate = candidates[0]
        logging.debug(
            f"智能检测找到候选内容，长度: {best_candidate['text_length']}, classes: {best_candidate['classes']}"
        )

        # 如果最佳候选者文本长度足够长，返回它
        if best_candidate["text_length"] > 500:
            return best_candidate["element"]

    # 策略2: 查找文章相关的容器
    article_containers = soup.find_all(["article", "main"])
    for container in article_containers:
        text_content = container.get_text(strip=True)
        if len(text_content) > text_length_threshold:
            logging.debug(f"找到文章容器: {container.name}")
            return container

    # 策略3: 查找包含多个段落的容器
    for div in all_divs:
        paragraphs = div.find_all("p")
        if len(paragraphs) >= 3:  # 至少3个段落
            total_p_text = sum(len(p.get_text(strip=True)) for p in paragraphs)
            if total_p_text > text_length_threshold:
                logging.debug(f"找到多段落容器，段落数: {len(paragraphs)}")
                return div

    logging.debug("智能内容检测未找到合适的内容")
    return None


def analyze_page_error(soup, response, url):
    """
    分析页面错误类型，区分404、登录要求、解析失败等
    """
    page_text = response.text.lower()

    # 检查404错误
    if "404" in page_text or "not found" in page_text or "页面不存在" in page_text:
        return "该文章链接被404, 无法直接访问"

    # 检查登录要求
    if "登录" in response.text or "login" in page_text or "请先登录" in response.text:
        return "该文章需要登录访问，请检查cookies配置"

    # 检查访问权限
    if "403" in page_text or "forbidden" in page_text or "访问被拒绝" in response.text:
        return "该文章访问被拒绝，可能需要特殊权限"

    # 检查内容是否被删除
    if (
        "已删除" in response.text
        or "内容不存在" in response.text
        or "deleted" in page_text
    ):
        return "该文章内容已被删除或不存在"

    # 检查是否有重定向
    if response.url != url:
        return f"页面被重定向到: {response.url}, 可能是登录页面或错误页面"

    # 检查页面是否包含正常的知乎页面结构
    zhihu_indicators = ["知乎", "zhihu", "www.zhihu.com"]
    has_zhihu_structure = any(indicator in page_text for indicator in zhihu_indicators)

    if not has_zhihu_structure:
        return "页面结构异常，可能不是正常的知乎页面"

    # 如果页面看起来正常但找不到内容，可能是页面结构变化
    return "页面结构可能发生变化，无法解析文章内容"


debug_log_file = setup_debug_logging()

cookies = load_cookies()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.zhihu.com/",
    "x-zse-93": "101_3_3.0",
    "x-zse-96": "2.0_3pMeV7de2ZCOYdR1sA1_MPH3NUYhNeCg9c2jOYKNOL3F2lnZg5HE02o0HSgWHX2aRdK5Oj8bSpSRRWM6IXefO0eQH2pD2LvjFFecfICcrswg8P0gMcPAqHrJ5kHeGYQBJQsr8q6NLTKcPHCqyGR9ov8kXFwGbe_LFNbqYpJTgYrKOLCuqA2ASU6pI-DNswzSqPcz8QdYnDkBMQf0KpLcJyftiBwOZzbfDNEFQAGAfCNWzIQzhNeRJdXqVFyGqqLoDo8w2eBp6ZsfgxHtEirXyBoWMV9FUSZHTY7msV7_VrK3e4ty5x0e7_LEu5",
    "sec-ch-ua": '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# API 请求的 headers（用于获取回答/专栏内容）
# 注: x-zse-93/x-zse-96 是知乎专栏文章 API 必需的反爬头，缺一不可
# 值由知乎前端 JS 动态生成，若失效需从浏览器请求中重新提取
api_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zhihu.com/",
    "x-requested-with": "fetch",
    "x-zse-93": "101_3_3.0",
    "x-zse-96": "2.0_3pMeV7de2ZCOYdR1sA1_MPH3NUYhNeCg9c2jOYKNOL3F2lnZg5HE02o0HSgWHX2aRdK5Oj8bSpSRRWM6IXefO0eQH2pD2LvjFFecfICcrswg8P0gMcPAqHrJ5kHeGYQBJQsr8q6NLTKcPHCqyGR9ov8kXFwGbe_LFNbqYpJTgYrKOLCuqA2ASU6pI-DNswzSqPcz8QdYnDkBMQf0KpLcJyftiBwOZzbfDNEFQAGAfCNWzIQzhNeRJdXqVFyGqqLoDo8w2eBp6ZsfgxHtEirXyBoWMV9FUSZHTY7msV7_VrK3e4ty5x0e7_LEu5",
    "sec-ch-ua": '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


class ObsidianStyleConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """

    def chomp(self, text):
        """
        If the text in an inline tag like b, a, or em contains a leading or trailing
        space, strip the string and return a space as suffix of prefix, if needed.
        This function is used to prevent conversions like
            <b> foo</b> => ** foo**
        """
        prefix = " " if text and text[0] == " " else ""
        suffix = " " if text and text[-1] == " " else ""
        text = text.strip()
        return (prefix, suffix, text)

    def convert_img(self, *args, **kwargs):
        logging.debug(f"convert_img called with args: {args}, kwargs={kwargs}")
        try:
            # 提取参数，适配不同的调用方式
            if len(args) >= 2:
                el, text = args[0], args[1]
            else:
                el = kwargs.get("el")
                text = kwargs.get("text", "")

            alt = el.attrs.get("alt", None) or ""
            src = el.attrs.get("src", None) or ""

            # 使用全局变量获取当前收藏夹名称
            global current_collection_name
            downloadDir = get_output_path(current_collection_name)
            if not os.path.exists(downloadDir):
                os.makedirs(downloadDir)
            assetsDir = os.path.join(downloadDir, "assets")
            if not os.path.exists(assetsDir):
                os.makedirs(assetsDir)

            try:
                img_content = requests.get(
                    url=src, headers=headers, cookies=cookies, timeout=30
                ).content
            except Exception as img_e:
                # 图片下载失败不致命，保留原始 URL
                logging.warning(f"图片下载失败: {src} - {img_e}")
                result = "![%s](%s)\n\n" % (alt, src)
                return result
            
            img_content_name = src.split("?")[0].split("/")[-1]

            imgPath = os.path.join(assetsDir, img_content_name)
            with open(imgPath, "wb") as fp:
                fp.write(img_content)

            result = "![[%s]]\n(%s)\n\n" % (img_content_name, alt)
            logging.debug(f"convert_img returning: {result}")
            return result
        except Exception as e:
            logging.error(f"convert_img error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            # 不 raise，降级为保留原始图片 URL
            return "![%s](%s)\n\n" % (alt, src)

    def convert_a(self, *args, **kwargs):
        logging.debug(f"convert_a called with args: {args}, kwargs={kwargs}")
        try:
            # 提取参数，适配不同的调用方式
            if len(args) >= 2:
                el, text = args[0], args[1]
                convert_as_inline = args[2] if len(args) > 2 else None
            else:
                el = kwargs.get("el")
                text = kwargs.get("text", "")
                convert_as_inline = kwargs.get("convert_as_inline")

            prefix, suffix, text = self.chomp(text)
            if not text:
                return ""
            href = el.get("href")
            # title = el.get('title')

            if el.get("aria-labelledby") and el.get("aria-labelledby").find("ref") > -1:
                text = text.replace("[", "[^")
                result = "%s" % text
                logging.debug(f"convert_a returning (aria-labelledby): {result}")
                return result
            if (el.attrs and "data-reference-link" in el.attrs) or (
                "class" in el.attrs and ("ReferenceList-backLink" in el.attrs["class"])
            ):
                text = "[^{}]: ".format(href[5])
                result = "%s" % text
                logging.debug(f"convert_a returning (reference-link): {result}")
                return result

            # 调用父类方法，适配不同的参数组合
            try:
                if convert_as_inline is not None:
                    result = super(ObsidianStyleConverter, self).convert_a(
                        el, text, convert_as_inline, **kwargs
                    )
                else:
                    result = super(ObsidianStyleConverter, self).convert_a(
                        el, text, **kwargs
                    )
            except TypeError:
                # 如果参数不匹配，尝试不同的调用方式
                try:
                    result = super(ObsidianStyleConverter, self).convert_a(
                        *args, **kwargs
                    )
                except TypeError:
                    result = super(ObsidianStyleConverter, self).convert_a(el, text)

            logging.debug(f"convert_a returning (super): {result}")
            return result
        except Exception as e:
            logging.error(f"convert_a error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    def convert_li(self, *args, **kwargs):
        logging.debug(f"convert_li called with args: {args}, kwargs={kwargs}")
        try:
            # 提取参数，适配不同的调用方式
            if len(args) >= 2:
                el, text = args[0], args[1]
                convert_as_inline = args[2] if len(args) > 2 else None
            else:
                el = kwargs.get("el")
                text = kwargs.get("text", "")
                convert_as_inline = kwargs.get("convert_as_inline")

            if el and el.find("a", {"aria-label": "back"}) is not None:
                result = "%s\n" % ((text or "").strip())
                logging.debug(f"convert_li returning (aria-label back): {result}")
                return result

            # 调用父类方法，适配不同的参数组合
            try:
                if convert_as_inline is not None:
                    result = super(ObsidianStyleConverter, self).convert_li(
                        el, text, convert_as_inline, **kwargs
                    )
                else:
                    result = super(ObsidianStyleConverter, self).convert_li(
                        el, text, **kwargs
                    )
            except TypeError:
                # 如果参数不匹配，尝试不同的调用方式
                try:
                    result = super(ObsidianStyleConverter, self).convert_li(
                        *args, **kwargs
                    )
                except TypeError:
                    result = super(ObsidianStyleConverter, self).convert_li(el, text)

            logging.debug(f"convert_li returning (super): {result}")
            return result
        except Exception as e:
            logging.error(f"convert_li error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise


def markdownify(html, **options):
    return ObsidianStyleConverter(**options).convert(html)


# 获取收藏夹的回答总数
def get_article_nums_of_collection(collection_id):
    """
    :param starturl: 收藏夹连接
    :return: 收藏夹的页数
    """
    try:
        collection_url = "https://www.zhihu.com/api/v4/collections/{}/items".format(
            collection_id
        )
        html = requests.get(collection_url, headers=headers, cookies=cookies, timeout=30)
        html.raise_for_status()

        # 页面总数
        result = html.json()["paging"].get("totals")
        logging.info(f"收藏夹 {collection_id} 包含 {result} 个项目")
        return result
    except Exception as e:
        logging.error(f"获取收藏夹 {collection_id} 总数失败: {str(e)}")
        return 0


# 解析出每个回答的具体链接
def get_article_urls_in_collection(collection_id):
    collection_id = collection_id.replace("\n", "")
    logging.info(f"开始获取收藏夹 {collection_id} 的文章列表")

    offset = 0
    limit = 20

    article_nums = get_article_nums_of_collection(collection_id)

    if article_nums is None or article_nums == 0:
        logging.warning(f"收藏夹 {collection_id} 没有文章或获取失败")
        return [], []

    url_list = []
    title_list = []
    while offset < article_nums:
        collection_url = "https://www.zhihu.com/api/v4/collections/{}/items?offset={}&limit={}".format(
            collection_id, offset, limit
        )
        try:
            logging.info(f"请求收藏夹API: offset={offset}, limit={limit}")
            html = requests.get(collection_url, headers=headers, cookies=cookies, timeout=30)
            html.raise_for_status()
            content = html.json()
            logging.info(f"成功获取 {len(content.get('data', []))} 个项目")
        except Exception as e:
            logging.error(f"请求收藏夹API失败: {str(e)}")
            # 返回已获取的内容而不是None
            return url_list, title_list

        for el in content.get("data", []):
            try:
                url_list.append(el["content"]["url"])
                if el["content"]["type"] == "answer":
                    title_list.append(el["content"]["question"]["title"])
                else:
                    title_list.append(el["content"]["title"])
                logging.debug(f"添加文章: {el['content'].get('title', '未知标题')}")
            except Exception as e:
                logging.warning(f"解析文章项目失败: {str(e)}")
                print("********")
                print("TBD 非回答, 非专栏, 想法类收藏暂时无法处理")
                for k, v in el["content"].items():
                    if k in ["type", "url"]:
                        print(k, v)
                print("********")
                # 如果已经添加了URL，需要移除对应的URL
                if len(url_list) > len(title_list):
                    url_list.pop()

        offset += limit

    logging.info(f"收藏夹 {collection_id} 总共获取到 {len(url_list)} 个有效文章")
    return url_list, title_list


# 获得单条答案的数据
def get_single_answer_content(answer_url):
    # zvideo/pin 内容不支持，快速返回避免 HTTP 超时浪费
    if '/zvideo/' in answer_url or '/pin/' in answer_url:
        return -1

    logging.debug(f"开始获取回答内容: {answer_url}")
    flush_logs()

    # 从URL中提取answer_id（用于API备用请求）
    # URL格式: https://www.zhihu.com/question/xxx/answer/yyy 或 https://www.zhihu.com/question/xxx/answer/yyy?param
    import re

    answer_id_match = re.search(r"/answer/(\d+)", answer_url)
    answer_id = answer_id_match.group(1) if answer_id_match else None

    try:
        # 发送请求（加 timeout 防网络卡死）
        html_content = requests.get(answer_url, headers=headers, cookies=cookies, timeout=30)
        logging.debug(f"HTTP请求状态码: {html_content.status_code}")

        # 如果返回403，尝试使用API备用方案
        if html_content.status_code == 403:
            logging.warning(f"HTML请求返回403，尝试API备用方案: {answer_url}")
            flush_logs()

            if answer_id:
                api_url = (
                    f"https://www.zhihu.com/api/v4/answers/{answer_id}?include=content"
                )
                logging.debug(f"调用API: {api_url}")

                try:
                    api_response = requests.get(
                        api_url, headers=api_headers, cookies=cookies, timeout=30
                    )
                    api_response.raise_for_status()
                    api_data = api_response.json()

                    if api_data and "content" in api_data:
                        # API返回的content是HTML格式的回答内容
                        content_html = api_data["content"]
                        logging.info(
                            f"API备用方案成功获取内容，长度: {len(content_html)}"
                        )
                        flush_logs()

                        # 直接使用API返回的HTML内容，不需要BeautifulSoup解析
                        # 但需要处理图片和链接卡片
                        soup = BeautifulSoup(content_html, "lxml")

                        # 去除不必要的style标签
                        for el in soup.find_all("style"):
                            el.extract()

                        for el in soup.select('img[src*="data:image/svg+xml"]'):
                            el.extract()

                        for el in soup.find_all("a"):
                            aclass = el.get("class")
                            if isinstance(aclass, list) and "LinkCard" in aclass:
                                linkcard_name = el.get("data-text")
                                el.string = (
                                    linkcard_name
                                    if linkcard_name is not None
                                    else el.get("href")
                                )
                            try:
                                if el.get("href") and el.get("href").startswith(
                                    "mailto"
                                ):
                                    el.name = "p"
                            except:
                                pass

                        # 添加html外层标签
                        answer_content = html_template(soup)
                        return answer_content

                except Exception as api_e:
                    logging.error(f"API备用方案失败: {str(api_e)}")
                    flush_logs()
            else:
                logging.error(f"无法从URL提取answer_id: {answer_url}")
                flush_logs()
                return -1

        html_content.raise_for_status()
        logging.debug(f"HTTP请求成功，状态码: {html_content.status_code}")

        soup = BeautifulSoup(html_content.text, "lxml")

        # 尝试多种可能的选择器
        answer_content = None
        selectors = [
            ("div", {"class": "AnswerCard"}),
            ("div", {"class": "QuestionAnswer-content"}),
            ("div", {"class": "RichContent"}),
            ("div", {"class": "ContentItem-expandButton"}),
        ]

        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs)
            if elements:
                logging.debug(f"找到{len(elements)}个 {tag} {attrs} 元素")
                for element in elements:
                    inner = element.find("div", class_="RichContent-inner")
                    if inner:
                        answer_content = inner
                        logging.debug("成功找到RichContent-inner元素")
                        break
                if answer_content:
                    break

        # 如果还没找到，尝试直接查找RichContent-inner
        if not answer_content:
            answer_content = soup.find("div", class_="RichContent-inner")
            if answer_content:
                logging.debug("直接找到RichContent-inner元素")

        # 如果仍未找到，尝试其他可能的内容容器
        if not answer_content:
            fallback_selectors = [
                "div.RichText",
                "div.Post-RichText",
                "div.ContentItem-content",
                ".QuestionAnswer .RichContent",
            ]

            for selector in fallback_selectors:
                answer_content = soup.select_one(selector)
                if answer_content:
                    logging.debug(f"使用备用选择器找到内容: {selector}")
                    break

        if not answer_content:
            logging.error(f"未找到回答内容容器: {answer_url}")
            # 保存页面HTML以供调试
            debug_dir = get_debug_path()
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(
                debug_dir, f"debug_answer_{answer_url.split('/')[-1]}.html"
            )
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html_content.text)
            logging.debug(f"页面HTML已保存到: {debug_file}")
            flush_logs()
            return -1

        # 去除不必要的style标签
        for el in answer_content.find_all("style"):
            el.extract()

    except Exception as e:
        logging.error(f"获取回答内容时发生错误: {str(e)}")
        logging.error(f"URL: {answer_url}")
        flush_logs()
        return -1

    for el in answer_content.select('img[src*="data:image/svg+xml"]'):
        el.extract()

    for el in answer_content.find_all("a"):  # 处理回答中的卡片链接
        aclass = el.get("class")
        if isinstance(aclass, list):
            if aclass[0] == "LinkCard":
                linkcard_name = el.get("data-text")
                el.string = (
                    linkcard_name if linkcard_name is not None else el.get("href")
                )
        else:
            pass
        try:
            if el.get(
                "href"
            ).startswith(
                "mailto"
            ):  # 特殊bug, 正文的aaa@bbb.ccc会被识别为邮箱, 嵌入<a href='mailto:xxx'>中, markdown转换时会报错
                el.name = "p"
        except:
            print(answer_url, el)  # 一些广告卡片, 不需要处理

    # 添加html外层标签
    answer_content = html_template(answer_content)

    return answer_content


# 获取单条专栏文章的内容
def get_single_post_content(paper_url):
    logging.debug(f"开始获取专栏文章内容: {paper_url}")
    flush_logs()

    # 如果HTTP请求失败，尝试API备用方案
    # 从URL提取article_id: zhuanlan.zhihu.com/p/{id}
    import re
    article_id_match = re.search(r"zhuanlan\.zhihu\.com/p/(\d+)", paper_url)
    article_id = article_id_match.group(1) if article_id_match else None

    # 尝试API备用方案（先试，因为API更可靠）
    if article_id:
        try:
            api_url = f"https://www.zhihu.com/api/v4/articles/{article_id}?include=content"
            api_response = requests.get(api_url, headers=api_headers, cookies=cookies, timeout=30)
            if api_response.status_code == 200:
                api_data = api_response.json()
                if api_data and "content" in api_data:
                    content_html = api_data["content"]
                    logging.info(f"API备用方案成功获取专栏内容，长度: {len(content_html)}")
                    flush_logs()
                    soup = BeautifulSoup(content_html, "lxml")
                    for el in soup.find_all("style"):
                        el.extract()
                    for el in soup.select('img[src*="data:image/svg+xml"]'):
                        el.extract()
                    post_content_html = html_template(soup)
                    return post_content_html
        except Exception as api_e:
            logging.warning(f"专栏API备用方案失败: {str(api_e)}")
            flush_logs()

    # API失败时回退到HTML请求
    max_retries = 2
    last_error = None

    for retry in range(max_retries):
        post_content = None
        try:
            # 发送请求，添加超时设置，使用流式下载处理大文章
            html_content = requests.get(
                paper_url, headers=headers, cookies=cookies, timeout=120, stream=True
            )
            html_content.raise_for_status()
            logging.debug(f"HTTP请求成功，状态码: {html_content.status_code}")

            # 流式读取内容，避免大文章的网络中断问题
            content_bytes = b""
            for chunk in html_content.iter_content(chunk_size=8192):
                if chunk:
                    content_bytes += chunk
            html_text = content_bytes.decode("utf-8", errors="ignore")
            logging.debug(f"内容长度: {len(html_text)} 字符")

            soup = BeautifulSoup(html_text, "lxml")

            # 尝试多种可能的选择器
            selectors = [
                ("div", {"class": "Post-RichText"}),
                ("div", {"class": "RichContent"}),
                ("div", {"class": "RichContent-inner"}),
                ("div", {"class": "Post-content"}),
                ("div", {"class": "Post-RichTextContainer"}),
                ("div", {"class": "ztext"}),
                ("div", {"class": "Post-Main"}),
                ("div", {"class": "Article-RichText"}),
            ]

            for tag, attrs in selectors:
                post_content = soup.find(tag, attrs)
                if post_content:
                    logging.debug(f"找到专栏内容: {tag} {attrs}")
                    break

            # 如果还没找到，尝试CSS选择器
            if not post_content:
                fallback_selectors = [
                    "div.RichText",
                    "div.Post-content",
                    "div.ContentItem-content",
                    ".Post .RichContent",
                    ".Post-RichTextContainer",
                    ".ztext",
                    ".Post-Main .RichContent",
                    "[data-zop-editor]",
                    ".Article-RichText",
                ]

                for selector in fallback_selectors:
                    post_content = soup.select_one(selector)
                    if post_content:
                        logging.debug(f"使用备用选择器找到内容: {selector}")
                        break

            # 如果仍然没找到，尝试智能内容检测
            if not post_content:
                post_content = smart_content_detection(soup, paper_url)
                if post_content:
                    logging.debug("使用智能内容检测找到内容")

            if not post_content:
                # 检查是否是真正的404或其他错误
                error_message = analyze_page_error(soup, html_content, paper_url)

                logging.error(f"未找到专栏内容容器: {paper_url} - {error_message}")
                # 保存页面HTML以供调试
                debug_dir = get_debug_path()
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(
                    debug_dir, f"debug_post_{paper_url.split('/')[-1]}.html"
                )
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html_content.text)
                logging.debug(f"页面HTML已保存到: {debug_file}")
                flush_logs()
                post_content = error_message

            if post_content and hasattr(post_content, "find_all"):
                # 去除不必要的style标签
                for el in post_content.find_all("style"):
                    el.extract()

                for el in post_content.select('img[src*="data:image/svg+xml"]'):
                    el.extract()

                for el in post_content.find_all("a"):  # 处理专栏文章中的卡片链接
                    aclass = el.get("class")
                    if isinstance(aclass, list):
                        if aclass[0] == "LinkCard":
                            linkcard_name = el.get("data-text")
                            el.string = (
                                linkcard_name
                                if linkcard_name is not None
                                else el.get("href")
                            )
                    else:
                        pass
                    try:
                        if el.get(
                            "href"
                        ).startswith(
                            "mailto"
                        ):  # 特殊bug, 正文的aaa@bbb.ccc会被识别为邮箱, 嵌入<a href='mailto:xxx'>中, markdown转换时会报错
                            el.name = "p"
                    except:
                        logging.warning(f"处理链接时出现问题: {paper_url}, {el}")

            # 成功获取内容，跳出重试循环
            if post_content:
                break

        except Exception as e:
            last_error = str(e)
            logging.warning(
                f"获取专栏文章内容时发生错误 (尝试 {retry + 1}/{max_retries}): {str(e)}"
            )
            logging.warning(f"URL: {paper_url}")
            flush_logs()

            if retry < max_retries - 1:
                import time

                time.sleep(2)  # 等待2秒后重试
                continue
            else:
                logging.error(f"达到最大重试次数，放弃: {paper_url}")
                flush_logs()
                post_content = f"该文章链接获取失败: {last_error}"

    # 添加html外层标签
    post_content = html_template(post_content)

    return post_content


def html_template(data):
    # api content
    html = (
        """
        <html>
        <head>
        </head>
        <body>
        %s
        </body>
        </html>
        """
        % data
    )
    return html


def is_article_already_downloaded(file_path, target_url):
    """
    检查文件是否已存在且包含相同的URL
    :param file_path: 要检查的markdown文件路径
    :param target_url: 目标URL
    :return: True如果文件存在且URL匹配，False否则
    """
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            # 检查第一行是否为引用块且包含目标URL
            if first_line.startswith("> ") and target_url in first_line:
                return True
    except:
        pass

    return False


def get_unique_filename(base_dir, title, url):
    """
    获取唯一的文件名，如果标题重复则添加URL的ID部分
    :param base_dir: 基础目录
    :param title: 文章标题
    :param url: 文章URL
    :return: 唯一的文件路径
    """
    base_filename = filter_title_str(title)
    file_path = os.path.join(base_dir, base_filename + ".md")

    # 如果文件不存在，直接返回
    if not os.path.exists(file_path):
        return file_path

    # 如果文件存在且URL匹配，返回该路径（用于跳过）
    if is_article_already_downloaded(file_path, url):
        return file_path

    # 如果文件存在但URL不匹配，添加URL ID后缀
    url_id = url.split("/")[-1]
    unique_filename = f"{base_filename}_{url_id}"
    return os.path.join(base_dir, unique_filename + ".md")


def save_processing_log():
    """
    保存处理日志到logs目录
    """
    logs_dir = get_logs_path()
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}.json"
    log_path = os.path.join(logs_dir, log_filename)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(processing_log, f, ensure_ascii=False, indent=2)

    print(f"处理日志已保存到: {log_path}")


def flush_logs():
    """强制刷新所有日志处理器"""
    import sys

    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        try:
            if hasattr(handler, "flush"):
                handler.flush()
            # 如果是文件处理器，强制同步
            if hasattr(handler, "stream") and hasattr(handler.stream, "flush"):
                handler.stream.flush()
                # 强制操作系统刷新
                if hasattr(handler.stream, "fileno"):
                    try:
                        os.fsync(handler.stream.fileno())
                    except:
                        pass
        except:
            pass

    # 强制刷新标准输出
    sys.stdout.flush()
    sys.stderr.flush()


def process_single_collection(collection_name, collection_url):
    """处理单个收藏夹"""
    global current_collection_name, processing_log
    current_collection_name = collection_name

    logging.info(f"开始处理收藏夹: {collection_name}")
    logging.info(f"收藏夹URL: {collection_url}")
    flush_logs()

    try:
        collection_id = collection_url.split("?")[0].split("/")[-1]
        logging.info(f"解析得到收藏夹ID: {collection_id}")
        flush_logs()

        urls, titles = get_article_urls_in_collection(collection_id)

        if not urls:
            logging.warning(f"收藏夹 '{collection_name}' 没有获取到任何文章")
            flush_logs()
            return

    except Exception as e:
        logging.error(f"处理收藏夹 '{collection_name}' 时发生错误: {str(e)}")
        logging.error(f"错误详情: {traceback.format_exc()}")
        flush_logs()
        return

    # 初始化此收藏夹的日志记录
    collection_log = {"name": collection_name, "url": collection_url, "list": []}

    # 验证数据一致性
    if len(urls) != len(titles):
        error_msg = f"地址标题列表长度不一致: urls={len(urls)}, titles={len(titles)}"
        logging.error(error_msg)
        flush_logs()
        processing_log.append(collection_log)
        return

    print(f"收藏夹 '{collection_name}' 共获取 {len(urls)} 篇可导出回答或专栏")

    downloadDir = get_output_path(collection_name)
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)

    for i in tqdm(range(len(urls)), desc=f"处理 {collection_name}"):
        content = None
        url = urls[i]
        title = titles[i]

        # 获取唯一的文件路径
        file_path = get_unique_filename(downloadDir, title, url)

        # 初始化文章日志记录
        article_log = {"name": title, "url": url, "status": ""}

        # 检查文件是否已存在且包含相同URL
        if is_article_already_downloaded(file_path, url):
            article_log["status"] = "文章已存在,跳过下载"
            collection_log["list"].append(article_log)
            continue

        try:
            logging.info(f"开始下载文章: {title}")
            flush_logs()

            if url.find("zhuanlan") != -1:
                content = get_single_post_content(url)
            else:
                content = get_single_answer_content(url)

            if content == -1:
                article_log["status"] = f"文章下载失败, 原因:获取内容失败"
                collection_log["list"].append(article_log)
                logging.warning(f"获取内容失败: {url}")
                flush_logs()
                continue

            md = markdownify(content, heading_style="ATX")
            md = "> %s\n" % url + md

            with open(file_path, "w", encoding="utf-8") as md_file:
                md_file.write(md)

            article_log["status"] = "文章不存在,正常下载"
            collection_log["list"].append(article_log)
            logging.info(f"文章下载成功: {title}")
            flush_logs()

            # 添加延时
            time.sleep(random.randint(1, 5))

        except Exception as e:
            article_log["status"] = f"文章下载失败, 原因:{str(e)}"
            collection_log["list"].append(article_log)
            logging.error(f"下载文章时发生错误: {title}")
            logging.error(f"错误详情: {str(e)}")
            logging.error(f"URL: {url}")
            flush_logs()

    # 将收藏夹日志添加到全局日志
    processing_log.append(collection_log)
    print(f"收藏夹 '{collection_name}' 下载完毕")


# ──────────────────────────────────────────────
# 取消收藏功能
# ──────────────────────────────────────────────


def parse_article_info(url):
    """
    解析文章URL，提取 content_id 和 content_type

    支持格式：
      - https://www.zhihu.com/question/xxx/answer/yyy   → answer, yyy
      - https://zhuanlan.zhihu.com/p/xxx                  → article, xxx
      - https://www.zhihu.com/zvideo/xxx                  → zvideo, xxx
      - https://www.zhihu.com/pin/xxx                     → pin, xxx
    """
    import re

    # 匹配回答: /question/xxx/answer/yyy 或 /question/xxx/answer/yyy?...
    m = re.search(r"/question/\d+/answer/(\d+)", url)
    if m:
        return m.group(1), "answer"

    # 匹配专栏文章: /p/xxx
    m = re.search(r"zhuanlan\.zhihu\.com/p/(\d+)", url)
    if m:
        return m.group(1), "article"

    # 匹配视频: /zvideo/xxx
    m = re.search(r"/zvideo/(\d+)", url)
    if m:
        return m.group(1), "zvideo"

    # 匹配想法: /pin/xxx
    m = re.search(r"/pin/(\d+)", url)
    if m:
        return m.group(1), "pin"

    # 兜底：取URL最后一段数字
    m = re.search(r"/(\d+)(?:\?|#|$)", url)
    if m:
        return m.group(1), "unknown"

    return None, None


def unfavorite_content(content_type, content_id):
    """
    取消收藏指定内容（从收藏夹中移除）

    通过 Playwright 浏览器抓包确定的正确 API 端点：
      DELETE https://www.zhihu.com/api/v4/collections/contents/{content_type}/{content_id}

    验证结果：
      - DELETE → 200 {"data":[...], "success":true}  ✅ 取消收藏
      - POST   → 200 {"collection":{...}, "success":true}  ✅ 添加收藏

    关键请求头：
      - X-Xsrftoken: CSRF token（从 cookies 中的 _xsrf 获取）
      - x-zse-93: "101_3_3.0"

    :param content_type: 内容类型 (answer/article/zvideo/pin)
    :param content_id: 内容ID
    :return: (success: bool, message: str)
    """
    api_url = (
        f"https://www.zhihu.com/api/v4/collections/contents/{content_type}/{content_id}"
    )

    # 获取 CSRF token
    xsrf_token = cookies.get("_xsrf", "") if isinstance(cookies, dict) else ""

    # 专用请求头（从浏览器拦截复制）
    unfav_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.zhihu.com/",
        "x-requested-with": "fetch",
        "x-zse-93": "101_3_3.0",
        "Content-Type": "application/json",
    }
    if xsrf_token:
        unfav_headers["X-Xsrftoken"] = xsrf_token

    logging.info(f"取消收藏: DELETE {api_url}")

    try:
        resp = requests.delete(
            api_url,
            headers=unfav_headers,
            cookies=cookies,
            timeout=30,
        )

        if resp.status_code == 200:
            try:
                result = resp.json()
                if result.get("success"):
                    favlists_count = result.get("favlists_count", "?")
                    logging.info(f"取消收藏成功, 当前收藏数: {favlists_count}")
                    return True, f"✅ 已取消收藏 (content_id={content_id})"
                else:
                    return True, f"✅ 已取消收藏 (content_id={content_id})"
            except json.JSONDecodeError:
                return True, f"✅ 已取消收藏 (content_id={content_id})"

        if resp.status_code in (201, 204):
            return True, f"✅ 已取消收藏 (content_id={content_id})"

        # 如果是403且错误是"未收藏"，那说明本来就没收藏，也算成功
        if resp.status_code == 403:
            try:
                err = resp.json()
                if "未收藏" in str(err.get("error", {})):
                    return True, f"✅ 本来就没有收藏该内容 (content_id={content_id})"
            except:
                pass

        error_body = resp.text[:300] if resp.text else "无响应体"
        return False, (
            f"❌ 取消收藏失败 (HTTP {resp.status_code})\n"
            f"   响应: {error_body}\n"
            f"   提示: 可能是Cookies已过期，请重新登录获取 cookies.json"
        )

    except requests.exceptions.Timeout:
        return False, f"❌ 请求超时（30s），请检查网络连接"
    except requests.exceptions.ConnectionError as e:
        return False, f"❌ 网络连接失败: {str(e)}"
    except Exception as e:
        logging.error(f"取消收藏异常: {str(e)}")
        return False, f"❌ 操作异常: {str(e)}"


def remove_from_collection(collection_url, article_url):
    """
    从知乎收藏夹中移除一篇文章（取消收藏）

    通过浏览器抓包验证的正确 API：
      DELETE https://www.zhihu.com/api/v4/collections/contents/{content_type}/{content_id}
      返回: {"data":[...], "favlists_count":N, "success":true}

    :param collection_url: 收藏夹URL（仅用于日志）
    :param article_url: 要移除的文章URL
    :return: (success: bool, message: str)
    """
    collection_id = collection_url.split("?")[0].split("/")[-1]
    content_id, content_type = parse_article_info(article_url)

    if not content_id:
        return False, f"❌ 无法从URL中解析文章ID: {article_url}"

    logging.info(
        f"取消收藏: 收藏夹={collection_id}, content_id={content_id}, type={content_type}"
    )

    return unfavorite_content(content_type, content_id)


def remove_articles_from_collection(collection_url, article_urls):
    """
    批量从收藏夹中移除多篇文章

    :param collection_url: 收藏夹URL
    :param article_urls: 文章URL列表
    :return: [(success, message, url), ...]
    """
    results = []
    for url in article_urls:
        success, msg = remove_from_collection(collection_url, url)
        results.append((success, msg, url))
        time.sleep(random.uniform(0.5, 1.5))  # 避免请求过快
    return results


if __name__ == "__main__":
    # 加载配置
    config = load_config()

    # 解析输出路径
    if config.get("outputPath"):
        base_output_path = parse_output_path(config["outputPath"], config.get("os", ""))
        if base_output_path:
            print(f"使用自定义输出路径: {base_output_path}")
            # 重新配置日志路径
            reconfigure_logging()
        else:
            print("输出路径解析失败，使用默认路径")
            base_output_path = None
    else:
        print("使用默认输出路径: downloads/")

    # 检查是否启用openCollection模式
    open_collection_mode = config.get("openCollection", False)

    if open_collection_mode:
        print("检测到openCollection模式已启用")
        print("请先运行 python fetch_collections.py 获取收藏夹列表")
        print("然后将config.json中的openCollection设为false，重新运行此程序")
        sys.exit(1)

    # 常规模式：处理收藏夹下载
    zhihu_collections = config.get("zhihuUrls", [])

    if not zhihu_collections:
        print("没有找到要处理的收藏夹配置")
        print("提示：请运行 python fetch_collections.py 自动获取收藏夹列表")
        sys.exit(1)

    print(f"共找到 {len(zhihu_collections)} 个收藏夹待处理")

    for collection in zhihu_collections:
        collection_name = collection.get("name", "未命名收藏夹")
        collection_url = collection.get("url", "")

        if not collection_url:
            print(f"收藏夹 '{collection_name}' 缺少URL，跳过")
            continue

        print(f"\n开始处理收藏夹: {collection_name}")
        process_single_collection(collection_name, collection_url)

    print("\n所有收藏夹处理完毕!")

    # 保存处理日志
    save_processing_log()

# def testMarkdownifySingleAnswer():
#     url = "https://www.zhihu.com/question/506166712/answer/2271842801"
#     content = get_single_answer_content(url)
#     md = markdownify(content, heading_style="ATX")
#     id = url.split('/')[-1]
#
#     downloadDir = os.path.join(os.path.dirname(__file__), 'downloads', '剪藏')
#     if not os.path.exists(downloadDir):
#         os.makedirs(downloadDir)
#     with open(os.path.join(downloadDir, id + ".md"), "w", encoding='utf-8') as md_file:
#         md_file.write(md)
#     print("{} 转换成功".format(id))
#
# def testMarkdownifySinglePost():
#     url = 'https://zhuanlan.zhihu.com/p/386395767'
#     content = get_single_post_content(url)
#     md = markdownify(content, heading_style="ATX")
#     id = url.split('/')[-1]
#     with open("./" + id + ".md", "w", encoding='utf-8') as md_file:
#         md_file.write(md)
#     print("{} 转换成功".format(id))
#
#
# # if __name__ == '__main__':
# #     testMarkdownifySingleAnswer()
#
