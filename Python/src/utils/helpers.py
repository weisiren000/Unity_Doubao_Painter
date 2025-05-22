"""
工具函数模块
提供各种通用工具函数
"""

import os
import json
import logging
from pathlib import Path
from PIL import Image
import requests
from io import BytesIO

# 配置日志
logger = logging.getLogger(__name__)

def ensure_dir_exists(directory):
    """
    确保目录存在，如果不存在则创建

    Args:
        directory (str or Path): 目录路径

    Returns:
        Path: 目录路径对象
    """
    directory = Path(directory)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建目录: {directory}")
    return directory


def load_paths_from_config(config_path=None):
    """
    从配置文件加载路径信息

    Args:
        config_path (str or Path, optional): 配置文件路径，如果为None则使用默认路径

    Returns:
        dict: 包含路径信息的字典，如果配置文件不存在则返回None
    """
    try:
        # 如果未指定配置文件路径，则使用默认路径
        if config_path is None:
            # 获取当前文件所在目录
            current_dir = Path(__file__).parent  # utils目录
            src_dir = current_dir.parent  # src目录
            python_dir = src_dir.parent  # Python目录
            project_dir = python_dir.parent  # 项目根目录
            config_path = project_dir / "paths.json"
        else:
            config_path = Path(config_path)

        # 检查配置文件是否存在
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}")
            return None

        # 读取配置文件
        with open(config_path, 'r') as f:
            paths_info = json.load(f)

        logger.info(f"从配置文件加载路径信息: {config_path}")
        return paths_info
    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        return None

def is_image_file(file_path):
    """
    检查文件是否为图片

    Args:
        file_path (str or Path): 文件路径

    Returns:
        bool: 是否为图片文件
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
    return Path(file_path).suffix.lower() in image_extensions

def resize_image(image_path, max_size=(1024, 1024), output_path=None):
    """
    调整图片大小，保持宽高比

    Args:
        image_path (str or Path): 图片路径
        max_size (tuple): 最大宽高
        output_path (str or Path, optional): 输出路径，默认覆盖原图

    Returns:
        Path: 输出图片路径
    """
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.LANCZOS)

        if output_path:
            output_path = Path(output_path)
        else:
            output_path = Path(image_path)

        img.save(output_path)
        logger.info(f"调整图片大小: {image_path} -> {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"调整图片大小失败: {str(e)}")
        return None

def download_image_from_url(url, output_path=None):
    """
    从URL下载图片

    Args:
        url (str): 图片URL
        output_path (str or Path, optional): 输出路径

    Returns:
        Image or None: PIL图像对象或None（如果失败）
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))

        if output_path:
            output_path = Path(output_path)
            img.save(output_path)
            logger.info(f"下载图片: {url} -> {output_path}")

        return img
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
        return None

def get_timestamp_filename(original_filename, prefix="", suffix=""):
    """
    生成基于时间戳的文件名

    Args:
        original_filename (str): 原始文件名
        prefix (str): 前缀
        suffix (str): 后缀

    Returns:
        str: 新文件名
    """
    import time
    timestamp = int(time.time())

    path = Path(original_filename)
    new_name = f"{prefix}{timestamp}{suffix}{path.suffix}"

    return new_name
