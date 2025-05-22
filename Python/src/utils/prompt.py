"""
提示词模块
集中存放项目中使用的各种提示词，便于统一管理和修改
"""

import logging
from typing import Dict, List, Optional, Union

# 配置日志
logger = logging.getLogger(__name__)

# 系统提示词
SYSTEM_PROMPTS = {
    # 视觉理解API的系统提示词
    "vision_system": "你是一个专业的图像分析助手，擅长将图片转化为详细的描述，用于AI图像生成。",
    
    # 图生图API的系统提示词
    "image_generation_system": "你是一个专业的图像生成助手，擅长根据提示词生成高质量的图像。"
}

# 用户提示词
USER_PROMPTS = {
    # 视觉理解API的用户提示词 - 基础版
    "vision_basic": "请分析这张图片，生成一个详细的描述，用于AI图像生成。描述应该包括图片中的主要内容、场景、风格、色彩和氛围。",
    
    # 视觉理解API的用户提示词 - 不包含人脸特征版
    "vision_no_face": "请分析这张图片，生成一个详细的描述，用于AI图像生成。描述应该包括图片中的主要内容、场景、风格、色彩和氛围，但不要包含任何人物的面部特征描述。",
    
    # 视觉理解API的用户提示词 - 艺术风格版
    "vision_artistic": "请分析这张图片，生成一个详细的艺术风格描述，用于AI图像生成。描述应该包括图片中的主要内容、场景、艺术风格、色彩和氛围，特别强调艺术表现手法和美学特点。",
    
    # 视觉理解API的用户提示词 - 风景版
    "vision_landscape": "请分析这张风景图片，生成一个详细的描述，用于AI图像生成。描述应该包括风景的主要元素、地理特征、季节、天气、光线条件、色彩和氛围。",
    
    # 视觉理解API的用户提示词 - 物品版
    "vision_object": "请分析这张物品图片，生成一个详细的描述，用于AI图像生成。描述应该包括物品的外观、材质、颜色、形状、功能和风格特点。",
    
    # 图生图默认提示词
    "default_generation": "基于这张图片创建一个艺术化的版本，增强色彩和细节",
    
    # 图生图保持构图提示词
    "keep_composition": "基于这张图片创建一个艺术化的版本，保持原始构图和主要元素位置，但提升画面的艺术性和美感。",
    
    # 图生图公园场景提示词
    "park_scene": "基于这张图片创建一个公园的图像，要求构图不能改变，主体物的位置类似，设施类型也不改变",
    
    # 图生图自然风景提示词
    "nature_scene": "基于这张图片创建一个自然风景图像，增强自然元素，使用更丰富的色彩和光影效果，保持原始构图",
    
    # 图生图城市场景提示词
    "city_scene": "基于这张图片创建一个城市场景图像，增强建筑细节和城市氛围，使用更丰富的色彩和光影效果，保持原始构图",
    
    # 图生图室内场景提示词
    "indoor_scene": "基于这张图片创建一个室内场景图像，增强室内装饰细节和氛围，使用更丰富的色彩和光影效果，保持原始构图"
}

# 提示词组合模板
PROMPT_TEMPLATES = {
    # 视觉分析后生成图片的组合提示词模板
    "vision_to_image": "{vision_result} 请保持原始图片的构图和主要元素位置，但可以提升画面的艺术性和美感。",
    
    # 视觉分析失败后的备用提示词模板
    "vision_fallback": "基于这张图片创建一个{scene_type}的图像，要求构图不能改变，主体物的位置类似，{additional_instructions}",
    
    # 自定义风格的提示词模板
    "custom_style": "{base_description}，使用{style}风格，{additional_instructions}"
}

def get_vision_prompt(prompt_type: str = "vision_basic") -> str:
    """
    获取视觉理解API的提示词
    
    Args:
        prompt_type (str): 提示词类型，可选值包括 "vision_basic", "vision_no_face", 
                          "vision_artistic", "vision_landscape", "vision_object"
    
    Returns:
        str: 对应类型的提示词
    """
    if prompt_type in USER_PROMPTS:
        return USER_PROMPTS[prompt_type]
    else:
        logger.warning(f"未找到提示词类型: {prompt_type}，使用基础提示词")
        return USER_PROMPTS["vision_basic"]

def get_generation_prompt(prompt_type: str = "default_generation") -> str:
    """
    获取图像生成API的提示词
    
    Args:
        prompt_type (str): 提示词类型，可选值包括 "default_generation", "keep_composition", 
                          "park_scene", "nature_scene", "city_scene", "indoor_scene"
    
    Returns:
        str: 对应类型的提示词
    """
    if prompt_type in USER_PROMPTS:
        return USER_PROMPTS[prompt_type]
    else:
        logger.warning(f"未找到提示词类型: {prompt_type}，使用默认提示词")
        return USER_PROMPTS["default_generation"]

def combine_vision_and_generation(vision_result: str, 
                                 scene_type: str = "公园", 
                                 additional_instructions: str = "设施类型也不改变") -> str:
    """
    组合视觉分析结果和图像生成提示词
    
    Args:
        vision_result (str): 视觉分析的结果
        scene_type (str): 场景类型，用于视觉分析失败时的备用提示词
        additional_instructions (str): 额外的指导说明
    
    Returns:
        str: 组合后的提示词
    """
    if vision_result:
        return PROMPT_TEMPLATES["vision_to_image"].format(vision_result=vision_result)
    else:
        return PROMPT_TEMPLATES["vision_fallback"].format(
            scene_type=scene_type,
            additional_instructions=additional_instructions
        )

def create_custom_prompt(base_description: str, 
                        style: str = "写实", 
                        additional_instructions: str = "") -> str:
    """
    创建自定义风格的提示词
    
    Args:
        base_description (str): 基础描述
        style (str): 风格，如"写实"、"油画"、"水彩"等
        additional_instructions (str): 额外的指导说明
    
    Returns:
        str: 自定义提示词
    """
    return PROMPT_TEMPLATES["custom_style"].format(
        base_description=base_description,
        style=style,
        additional_instructions=additional_instructions
    )

# 测试代码
if __name__ == "__main__":
    # 配置日志输出到控制台
    logging.basicConfig(level=logging.INFO)
    
    # 测试获取提示词
    print("视觉理解基础提示词:", get_vision_prompt())
    print("视觉理解无人脸提示词:", get_vision_prompt("vision_no_face"))
    print("图像生成默认提示词:", get_generation_prompt())
    print("图像生成保持构图提示词:", get_generation_prompt("keep_composition"))
    
    # 测试组合提示词
    vision_result = "一张城市公园的照片，有绿色的草地、树木和一条小径。"
    combined = combine_vision_and_generation(vision_result)
    print("组合提示词:", combined)
    
    # 测试视觉分析失败的情况
    fallback = combine_vision_and_generation(None, "城市", "保持建筑风格")
    print("备用提示词:", fallback)
    
    # 测试自定义提示词
    custom = create_custom_prompt("一座山脉和湖泊", "油画", "使用明亮的色彩")
    print("自定义提示词:", custom)
