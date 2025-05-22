"""
Streamlit UI界面
提供Web界面展示生成结果，并允许用户创建图片生成请求，以及图床功能
"""

import os
import time
import io
import logging
from pathlib import Path
from datetime import datetime
import streamlit as st
from PIL import Image
import requests
from dotenv import load_dotenv

# 添加当前目录到Python路径，以便能够导入模块
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 现在可以导入模块了
from src.utils.helpers import ensure_dir_exists, is_image_file, load_paths_from_config
from src.utils.prompt import get_generation_prompt, USER_PROMPTS
from src.api.doubao_api import DoubaoAPI
from src.ui.components import create_masonry_gallery, image_upload_section, image_actions_section

# 加载环境变量
load_dotenv()

# 配置日志
# 使用相对路径而不是绝对路径，提高环境适应性
current_dir = Path(__file__).parent  # ui目录
src_dir = current_dir.parent  # src目录
python_dir = src_dir.parent  # Python目录

# 尝试从配置文件加载路径信息
paths_info = load_paths_from_config()

# 获取日志目录 - 优先使用环境变量，其次使用配置文件，最后使用相对路径
logs_dir = os.getenv("LOGS_DIR")

# 如果环境变量未设置，尝试使用配置文件中的路径
if not logs_dir and paths_info and 'logs_dir' in paths_info:
    logs_dir = paths_info['logs_dir']
    logger = logging.getLogger(__name__)
    logger.info(f"使用配置文件中的Logs目录: {logs_dir}")

# 如果配置文件也没有设置，使用相对路径
if not logs_dir:
    logs_dir = python_dir / "logs"  # 默认为Python目录下的logs
else:
    logs_dir = Path(logs_dir)

# 确保日志目录存在
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 获取目录配置 - 优先使用环境变量，其次使用配置文件，最后使用相对路径
screenshots_dir = os.getenv("SCREENSHOTS_DIR")
outputs_dir = os.getenv("OUTPUTS_DIR")

# 如果环境变量未设置，尝试使用配置文件中的路径
if not screenshots_dir and paths_info and 'screenshots_dir' in paths_info:
    screenshots_dir = paths_info['screenshots_dir']
    logger.info(f"使用配置文件中的Screenshots目录: {screenshots_dir}")

if not outputs_dir and paths_info and 'outputs_dir' in paths_info:
    outputs_dir = paths_info['outputs_dir']
    logger.info(f"使用配置文件中的Outputs目录: {outputs_dir}")

# 如果配置文件也没有设置，使用相对路径
if not screenshots_dir:
    SCREENSHOTS_DIR = python_dir.parent / "Screenshots"  # 默认为项目根目录下的Screenshots
    logger.info(f"使用默认的Screenshots目录: {SCREENSHOTS_DIR}")
else:
    SCREENSHOTS_DIR = Path(screenshots_dir)

if not outputs_dir:
    OUTPUTS_DIR = python_dir.parent / "Outputs"  # 默认为项目根目录下的Outputs
    logger.info(f"使用默认的Outputs目录: {OUTPUTS_DIR}")
else:
    OUTPUTS_DIR = Path(outputs_dir)

# 确保所有必要的目录都存在
directories = {
    "Screenshots": SCREENSHOTS_DIR,
    "Outputs": OUTPUTS_DIR,
    "Logs": logs_dir,
    "Temp": python_dir / "temp"  # 临时目录，用于存储上传的临时文件
}

# 检查并创建所有目录
for name, path in directories.items():
    try:
        ensure_dir_exists(path)
        logger.info(f"{name} 目录已确认存在: {path}")
    except Exception as e:
        logger.error(f"创建 {name} 目录时出错: {str(e)}")
        st.error(f"创建 {name} 目录时出错: {str(e)}")  # 在UI中显示错误

def get_image_pairs():
    """
    获取原始图片和生成图片的配对

    Returns:
        list: 包含(原始图片路径, 生成图片路径)元组的列表
    """
    # 获取所有生成的图片
    generated_images = sorted(
        [f for f in OUTPUTS_DIR.glob("*") if is_image_file(f)],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    # 提取原始图片名称
    pairs = []
    for gen_img in generated_images:
        # 从生成图片名称中提取原始图片名称
        # 假设格式为: generated_TIMESTAMP_原始文件名
        parts = gen_img.name.split("_", 2)
        if len(parts) >= 3:
            original_name = parts[2]
            original_path = SCREENSHOTS_DIR / original_name

            if original_path.exists():
                pairs.append((original_path, gen_img))
            else:
                # 如果原始图片不存在，只显示生成的图片
                pairs.append((None, gen_img))

    return pairs

def get_image_gallery():
    """获取图床中的所有图片"""
    # 获取Outputs文件夹中的所有图片
    image_files = sorted(
        [f for f in OUTPUTS_DIR.glob("*") if is_image_file(f)],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    return image_files

def create_image_request():
    """创建图片生成请求部分"""
    st.header("创建图片生成请求")

    # 创建API客户端
    api = DoubaoAPI()

    # 上传图片
    uploaded_file = st.file_uploader("上传图片", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 显示上传的图片
        image = Image.open(uploaded_file)
        st.image(image, caption="上传的图片", use_container_width=True)

        # 提示词输入 - 使用prompt.py中的提示词
        default_prompt = get_generation_prompt("default_generation")

        # 提供预设提示词选择
        prompt_options = ["自定义"] + list(USER_PROMPTS.keys())
        selected_prompt_key = st.selectbox("选择预设提示词", prompt_options, index=0)

        if selected_prompt_key == "自定义":
            prompt = st.text_area("输入提示词", value=default_prompt)
        else:
            prompt = USER_PROMPTS[selected_prompt_key]
            st.info(f"已选择预设提示词: {prompt[:100]}..." if len(prompt) > 100 else prompt)

        # 图片尺寸选择
        size_options = ["1024x1024", "864x1152", "1152x864", "1280x720", "720x1280", "832x1248", "1248x832", "1512x648"]
        size = st.selectbox("选择图片尺寸", size_options)

        # 生成参数
        col1, col2 = st.columns(2)
        with col1:
            guidance_scale = st.slider("创意自由度", 1.0, 10.0, 2.5, 0.1,
                                      help="值越小，生成图像的自由度越大；值越大，与提示词的相关性越强")
        with col2:
            seed = st.number_input("随机种子", -1, 2147483647, -1,
                                  help="-1表示随机生成种子")

        watermark = st.checkbox("添加水印", value=True)

        # 生成按钮
        if st.button("生成图片"):
            with st.spinner("正在生成图片..."):
                try:
                    # 保存上传的图片到临时文件
                    temp_dir = Path("temp")
                    temp_dir.mkdir(exist_ok=True)
                    temp_file = temp_dir / uploaded_file.name
                    with open(temp_file, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # 调用API生成图片
                    st.info(f"正在调用豆包API生成图片，使用提示词: {prompt}")
                    result = api.generate_image(
                        prompt=prompt,
                        size=size,
                        guidance_scale=guidance_scale,
                        watermark=watermark,
                        seed=seed
                    )

                    if result and "data" in result and len(result["data"]) > 0:
                        url = result["data"][0].get("url")
                        if url:
                            # 显示生成的图片
                            st.success("图片生成成功！")

                            # 下载并显示图片
                            response = requests.get(url)
                            img = Image.open(io.BytesIO(response.content))
                            st.image(img, caption="生成的图片", use_container_width=True)

                            # 保存按钮
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_filename = f"generated_{timestamp}_{uploaded_file.name}"
                            output_path = OUTPUTS_DIR / output_filename

                            if st.button("保存到Outputs文件夹"):
                                img.save(output_path)
                                st.success(f"图片已保存到: {output_path}")
                        else:
                            st.error(f"API响应中没有图片URL: {result}")
                    else:
                        st.error(f"API调用失败或响应格式错误: {result}")
                except Exception as e:
                    st.error(f"处理图片时出错: {str(e)}")

def image_gallery():
    """图床功能 - 真正的瀑布流布局"""
    st.header("图床")

    # 添加上传图片功能
    image_upload_section(OUTPUTS_DIR)

    # 获取所有图片
    images = get_image_gallery()

    if not images:
        st.info("图床中暂无图片。请先生成或上传图片。")
        return

    # 添加筛选功能
    search_col, filter_col = st.columns([3, 1])

    with search_col:
        search_term = st.text_input("搜索图片", placeholder="输入文件名关键词...")

    with filter_col:
        sort_option = st.selectbox(
            "排序方式",
            options=["最新优先", "最旧优先", "名称升序", "名称降序"],
            index=0
        )

    # 应用筛选和排序
    if search_term:
        filtered_images = [img for img in images if search_term.lower() in img.name.lower()]
    else:
        filtered_images = images.copy()

    # 排序
    if sort_option == "最新优先":
        filtered_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    elif sort_option == "最旧优先":
        filtered_images.sort(key=lambda x: x.stat().st_mtime)
    elif sort_option == "名称升序":
        filtered_images.sort(key=lambda x: x.name)
    elif sort_option == "名称降序":
        filtered_images.sort(key=lambda x: x.name, reverse=True)

    # 显示图片统计信息
    if search_term and len(filtered_images) < len(images):
        st.success(f"找到 {len(filtered_images)} 张匹配图片，共 {len(images)} 张")
    else:
        st.success(f"图床中共有 {len(filtered_images)} 张图片")

    # 分页功能 - 优化UI
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        images_per_page = st.select_slider(
            "每页显示图片数量",
            options=[12, 24, 36, 48, 60],
            value=24,
            help="选择合适的数量以获得最佳性能"
        )

    total_pages = max(1, (len(filtered_images) + images_per_page - 1) // images_per_page)

    with col2:
        page = st.number_input("页码", min_value=1, max_value=total_pages, value=1)

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)  # 添加一点垂直间距
        prev_page = st.button("上一页", disabled=(page <= 1))

    if prev_page and page > 1:
        page -= 1
        st.session_state.gallery_page = page
        st.rerun()

    _, next_col2 = st.columns([3, 1])
    with next_col2:
        next_page = st.button("下一页", disabled=(page >= total_pages))

    if next_page and page < total_pages:
        page += 1
        st.session_state.gallery_page = page
        st.rerun()

    # 计算当前页的图片
    start_idx = (page - 1) * images_per_page
    end_idx = min(start_idx + images_per_page, len(filtered_images))

    # 只加载当前页的图片
    page_images = filtered_images[start_idx:end_idx]

    # 显示分页信息
    st.write(f"显示第 {start_idx+1}-{end_idx} 张图片，共 {len(filtered_images)} 张")

    # 添加性能提示
    with st.expander("使用技巧", expanded=False):
        st.info("""
        ### 图床使用技巧

        - **浏览图片**: 图片使用高效的延迟加载技术，只有在滚动到可见区域时才会加载
        - **性能优化**: 如果加载速度较慢，可以减少每页显示的图片数量
        - **图片操作**: 点击任意图片可以快速选择并打开操作面板
        - **搜索功能**: 使用搜索框可以快速找到特定图片
        - **排序选项**: 可以按时间或名称排序浏览图片
        """)

    # 创建真正的瀑布流布局
    create_masonry_gallery(page_images)

    # 使用查询参数而不是session_state来处理图片选择
    query_params = st.query_params
    selected_image_param = query_params.get("selected_image", ["0"])[0]
    try:
        selected_image_index = int(selected_image_param)
    except ValueError:
        selected_image_index = 0

    # 图片操作区域 - 改进UI
    with st.expander("图片操作", expanded=False):
        if page_images:
            # 使用查询参数中的索引，或者让用户手动选择
            col1, col2 = st.columns([3, 1])

            with col1:
                # 确保索引在有效范围内
                valid_index = min(selected_image_index, len(page_images)-1) if len(page_images) > 0 else 0

                selected_idx = st.selectbox(
                    "选择图片",
                    range(len(page_images)),
                    index=valid_index,
                    format_func=lambda i: page_images[i].name if i < len(page_images) else ""
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("刷新选择", help="如果点击图片后没有自动更新选择，请点击此按钮"):
                    st.rerun()

            # 显示图片操作界面
            image_actions_section(page_images, selected_idx)
        else:
            st.info("当前页面没有图片可供操作")

    # 添加批量操作功能
    with st.expander("批量操作", expanded=False):
        st.warning("⚠️ 批量操作会影响所有筛选后的图片，请谨慎使用")

        if st.button("刷新图床缓存", help="清除图床缓存并重新加载所有图片"):
            st.cache_data.clear()
            st.rerun()

        if st.button("导出图片列表", help="导出当前筛选的图片列表为文本"):
            if filtered_images:
                image_list = "\n".join([f"{i+1}. {img.name}" for i, img in enumerate(filtered_images)])
                st.download_button(
                    label="下载图片列表",
                    data=image_list,
                    file_name="image_list.txt",
                    mime="text/plain"
                )
            else:
                st.info("没有图片可供导出")

def main():
    """Streamlit应用主函数"""
    st.set_page_config(
        page_title="Unity截图 + 豆包AI生图系统",
        page_icon="🖼️",
        layout="wide"
    )

    st.title("Unity截图 + 豆包AI生图系统")

    # 侧边栏配置
    st.sidebar.header("配置")
    auto_refresh = st.sidebar.checkbox("自动刷新", value=True)
    refresh_interval = st.sidebar.slider("刷新间隔（秒）", 1, 60, 5)

    # 显示目录信息
    st.sidebar.subheader("目录信息")
    st.sidebar.text(f"截图目录: {SCREENSHOTS_DIR}")
    st.sidebar.text(f"输出目录: {OUTPUTS_DIR}")

    # 手动刷新按钮
    if st.sidebar.button("手动刷新"):
        st.rerun()

    # 添加选项卡 - 调整顺序，将图床放在第一位
    tab1, tab2, tab3 = st.tabs(["图床", "创建请求", "历史图片"])

    # 图床选项卡（现在是第一个选项卡）
    with tab1:
        image_gallery()

    # 创建请求选项卡
    with tab2:
        create_image_request()

    # 历史图片选项卡（现在是第三个选项卡）
    with tab3:
        # 获取图片对
        image_pairs = get_image_pairs()

        # 获取截图文件夹状态
        screenshots = [f for f in SCREENSHOTS_DIR.glob("*") if is_image_file(f)]

        # 显示监控状态
        st.subheader("监控状态")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("生成图片数量", len(image_pairs))

        with col2:
            st.metric("待处理图片数量", len(screenshots))

        if len(screenshots) > 0:
            st.info(f"截图文件夹中有 {len(screenshots)} 张图片等待处理。系统将自动处理这些图片并生成AI版本。")
        else:
            st.success("截图文件夹为空。当有新截图时，系统将自动处理。")

        st.markdown("---")

        # 显示生成的图片
        st.subheader("生成历史")
        if not image_pairs:
            st.info("暂无生成图片。请在Unity中创建截图，系统将自动处理并在此显示结果。")
        else:
            st.success(f"找到 {len(image_pairs)} 张生成图片")

            # 显示图片对
            for i, (original, generated) in enumerate(image_pairs):
                col1, col2 = st.columns(2)

                # 显示生成时间
                gen_time = datetime.fromtimestamp(generated.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                st.subheader(f"图片 {i+1} - 生成时间: {gen_time}")

                with col1:
                    if original:
                        st.image(str(original), caption=f"原始截图: {original.name}", use_container_width=True)
                    else:
                        st.info("原始截图已被处理并删除")

                with col2:
                    st.image(str(generated), caption=f"AI生成图片: {generated.name}", use_container_width=True)

                st.markdown("---")

    # 自动刷新
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
