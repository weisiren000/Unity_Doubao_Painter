"""
主程序入口
协调各模块工作
"""

import os
import sys
import logging
import threading
import subprocess
from pathlib import Path
from dotenv import load_dotenv

from src.monitor.image_monitor import ImageMonitor
from src.utils.helpers import ensure_dir_exists, load_paths_from_config

# 加载环境变量
load_dotenv()

# 配置日志
def setup_logging():
    """设置日志系统"""
    # 使用相对路径而不是绝对路径，提高环境适应性
    current_dir = Path(__file__).parent  # Python目录

    # 获取日志目录 - 优先使用环境变量，否则使用相对路径
    logs_dir = os.getenv("LOGS_DIR")
    if logs_dir:
        logs_dir = Path(logs_dir)
    else:
        # 默认使用相对路径 ./logs
        logs_dir = current_dir / "logs"

    ensure_dir_exists(logs_dir)

    log_file = os.path.join(logs_dir, "app.log")

    logging.basicConfig(
        level=logging.DEBUG,  # 修改为DEBUG级别，以便查看更详细的日志
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # 设置第三方库的日志级别为WARNING，避免过多的日志输出
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成")
    return logger

def ensure_directories():
    """确保必要的目录结构存在"""
    # 尝试从配置文件加载路径信息
    paths_info = load_paths_from_config()

    # 使用相对路径而不是绝对路径，提高环境适应性
    current_dir = Path(__file__).parent  # Python目录

    # 获取目录配置 - 优先使用环境变量，其次使用配置文件，最后使用相对路径
    screenshots_dir = os.getenv("SCREENSHOTS_DIR")
    outputs_dir = os.getenv("OUTPUTS_DIR")
    logs_dir = os.getenv("LOGS_DIR")

    # 如果环境变量未设置，尝试使用配置文件中的路径
    if not screenshots_dir and paths_info and 'screenshots_dir' in paths_info:
        screenshots_dir = paths_info['screenshots_dir']
        logger.info(f"使用配置文件中的Screenshots目录: {screenshots_dir}")

    if not outputs_dir and paths_info and 'outputs_dir' in paths_info:
        outputs_dir = paths_info['outputs_dir']
        logger.info(f"使用配置文件中的Outputs目录: {outputs_dir}")

    if not logs_dir and paths_info and 'logs_dir' in paths_info:
        logs_dir = paths_info['logs_dir']
        logger.info(f"使用配置文件中的Logs目录: {logs_dir}")

    # 如果配置文件也没有设置，使用相对路径
    if not screenshots_dir:
        screenshots_dir = current_dir.parent / "Screenshots"  # 默认为项目根目录下的Screenshots
        logger.info(f"使用默认的Screenshots目录: {screenshots_dir}")
    else:
        screenshots_dir = Path(screenshots_dir)

    if not outputs_dir:
        outputs_dir = current_dir.parent / "Outputs"  # 默认为项目根目录下的Outputs
        logger.info(f"使用默认的Outputs目录: {outputs_dir}")
    else:
        outputs_dir = Path(outputs_dir)

    if not logs_dir:
        logs_dir = current_dir / "logs"  # 默认为Python目录下的logs
        logger.info(f"使用默认的Logs目录: {logs_dir}")
    else:
        logs_dir = Path(logs_dir)

    # 确保所有必要的目录都存在
    directories = {
        "Screenshots": screenshots_dir,
        "Outputs": outputs_dir,
        "Logs": logs_dir,
        "Temp": current_dir / "temp"  # 临时目录，用于存储上传的临时文件
    }

    # 检查并创建所有目录
    for name, path in directories.items():
        try:
            ensure_dir_exists(path)
            logger.info(f"{name} 目录已确认存在: {path}")
        except Exception as e:
            logger.error(f"创建 {name} 目录时出错: {str(e)}")

    return screenshots_dir, outputs_dir

def start_streamlit():
    """启动Streamlit UI界面"""
    streamlit_script = Path(__file__).parent / "src" / "ui" / "streamlit_app.py"

    # 使用subprocess启动Streamlit，使用127.0.0.1作为地址以避免网络问题
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(streamlit_script),
        "--server.port=8505",  # 使用不同的端口
        "--server.address=127.0.0.1"
    ]

    # 直接显示输出，不捕获，这样可以看到错误信息
    process = subprocess.Popen(
        cmd,
        # 不捕获输出，让它直接显示在控制台
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        text=True
    )

    logger.info(f"Streamlit UI已启动，访问地址: http://localhost:8501")
    return process

def main():
    """主函数"""
    # 确保目录存在
    screenshots_dir, outputs_dir = ensure_directories()

    # 创建并启动图片监控器
    monitor = ImageMonitor(screenshots_dir, outputs_dir)
    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()

    # 启动Streamlit UI
    streamlit_process = start_streamlit()

    try:
        # 等待Streamlit进程结束
        streamlit_process.wait()
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止程序...")
    finally:
        # 停止监控
        monitor.stop()

        # 确保Streamlit进程结束
        if streamlit_process.poll() is None:
            streamlit_process.terminate()
            streamlit_process.wait()

        logger.info("程序已停止")

if __name__ == "__main__":
    # 设置日志
    logger = setup_logging()

    # 启动主程序
    logger.info("启动Unity截图 + 豆包AI生图系统")
    main()