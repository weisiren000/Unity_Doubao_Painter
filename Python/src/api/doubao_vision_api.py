"""
豆包视觉理解API调用模块
负责与豆包视觉理解API进行交互，将图片转化为提示词
"""

import os
import json
import base64
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

# 导入提示词模块
from src.utils.prompt import SYSTEM_PROMPTS

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

class DoubaoVisionAPI:
    """豆包视觉理解API客户端类"""

    def __init__(self):
        """初始化豆包视觉理解API客户端"""
        self.api_key = os.getenv("DOUBAO_API_KEY")
        self.api_url = os.getenv("DOUBAO_VISION_API_URL", "https://ark.cn-beijing.volces.com/api/v3/chat/completions")
        self.model = os.getenv("DOUBAO_VISION_MODEL", "doubao-1.5-thinking-vision-pro-250428")

        if not self.api_key:
            raise ValueError("缺少必要的API配置，请检查.env文件")

        logger.info(f"豆包视觉理解API客户端初始化完成，使用模型: {self.model}")

    def image_to_prompt(self, image_path, instruction=None):
        """
        将图片转化为提示词

        Args:
            image_path (str): 图片路径
            instruction (str, optional): 额外的指导说明，例如"生成一个详细的图片描述"

        Returns:
            str: 生成的提示词
        """
        # 将图片转换为Base64编码，并获取正确的格式
        image_base64, img_format = self._encode_image(image_path)

        # 如果没有提供指导说明，使用默认值
        if not instruction:
            instruction = "请分析这张图片，生成一个详细的描述，可以用于AI图像生成。描述应该包括图片中的主要内容、场景、风格、色彩和氛围。"

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 构建请求体，根据豆包API文档调整格式
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPTS["vision_system"]  # 使用prompt.py中的系统提示词
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": instruction
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{img_format};base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "stream": False,
            "max_tokens": 1000
        }

        logger.info(f"发送图片分析请求: {Path(image_path).name}")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)

            # 记录请求和响应的详细信息，以便调试
            logger.debug(f"请求URL: {self.api_url}")
            logger.debug(f"请求头: {headers}")
            logger.debug(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应内容: {response.text[:500]}...")  # 只记录前500个字符

            response.raise_for_status()  # 如果响应状态码不是200，抛出异常

            result = response.json()

            # 从响应中提取生成的提示词
            if "choices" in result and len(result["choices"]) > 0:
                prompt = result["choices"][0]["message"]["content"]
                logger.info(f"图片分析成功，生成提示词长度: {len(prompt)}")

                # 记录token使用情况
                if "usage" in result:
                    usage = result["usage"]
                    logger.info(f"Token使用情况: 输入={usage.get('prompt_tokens', 0)}, "
                               f"输出={usage.get('completion_tokens', 0)}, "
                               f"总计={usage.get('total_tokens', 0)}")

                return prompt
            else:
                logger.error(f"API响应格式错误: {result}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"错误响应: {e.response.text}")
            return None
        except json.JSONDecodeError:
            logger.error(f"解析API响应失败: {response.text}")
            return None
        except Exception as e:
            logger.error(f"图片分析过程中出错: {str(e)}")
            return None

    def _encode_image(self, image_path):
        """
        将图片编码为Base64字符串，并确保格式正确

        Args:
            image_path (str): 图片路径

        Returns:
            str: Base64编码的图片
            str: 图片格式（jpeg, png等）
        """
        try:
            # 使用PIL打开图片，确保格式正确
            from PIL import Image
            import io

            # 打开图片
            with Image.open(image_path) as img:
                # 确定图片格式
                img_format = img.format.lower() if img.format else "jpeg"

                # 转换为RGB模式（如果是RGBA或其他模式）
                if img.mode != "RGB" and img_format != "png":
                    img = img.convert("RGB")

                # 将图片保存到内存缓冲区
                buffer = io.BytesIO()
                img.save(buffer, format=img_format)
                buffer.seek(0)

                # 编码为Base64
                return base64.b64encode(buffer.read()).decode('utf-8'), img_format
        except Exception as e:
            logger.error(f"图片编码失败: {str(e)}")
            raise


# 测试代码
if __name__ == "__main__":
    # 配置日志输出到控制台
    logging.basicConfig(level=logging.INFO)

    # 创建API客户端
    api = DoubaoVisionAPI()

    # 测试图片分析
    test_image = "test_image.jpg"  # 替换为实际的测试图片路径
    if os.path.exists(test_image):
        prompt = api.image_to_prompt(test_image)
        print(f"生成的提示词: {prompt}")
    else:
        print(f"测试图片不存在: {test_image}")
