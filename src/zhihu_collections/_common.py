# -*- coding:utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import pathlib
import platform
from typing import Any, Optional


def load_cookies(cookies_path: Optional[str] = None) -> dict[str, str]:
    """从 cookies.json 加载知乎认证 cookies

    :return: cookies 字典，若文件不存在则返回空字典
    """
    if cookies_path is None:
        cookies_path = os.path.join(os.getcwd(), "cookies.json")

    try:
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies_list = json.load(f)
        cookies_dict: dict[str, str] = {}
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


def load_config() -> dict[str, Any]:
    """从 config.json 加载主配置

    :return: 配置字典，若文件不存在则返回默认空配置
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("未找到 config.json 文件，请创建并配置收藏夹信息")
        return {"zhihuUrls": [], "outputPath": "", "os": ""}


def get_current_os() -> str:
    """检测当前操作系统类型"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def resolve_base_output_path(
    cli_output_path: Optional[str], config: dict[str, Any]
) -> tuple[Optional[pathlib.Path], str]:
    """按 CLI 参数 > config.json > 默认 downloads/ 的优先级解析输出目录

    :param cli_output_path: 命令行 -o/--output 参数值,未传则为 None
    :param config: 已加载的 config.json 字典
    :return: (绝对路径 Path 对象或 None, 来源标识: "命令行参数" / "config.json" / "默认")
    """
    config_output_path = config.get("outputPath", "")

    if cli_output_path:
        base_output_path = parse_output_path(
            cli_output_path, config.get("os", "")
        )
        return base_output_path, "命令行参数"

    if config_output_path:
        base_output_path = parse_output_path(
            config_output_path, config.get("os", "")
        )
        return base_output_path, "config.json"

    return None, "默认"


def parse_output_path(path_str: str, os_type: str) -> Optional[pathlib.Path]:
    """跨平台路径解析，处理不同操作系统的路径格式

    支持 Windows/Linux/macOS/Cygwin 等路径格式。

    :param path_str: 原始路径字符串
    :param os_type: 操作系统类型标识
    :return: 解析后的 Path 对象，失败返回 None
    """
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
