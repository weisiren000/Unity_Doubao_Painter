"""
UI组件模块
包含可重用的UI组件
"""

import os
import io
import base64
import streamlit as st
from pathlib import Path
from PIL import Image
from datetime import datetime

def get_image_base64(image_path):
    """将图片转换为base64编码"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def get_image_dimensions(img_path):
    """获取图片的宽高比"""
    try:
        with Image.open(img_path) as img:
            width, height = img.size
            return width / height
    except Exception:
        return 1.0  # 默认为正方形

def create_masonry_gallery(images):
    """
    创建瀑布流布局图片画廊 - 使用原生Streamlit组件

    Args:
        images (list): 图片路径列表
    """
    if not images:
        st.info("暂无图片")
        return

    # 使用CSS美化图片网格
    st.markdown("""
    <style>
    /* 图片网格样式 */
    .gallery-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        justify-content: center;
    }

    .gallery-item {
        flex: 0 0 calc(33.333% - 16px);
        max-width: calc(33.333% - 16px);
        position: relative;
        overflow: hidden;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .gallery-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }

    .gallery-item img {
        width: 100%;
        height: auto;
        display: block;
        transition: transform 0.5s ease;
    }

    .gallery-item:hover img {
        transform: scale(1.05);
    }

    .gallery-item .caption {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(to top, rgba(0,0,0,0.8), rgba(0,0,0,0));
        color: white;
        padding: 16px;
        font-size: 14px;
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .gallery-item:hover .caption {
        opacity: 1;
    }

    /* 响应式布局 */
    @media (max-width: 1200px) {
        .gallery-item {
            flex: 0 0 calc(50% - 16px);
            max-width: calc(50% - 16px);
        }
    }

    @media (max-width: 768px) {
        .gallery-item {
            flex: 0 0 100%;
            max-width: 100%;
        }
    }

    /* 选中状态 */
    .gallery-item.selected {
        border: 3px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    # 使用Streamlit的原生列布局创建网格
    # 每行3列，创建瀑布流效果
    num_cols = 3
    rows = [st.columns(num_cols) for _ in range((len(images) + num_cols - 1) // num_cols)]

    # 不使用session_state，避免ScriptRunContext警告

    # 创建图片网格
    for i, img_path in enumerate(images):
        col_idx = i % num_cols
        row_idx = i // num_cols

        with rows[row_idx][col_idx]:
            # 获取图片名称
            img_name = img_path.name
            display_name = img_name.split('_')[-1] if '_' in img_name else img_name

            # 创建缩略图
            try:
                # 打开图片并创建缩略图
                with Image.open(img_path) as img:
                    # 保持原始宽高比，但限制最大尺寸
                    img.thumbnail((300, 300), Image.LANCZOS)

                    # 显示图片
                    st.image(
                        img,
                        caption=display_name,
                        use_container_width=True
                    )

                    # 添加点击功能
                    is_selected = st.button(
                        f"选择 #{i+1}",
                        key=f"select_img_{i}",
                        help=f"选择图片: {display_name}"
                    )

                    # 如果选择了图片，返回索引
                    if is_selected:
                        # 使用查询参数而不是session_state
                        st.query_params["selected_image"] = str(i)
                        st.rerun()
            except Exception as e:
                st.error(f"加载图片 {img_name} 时出错: {str(e)}")

    return True

def image_upload_section(output_dir):
    """
    图片上传组件

    Args:
        output_dir (Path): 输出目录
    """
    with st.expander("上传图片到图床", expanded=False):
        uploaded_files = st.file_uploader("选择图片文件", type=["jpg", "jpeg", "png", "gif", "bmp"], accept_multiple_files=True)

        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    # 生成唯一文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # 使用文件名直接构建新文件名，不需要单独提取扩展名
                    new_filename = f"uploaded_{timestamp}_{uploaded_file.name}"
                    save_path = output_dir / new_filename

                    # 保存上传的图片
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    st.success(f"成功上传图片: {new_filename}")
                except Exception as e:
                    st.error(f"上传图片失败: {str(e)}")

            # 上传完成后刷新页面
            if st.button("完成上传，刷新图床"):
                st.rerun()

def image_actions_section(images, selected_idx):
    """
    增强的图片操作组件

    Args:
        images (list): 图片路径列表
        selected_idx (int): 选中的图片索引
    """
    if not images or selected_idx is None or selected_idx >= len(images):
        return

    selected_img = images[selected_idx]

    # 获取图片信息
    try:
        with Image.open(selected_img) as img:
            width, height = img.size
            format_name = img.format or "未知"
            mode = img.mode
            file_size = selected_img.stat().st_size / 1024  # KB
    except Exception as e:
        width, height = 0, 0
        format_name = "无法读取"
        mode = "未知"
        file_size = 0
        st.error(f"读取图片信息失败: {str(e)}")

    # 显示选中的图片
    st.image(str(selected_img), caption=selected_img.name, use_container_width=True)

    # 显示图片详细信息
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.metric("尺寸", f"{width}×{height}px")
    with info_col2:
        st.metric("格式", f"{format_name} ({mode})")
    with info_col3:
        st.metric("文件大小", f"{file_size:.1f} KB")

    # 创建时间信息
    creation_time = datetime.fromtimestamp(selected_img.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"创建时间: {creation_time}")

    # 操作按钮分组
    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        # 复制图片链接
        if st.button("📋 复制图片链接", help="生成并复制图片的Base64数据URL"):
            try:
                img_base64 = get_image_base64(selected_img)
                data_url = f"data:image/{selected_img.suffix[1:]};base64,{img_base64}"

                # 显示不同格式的链接选项
                link_type = st.radio(
                    "选择链接格式:",
                    ["HTML图片标签", "Markdown格式", "纯Base64 URL"],
                    horizontal=True
                )

                if link_type == "HTML图片标签":
                    code = f'<img src="{data_url}" alt="{selected_img.name}" width="{width}" height="{height}">'
                elif link_type == "Markdown格式":
                    code = f'![{selected_img.name}]({data_url})'
                else:
                    code = data_url

                st.code(code, language="html")
                st.success("已生成图片链接，可以复制使用")
            except Exception as e:
                st.error(f"生成链接失败: {str(e)}")

    with action_col2:
        # 下载图片
        with open(selected_img, "rb") as file:
            file_content = file.read()

        st.download_button(
            label="💾 下载图片",
            data=file_content,
            file_name=selected_img.name,
            mime=f"image/{selected_img.suffix[1:]}",
            help="将图片下载到本地"
        )

    with action_col3:
        # 删除图片
        if st.button("🗑️ 删除图片", help="从图床中永久删除此图片"):
            confirm = st.checkbox("确认删除", value=False)
            if confirm:
                try:
                    os.remove(selected_img)
                    st.success(f"已删除图片: {selected_img.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"删除图片失败: {str(e)}")
            else:
                st.warning("请先确认删除操作")

    # 添加图片预览增强功能
    st.markdown("---")
    preview_col1, preview_col2 = st.columns(2)

    with preview_col1:
        if st.button("🔍 查看原始大小", help="在新窗口中查看原始大小的图片"):
            # 创建一个临时HTML文件用于查看原图
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{selected_img.name} - 原始大小预览</title>
                <style>
                    body {{ margin: 0; padding: 20px; background: #f0f0f0; text-align: center; }}
                    img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
                    h3 {{ font-family: sans-serif; color: #333; }}
                </style>
            </head>
            <body>
                <h3>{selected_img.name} ({width}×{height}px)</h3>
                <img src="data:image/{selected_img.suffix[1:]};base64,{get_image_base64(selected_img)}" alt="{selected_img.name}">
            </body>
            </html>
            """
            st.components.v1.html(html_content, height=500, scrolling=True)

    with preview_col2:
        # 图片信息显示
        st.text_area(
            "图片路径",
            value=str(selected_img.absolute()),
            height=100,
            help="图片在系统中的完整路径"
        )
