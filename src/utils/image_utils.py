"""
图像处理工具
"""

from typing import Union, Tuple
from PIL import Image
import numpy as np
import requests
from io import BytesIO
from pathlib import Path


def load_image(image_source: Union[str, Path, Image.Image, np.ndarray]) -> Image.Image:
    """
    加载图像（支持多种输入格式）

    Args:
        image_source: 图像源（文件路径、URL、PIL Image 或 numpy 数组）

    Returns:
        PIL Image 对象
    """
    if isinstance(image_source, Image.Image):
        return image_source

    if isinstance(image_source, np.ndarray):
        return Image.fromarray(image_source)

    if isinstance(image_source, (str, Path)):
        image_source = str(image_source)

        # URL
        if image_source.startswith(('http://', 'https://')):
            response = requests.get(image_source, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))

        # 本地文件
        image_path = Path(image_source)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_source}")

        return Image.open(image_path)

    raise TypeError(f"Unsupported image source type: {type(image_source)}")


def resize_image(
    image: Image.Image,
    target_size: Union[int, Tuple[int, int]],
    keep_aspect_ratio: bool = True
) -> Image.Image:
    """
    调整图像大小

    Args:
        image: PIL Image
        target_size: 目标大小（单个整数或 (width, height) 元组）
        keep_aspect_ratio: 是否保持宽高比

    Returns:
        调整后的图像
    """
    if isinstance(target_size, int):
        target_size = (target_size, target_size)

    if not keep_aspect_ratio:
        return image.resize(target_size, Image.LANCZOS)

    # 保持宽高比
    image.thumbnail(target_size, Image.LANCZOS)
    return image


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """
    转换图像为 RGB 格式

    Args:
        image: PIL Image

    Returns:
        RGB 格式图像
    """
    if image.mode != 'RGB':
        return image.convert('RGB')
    return image


def image_to_numpy(image: Image.Image) -> np.ndarray:
    """
    PIL Image 转 numpy 数组

    Args:
        image: PIL Image

    Returns:
        numpy 数组
    """
    return np.array(image)


def numpy_to_image(array: np.ndarray) -> Image.Image:
    """
    numpy 数组转 PIL Image

    Args:
        array: numpy 数组

    Returns:
        PIL Image
    """
    return Image.fromarray(array)


def normalize_image(
    image: np.ndarray,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
) -> np.ndarray:
    """
    归一化图像（ImageNet 标准）

    Args:
        image: numpy 数组 (H, W, C)
        mean: 均值
        std: 标准差

    Returns:
        归一化后的图像
    """
    image = image.astype(np.float32) / 255.0
    image = (image - mean) / std
    return image


def denormalize_image(
    image: np.ndarray,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
) -> np.ndarray:
    """
    反归一化图像

    Args:
        image: 归一化的 numpy 数组
        mean: 均值
        std: 标准差

    Returns:
        原始图像
    """
    image = image * std + mean
    image = (image * 255.0).astype(np.uint8)
    return image


def crop_image(
    image: Image.Image,
    bbox: Tuple[int, int, int, int]
) -> Image.Image:
    """
    裁剪图像

    Args:
        image: PIL Image
        bbox: 边界框 (x1, y1, x2, y2)

    Returns:
        裁剪后的图像
    """
    return image.crop(bbox)


def pad_image(
    image: Image.Image,
    target_size: Tuple[int, int],
    fill_color: Union[int, Tuple[int, int, int]] = 0
) -> Image.Image:
    """
    填充图像到目标大小

    Args:
        image: PIL Image
        target_size: 目标大小 (width, height)
        fill_color: 填充颜色

    Returns:
        填充后的图像
    """
    width, height = image.size
    target_width, target_height = target_size

    if width == target_width and height == target_height:
        return image

    # 创建新图像
    new_image = Image.new('RGB', target_size, fill_color)

    # 居中粘贴
    paste_x = (target_width - width) // 2
    paste_y = (target_height - height) // 2
    new_image.paste(image, (paste_x, paste_y))

    return new_image


def calculate_iou(
    box1: Tuple[float, float, float, float],
    box2: Tuple[float, float, float, float]
) -> float:
    """
    计算两个边界框的 IoU (Intersection over Union)

    Args:
        box1: 边界框 1 (x1, y1, x2, y2)
        box2: 边界框 2 (x1, y1, x2, y2)

    Returns:
        IoU 值
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # 交集
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # 并集
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0
