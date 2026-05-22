# -*- coding:utf-8 -*-
import json
import logging
import os
import pathlib
import platform


def load_cookies(cookies_path=None):
    if cookies_path is None:
        cookies_path = os.path.join(os.getcwd(), "cookies.json")

    try:
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies_list = json.load(f)
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie["name"]] = cookie["value"]
        return cookies_dict
    except FileNotFoundError:
        msg = "未找到 cookies.json 文件，将使用无登录模式访问（部分内容可能无法获取）"
        print(msg)
        try:
            logging.warning(msg)
        except Exception:
            pass
        return {}


def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("未找到 config.json 文件，尝试读取旧版 zhihuUrls.json 文件")
        try:
            with open("zhihuUrls.json", "r", encoding="utf-8") as f:
                urls = json.load(f)
                return {"zhihuUrls": urls, "outputPath": "", "os": ""}
        except FileNotFoundError:
            print("未找到配置文件，请创建 config.json 文件并配置收藏夹信息")
            return {"zhihuUrls": [], "outputPath": "", "os": ""}


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


def parse_output_path(path_str, os_type):
    if not path_str:
        return None

    if not os_type:
        os_type = get_current_os()

    try:
        if os_type.lower() == "windows":
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
            if path_str.startswith("~"):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["macos", "darwin"]:
            if path_str.startswith("~"):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["cygwin", "msys"]:
            if path_str.startswith("/cygdrive/"):
                drive_path = path_str[10:]
                if len(drive_path) >= 2 and drive_path[1] == "/":
                    path_str = (
                        drive_path[0].upper() + ":" + drive_path[1:].replace("/", "\\")
                    )
            elif path_str.startswith("/") and len(path_str) >= 3 and path_str[2] == "/":
                path_str = path_str[1].upper() + ":" + path_str[2:].replace("/", "\\")
            return pathlib.Path(path_str).resolve()
        else:
            logging.warning(f"未知操作系统类型: {os_type}，尝试通用路径处理")
            if path_str.startswith("~"):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
    except Exception as e:
        logging.error(f"路径解析失败: {path_str}, 错误: {str(e)}")
        return None
