"""
图片监控模块
负责监控Screenshots文件夹中的新图片，先调用豆包视觉理解API分析图片生成提示词，再调用豆包API进行图生图
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image

from src.api.doubao_api import DoubaoAPI
from src.api.doubao_vision_api import DoubaoVisionAPI
from src.utils.helpers import is_image_file, ensure_dir_exists
from src.utils.prompt import get_vision_prompt, get_generation_prompt, combine_vision_and_generation

# 配置日志
logger = logging.getLogger(__name__)

class ImageHandler(FileSystemEventHandler):
    """处理图片文件事件的类"""

    def __init__(self, screenshots_dir, outputs_dir, api, vision_api):
        """
        初始化图片处理器

        Args:
            screenshots_dir (str): 截图文件夹路径
            outputs_dir (str): 输出文件夹路径
            api (DoubaoAPI): 豆包API客户端实例
            vision_api (DoubaoVisionAPI): 豆包视觉理解API客户端实例
        """
        self.screenshots_dir = Path(screenshots_dir)
        self.outputs_dir = Path(outputs_dir)
        self.api = api
        self.vision_api = vision_api
        self.processed_files = set()
        self.processing_lock = False  # 防止并发处理

        # 确保输出目录存在
        ensure_dir_exists(self.outputs_dir)

        logger.info(f"图片处理器初始化完成，监控目录: {self.screenshots_dir}")

    def on_created(self, event):
        """
        当新文件创建时触发
        立即将文件添加到待处理队列，不进行实际处理
        实际处理由监控线程的_check_for_new_images方法完成

        Args:
            event: 文件系统事件
        """
        if not event.is_directory and is_image_file(event.src_path):
            file_path = Path(event.src_path)

            # 避免重复处理
            if str(file_path) in self.processed_files:
                return

            logger.info(f"检测到新图片创建事件: {file_path}")

            # 等待文件写入完成
            if self._wait_for_file_ready(file_path):
                logger.info(f"文件已准备就绪，等待处理: {file_path}")
            else:
                logger.warning(f"文件未准备就绪，可能需要稍后重试: {file_path}")

            # 注意：不在这里处理图片，而是让监控线程的_check_for_new_images方法处理
            # 这样可以避免并发问题，并确保所有图片都能被处理

    def _wait_for_file_ready(self, file_path, timeout=5, check_interval=0.1):
        """
        等待文件写入完成

        Args:
            file_path (Path): 文件路径
            timeout (float): 超时时间（秒）
            check_interval (float): 检查间隔（秒）
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 尝试打开文件
                with open(file_path, 'rb') as f:
                    pass
                # 如果成功打开，检查文件大小是否稳定
                size1 = file_path.stat().st_size
                time.sleep(check_interval)
                size2 = file_path.stat().st_size

                if size1 == size2 and size1 > 0:
                    logger.debug(f"文件已准备就绪: {file_path}")
                    return True
            except (IOError, OSError):
                pass

            time.sleep(check_interval)

        logger.warning(f"等待文件准备就绪超时: {file_path}")
        return False

    def _process_image(self, file_path):
        """
        处理图片：先调用视觉理解API分析图片生成提示词，再调用豆包API生成新图片

        Args:
            file_path (Path): 图片文件路径
        """
        try:
            # 获取原图尺寸
            with Image.open(file_path) as img:
                width, height = img.size
                # 根据原图尺寸选择最接近的支持尺寸
                size = self._get_best_size_match(width, height)
                logger.info(f"原图尺寸: {width}x{height}, 选择生成尺寸: {size}")

            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"generated_{timestamp}_{file_path.name}"
            output_path = self.outputs_dir / output_filename

            # 调用视觉理解API分析图片生成提示词
            # 使用prompt.py中的提示词
            instruction = get_vision_prompt("vision_no_face")
            generated_prompt = self.vision_api.image_to_prompt(file_path, instruction)

            if not generated_prompt:
                # 如果视觉理解API调用失败，使用默认提示词
                logger.warning(f"视觉理解API调用失败，使用默认提示词")
                # 使用prompt.py中的备用提示词
                prompt = get_generation_prompt("park_scene")
            else:
                # 使用prompt.py中的组合函数，将视觉分析结果和生成提示词组合
                prompt = combine_vision_and_generation(generated_prompt)
                logger.info(f"成功生成提示词: {prompt[:100]}...")  # 只记录前100个字符，避免日志过长

            # 调用豆包API生成图片，传入尺寸参数
            result = self.api.generate_image(prompt, size=size)

            if result and "data" in result and len(result["data"]) > 0:
                url = result["data"][0].get("url")
                if url:
                    # 下载生成的图片
                    success = self.api.download_image(url, output_path)

                    if success:
                        logger.info(f"图片处理成功: {file_path} -> {output_path}")

                        # 删除原始截图，添加重试机制
                        try:
                            # 确保文件存在
                            if file_path.exists():
                                # 尝试删除文件
                                os.remove(file_path)
                                # 验证文件是否已被删除
                                if not file_path.exists():
                                    logger.info(f"已成功删除原始截图: {file_path}")
                                else:
                                    logger.warning(f"文件删除失败，文件仍然存在: {file_path}")
                                    # 尝试使用Windows特定的删除命令
                                    import subprocess
                                    try:
                                        subprocess.run(["del", "/F", str(file_path)], shell=True, check=True)
                                        logger.info(f"使用系统命令删除文件成功: {file_path}")
                                    except Exception as del_err:
                                        logger.error(f"使用系统命令删除文件失败: {str(del_err)}")
                            else:
                                logger.warning(f"文件不存在，无需删除: {file_path}")
                        except Exception as del_e:
                            logger.error(f"删除文件时出错: {str(del_e)}")
                            # 将文件标记为已处理，即使删除失败
                            # 这样可以避免重复处理同一个文件
                    else:
                        logger.error(f"下载生成的图片失败: {url}")
                else:
                    logger.error(f"API响应中没有图片URL: {result}")
            else:
                logger.error(f"API调用失败或响应格式错误: {result}")

        except Exception as e:
            logger.exception(f"处理图片时出错: {str(e)}")

    def _get_best_size_match(self, width, height):
        """
        根据原图尺寸选择最接近的支持尺寸

        Args:
            width (int): 原图宽度
            height (int): 原图高度

        Returns:
            str: 最佳匹配的尺寸字符串 (例如 "1024x1024")
        """
        # 豆包API支持的尺寸列表
        supported_sizes = [
            "1024x1024",  # 1:1
            "1152x864",   # 4:3
            "864x1152",   # 3:4
            "1280x720",   # 16:9
            "720x1280",   # 9:16
            "1248x832",   # 3:2
            "832x1248",   # 2:3
            "1512x648"    # 7:3
        ]

        # 计算原图宽高比
        ratio = width / height

        # 找到最接近的尺寸
        best_size = supported_sizes[0]  # 默认为1024x1024
        min_diff = float('inf')

        for size_str in supported_sizes:
            w, h = map(int, size_str.split('x'))
            size_ratio = w / h
            diff = abs(ratio - size_ratio)

            if diff < min_diff:
                min_diff = diff
                best_size = size_str

        return best_size


class ImageMonitor:
    """图片监控类，用于启动和管理文件系统监控"""

    def __init__(self, screenshots_dir, outputs_dir):
        """
        初始化图片监控器

        Args:
            screenshots_dir (str): 截图文件夹路径
            outputs_dir (str): 输出文件夹路径
        """
        self.screenshots_dir = Path(screenshots_dir)
        self.outputs_dir = Path(outputs_dir)
        self.api = DoubaoAPI()
        self.vision_api = DoubaoVisionAPI()  # 初始化视觉理解API客户端
        self.observer = None
        self.running = False
        self.check_interval = 2  # 检查间隔（秒）
        self.is_processing = False  # 防止重复处理

        # 确保目录存在
        ensure_dir_exists(self.screenshots_dir)
        ensure_dir_exists(self.outputs_dir)

        logger.info(f"图片监控器初始化完成")

    def start(self):
        """启动监控"""
        self.running = True
        event_handler = ImageHandler(self.screenshots_dir, self.outputs_dir, self.api, self.vision_api)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.screenshots_dir), recursive=False)
        self.observer.start()

        logger.info(f"开始监控目录: {self.screenshots_dir}")

        # 处理已存在的图片
        self._process_existing_images(event_handler)

        # 设置更短的检查间隔，提高响应速度
        self.check_interval = 1  # 每秒检查一次

        # 持续检查文件夹状态
        while self.running:
            try:
                # 始终检查是否有新图片，不管是否正在处理
                self._check_for_new_images(event_handler)

                # 暂停一段时间
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"监控过程中出错: {str(e)}")
                logger.exception(e)  # 打印完整的异常堆栈
                time.sleep(self.check_interval)  # 出错后暂停一段时间再继续

    def _check_for_new_images(self, handler):
        """
        检查是否有新图片，如果有则立即处理
        即使正在处理其他图片，也会将新图片加入队列

        Args:
            handler (ImageHandler): 图片处理器实例
        """
        # 获取所有图片文件
        existing_images = [f for f in self.screenshots_dir.glob("*") if is_image_file(f)]

        # 找出未处理的图片
        unprocessed_images = [img for img in existing_images if str(img) not in handler.processed_files]

        if unprocessed_images:
            # 有新图片，开始处理
            logger.info(f"检测到{len(unprocessed_images)}张新图片，开始处理...")

            # 设置处理标志
            self.is_processing = True

            # 处理每一张未处理的图片
            for img_path in unprocessed_images:
                try:
                    logger.info(f"处理新图片: {img_path}")
                    handler._process_image(img_path)
                    handler.processed_files.add(str(img_path))
                except Exception as e:
                    logger.error(f"处理图片 {img_path} 时出错: {str(e)}")
                    # 继续处理下一张图片，不中断流程

            # 检查是否还有未处理的图片
            remaining_images = [f for f in self.screenshots_dir.glob("*") if is_image_file(f)]
            if remaining_images:
                logger.info(f"处理完成，但仍有 {len(remaining_images)} 张图片在文件夹中")

                # 检查是否有已处理但未成功删除的图片
                for img_path in remaining_images:
                    if str(img_path) in handler.processed_files:
                        logger.warning(f"发现已处理但未删除的图片，尝试强制删除: {img_path}")
                        try:
                            # 尝试强制删除
                            import subprocess
                            subprocess.run(["del", "/F", "/Q", str(img_path)], shell=True, check=True)
                            logger.info(f"强制删除文件成功: {img_path}")
                        except Exception as e:
                            logger.error(f"强制删除文件失败: {str(e)}")
            else:
                logger.info("所有图片处理完成，文件夹为空")
                self.is_processing = False
        else:
            # 文件夹中没有未处理的图片
            if self.is_processing:
                # 再次检查是否有图片，避免处理过程中新增的图片被忽略
                remaining_images = [f for f in self.screenshots_dir.glob("*") if is_image_file(f)]
                if not remaining_images:
                    logger.info("文件夹为空，等待新图片...")
                    self.is_processing = False

    def _process_existing_images(self, handler):
        """
        处理已存在的图片，并确保删除处理过的图片

        Args:
            handler (ImageHandler): 图片处理器实例
        """
        existing_images = [f for f in self.screenshots_dir.glob("*") if is_image_file(f)]

        if existing_images:
            logger.info(f"发现{len(existing_images)}张现有图片，开始处理...")
            self.is_processing = True

            for img_path in existing_images:
                try:
                    logger.info(f"处理现有图片: {img_path}")
                    handler._process_image(img_path)
                    handler.processed_files.add(str(img_path))

                    # 确保图片已被删除
                    if img_path.exists():
                        logger.warning(f"图片处理后仍然存在，尝试再次删除: {img_path}")
                        try:
                            # 尝试强制删除
                            import subprocess
                            subprocess.run(["del", "/F", "/Q", str(img_path)], shell=True, check=True)
                            if not img_path.exists():
                                logger.info(f"强制删除成功: {img_path}")
                            else:
                                logger.error(f"强制删除失败，文件仍然存在: {img_path}")
                        except Exception as e:
                            logger.error(f"强制删除出错: {str(e)}")
                except Exception as e:
                    logger.error(f"处理图片时出错: {str(e)}")
                    # 继续处理下一张图片

            # 再次检查是否有未删除的图片
            remaining_images = [f for f in self.screenshots_dir.glob("*") if is_image_file(f)]
            if remaining_images:
                logger.warning(f"处理完成后仍有 {len(remaining_images)} 张图片未被删除")
            else:
                logger.info("所有图片处理完成并已删除")

            self.is_processing = False
        else:
            logger.info("文件夹为空，等待新图片...")

    def stop(self):
        """停止监控"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("图片监控已停止")
