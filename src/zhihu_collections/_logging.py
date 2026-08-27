# -*- coding:utf-8 -*-
from __future__ import annotations

import os
import sys
import logging
from datetime import datetime
from typing import Optional

from zhihu_collections._paths import get_logs_path


def setup_debug_logging() -> None:
    """初始化调试日志系统，输出到 downloads/logs/ 目录"""
    logs_dir = os.path.join(os.getcwd(), "downloads", "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_log_file = os.path.join(logs_dir, f"debug_{timestamp}.log")

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(debug_log_file, encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info(f"日志系统初始化完成，日志文件: {debug_log_file}")

    for handler in root_logger.handlers:
        if hasattr(handler, "flush"):
            handler.flush()


def reconfigure_logging(base_output_path: Optional[str]) -> str:
    """重新配置日志输出路径（切换到用户指定的目录）

    :return: 新日志文件的完整路径
    """
    logs_dir = get_logs_path(base_output_path)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_log_file = os.path.join(logs_dir, f"debug_{timestamp}.log")

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.flush()
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(debug_log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    return debug_log_file


def flush_logs() -> None:
    """强制刷新所有日志处理器和标准输出流"""
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        try:
            if hasattr(handler, "flush"):
                handler.flush()
            if hasattr(handler, "stream") and hasattr(handler.stream, "flush"):
                handler.stream.flush()
                if hasattr(handler.stream, "fileno"):
                    try:
                        os.fsync(handler.stream.fileno())
                    except:
                        pass
        except:
            pass

    sys.stdout.flush()
    sys.stderr.flush()
