"""
豆包API调用模块
负责与豆包API进行交互，发送图片生成请求并获取结果
"""

import os
import json
import logging
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

class DoubaoAPI:
    """豆包API客户端类"""

    def __init__(self):
        """初始化豆包API客户端"""
        self.api_key = os.getenv("DOUBAO_API_KEY")
        self.api_url = os.getenv("DOUBAO_API_URL")
        self.model = os.getenv("DOUBAO_MODEL")

        if not self.api_key or not self.api_url or not self.model:
            raise ValueError("缺少必要的API配置，请检查.env文件")

        logger.info(f"豆包API客户端初始化完成，使用模型: {self.model}")

    def generate_image(self, prompt, size="1024x1024", response_format="url",
                      guidance_scale=2.5, watermark=True, seed=-1, n=1):
        """
        调用豆包API生成图片

        Args:
            prompt (str): 用于生成图像的提示词
            size (str): 生成图像的尺寸，例如"1024x1024"
            response_format (str): 返回格式，"url"或"b64_json"
            guidance_scale (float): 生成图像与提示词的相关性强度，范围[1, 10]
            watermark (bool): 是否添加水印
            seed (int): 随机数种子，-1表示随机
            n (int): 生成图片数量

        Returns:
            dict: 包含生成图片URL或base64数据的响应
        """
        # 验证尺寸参数
        valid_sizes = [
            "1024x1024",  # 1:1
            "1152x864",   # 4:3
            "864x1152",   # 3:4
            "1280x720",   # 16:9
            "720x1280",   # 9:16
            "1248x832",   # 3:2
            "832x1248",   # 2:3
            "1512x648"    # 7:3
        ]

        if size not in valid_sizes:
            logger.warning(f"不支持的尺寸: {size}，将使用默认尺寸1024x1024")
            size = "1024x1024"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "response_format": response_format,
            "size": size,
            "guidance_scale": guidance_scale,
            "watermark": watermark,
            "seed": seed,
            "n": n
        }

        logger.info(f"发送图片生成请求: prompt='{prompt}', size={size}")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常

            result = response.json()
            logger.info(f"图片生成成功: {result.get('created')}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"错误响应: {e.response.text}")
            raise
        except json.JSONDecodeError:
            logger.error(f"解析API响应失败: {response.text}")
            raise

    def download_image(self, url, save_path):
        """
        从URL下载图片并保存到指定路径

        Args:
            url (str): 图片URL
            save_path (str): 保存路径

        Returns:
            bool: 下载是否成功
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"图片下载成功: {save_path}")
            return True

        except Exception as e:
            logger.error(f"图片下载失败: {str(e)}")
            return False


# 测试代码
if __name__ == "__main__":
    # 配置日志输出到控制台
    logging.basicConfig(level=logging.INFO)

    # 创建API客户端
    api = DoubaoAPI()

    # 测试生成图片
    prompt = "一只可爱的猫咪在阳光下玩耍"
    result = api.generate_image(prompt)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 如果生成成功，下载图片
    if result and "data" in result and len(result["data"]) > 0:
        url = result["data"][0].get("url")
        if url:
            api.download_image(url, "test_output.jpg")
