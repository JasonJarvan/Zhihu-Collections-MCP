# -*- coding:utf-8 -*-
from __future__ import annotations

import os
from typing import Optional


def get_output_path(collection_name: str, base_output_path: Optional[str]) -> str:
    """根据基础路径和收藏夹名称生成输出目录路径"""
    if base_output_path:
        return os.path.join(str(base_output_path), collection_name)
    else:
        return os.path.join(os.getcwd(), "downloads", collection_name)


def get_logs_path(base_output_path: Optional[str]) -> str:
    """获取日志输出目录路径"""
    if base_output_path:
        return os.path.join(str(base_output_path), "logs")
    else:
        return os.path.join(os.getcwd(), "downloads", "logs")


def get_debug_path(base_output_path: Optional[str]) -> str:
    """获取调试文件输出目录路径"""
    if base_output_path:
        return os.path.join(str(base_output_path), "debug")
    else:
        return os.path.join(os.getcwd(), "downloads", "debug")
