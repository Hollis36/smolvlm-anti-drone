"""
可视化工具
"""

from typing import List, Tuple, Optional, Dict
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path

from ..detectors.base_detector import DetectionResult
from ..applications.anti_drone import ThreatLevel


class Visualizer:
    """结果可视化工具"""

    # 威胁等级颜色映射
    THREAT_COLORS = {
        ThreatLevel.LOW: '#00FF00',      # 绿色
        ThreatLevel.MEDIUM: '#FFFF00',   # 黄色
        ThreatLevel.HIGH: '#FFA500',     # 橙色
        ThreatLevel.CRITICAL: '#FF0000'  # 红色
    }

    # 类别颜色（循环使用）
    CLASS_COLORS = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
        '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'
    ]

    def __init__(self, font_size: int = 16):
        """
        初始化可视化器

        Args:
            font_size: 字体大小
        """
        self.font_size = font_size
        self.font = self._load_font()

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """加载字体"""
        try:
            # 尝试加载系统字体
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", self.font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", self.font_size)
            except:
                # 使用默认字体
                font = ImageFont.load_default()

        return font

    def draw_detections(
        self,
        image: Image.Image,
        detections: List[DetectionResult],
        show_confidence: bool = True,
        show_labels: bool = True
    ) -> Image.Image:
        """
        绘制检测结果

        Args:
            image: PIL Image
            detections: 检测结果列表
            show_confidence: 是否显示置信度
            show_labels: 是否显示标签

        Returns:
            标注后的图像
        """
        # 创建副本
        image = image.copy()
        draw = ImageDraw.Draw(image)

        for i, det in enumerate(detections):
            # 获取边界框
            x1, y1, x2, y2 = det.bbox

            # 选择颜色
            color = self.CLASS_COLORS[det.class_id % len(self.CLASS_COLORS)]

            # 绘制边界框
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

            # 绘制标签
            if show_labels:
                label = det.class_name
                if show_confidence:
                    label += f" {det.confidence:.2f}"

                # 计算标签背景大小
                bbox = draw.textbbox((x1, y1), label, font=self.font)
                label_width = bbox[2] - bbox[0]
                label_height = bbox[3] - bbox[1]

                # 绘制标签背景
                draw.rectangle(
                    [x1, y1 - label_height - 5, x1 + label_width + 5, y1],
                    fill=color
                )

                # 绘制标签文字
                draw.text((x1 + 2, y1 - label_height - 3), label, fill='white', font=self.font)

        return image

    def draw_threat_banner(
        self,
        image: Image.Image,
        threat_level: ThreatLevel,
        confidence: float,
        num_detections: int
    ) -> Image.Image:
        """
        绘制威胁等级横幅

        Args:
            image: PIL Image
            threat_level: 威胁等级
            confidence: 置信度
            num_detections: 检测数量

        Returns:
            带横幅的图像
        """
        # 创建副本
        image = image.copy()
        draw = ImageDraw.Draw(image)

        width, height = image.size
        banner_height = 60

        # 获取颜色
        color = self.THREAT_COLORS[threat_level]

        # 绘制横幅背景
        draw.rectangle([0, 0, width, banner_height], fill=color)

        # 绘制威胁等级文字
        level_text = f"THREAT: {threat_level.value}"
        draw.text((10, 10), level_text, fill='white', font=self.font)

        # 绘制置信度
        conf_text = f"Confidence: {confidence:.2%}"
        draw.text((10, 35), conf_text, fill='white', font=self.font)

        # 绘制检测数量
        det_text = f"Detections: {num_detections}"
        det_bbox = draw.textbbox((0, 0), det_text, font=self.font)
        det_width = det_bbox[2] - det_bbox[0]
        draw.text((width - det_width - 10, 20), det_text, fill='white', font=self.font)

        return image

    def create_comparison_grid(
        self,
        images: List[Image.Image],
        titles: List[str],
        grid_cols: int = 2
    ) -> Image.Image:
        """
        创建对比网格

        Args:
            images: 图像列表
            titles: 标题列表
            grid_cols: 网格列数

        Returns:
            网格图像
        """
        if len(images) != len(titles):
            raise ValueError("Number of images and titles must match")

        num_images = len(images)
        grid_rows = (num_images + grid_cols - 1) // grid_cols

        # 调整所有图像到相同大小
        target_width = 400
        target_height = 300

        resized_images = []
        for img in images:
            img_resized = img.resize((target_width, target_height))
            resized_images.append(img_resized)

        # 计算网格尺寸
        title_height = 40
        grid_width = target_width * grid_cols
        grid_height = (target_height + title_height) * grid_rows

        # 创建空白画布
        grid_image = Image.new('RGB', (grid_width, grid_height), color='white')
        draw = ImageDraw.Draw(grid_image)

        # 放置图像
        for i, (img, title) in enumerate(zip(resized_images, titles)):
            row = i // grid_cols
            col = i % grid_cols

            x = col * target_width
            y = row * (target_height + title_height) + title_height

            # 粘贴图像
            grid_image.paste(img, (x, y))

            # 绘制标题
            title_y = row * (target_height + title_height)
            draw.rectangle([x, title_y, x + target_width, title_y + title_height], fill='#333333')
            draw.text((x + 10, title_y + 10), title, fill='white', font=self.font)

        return grid_image

    def draw_metrics_overlay(
        self,
        image: Image.Image,
        metrics: Dict[str, float],
        position: Tuple[int, int] = (10, 10)
    ) -> Image.Image:
        """
        绘制性能指标覆盖层

        Args:
            image: PIL Image
            metrics: 指标字典
            position: 起始位置

        Returns:
            带指标的图像
        """
        image = image.copy()
        draw = ImageDraw.Draw(image)

        x, y = position
        line_height = 25

        # 绘制半透明背景
        max_width = max([draw.textbbox((0, 0), f"{k}: {v}", font=self.font)[2] for k, v in metrics.items()])
        bg_height = len(metrics) * line_height + 20

        # 创建半透明层（使用 alpha 混合）
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [x - 5, y - 5, x + max_width + 10, y + bg_height],
            fill=(0, 0, 0, 180)
        )
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(image)

        # 绘制指标
        current_y = y
        for key, value in metrics.items():
            if isinstance(value, float):
                text = f"{key}: {value:.2f}"
            else:
                text = f"{key}: {value}"

            draw.text((x, current_y), text, fill='white', font=self.font)
            current_y += line_height

        return image

    def save_annotated_image(
        self,
        image: Image.Image,
        detections: List[DetectionResult],
        output_path: str,
        threat_level: Optional[ThreatLevel] = None,
        confidence: Optional[float] = None
    ):
        """
        保存标注后的图像

        Args:
            image: 原始图像
            detections: 检测结果
            output_path: 输出路径
            threat_level: 威胁等级（可选）
            confidence: 置信度（可选）
        """
        # 绘制检测框
        annotated = self.draw_detections(image, detections)

        # 绘制威胁横幅
        if threat_level and confidence is not None:
            annotated = self.draw_threat_banner(
                annotated,
                threat_level,
                confidence,
                len(detections)
            )

        # 保存
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        annotated.save(output_path)


def create_detection_heatmap(
    image_size: Tuple[int, int],
    detections: List[DetectionResult],
    output_path: Optional[str] = None
) -> Image.Image:
    """
    创建检测热力图

    Args:
        image_size: 图像尺寸 (width, height)
        detections: 检测结果列表
        output_path: 输出路径（可选）

    Returns:
        热力图
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    width, height = image_size

    # 创建图形
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)  # 反转 Y 轴
    ax.set_aspect('equal')

    # 绘制检测框
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        w = x2 - x1
        h = y2 - y1

        # 根据置信度设置颜色
        alpha = det.confidence
        color = plt.cm.Reds(alpha)

        rect = patches.Rectangle(
            (x1, y1), w, h,
            linewidth=2,
            edgecolor=color,
            facecolor=color,
            alpha=0.3
        )
        ax.add_patch(rect)

        # 添加标签
        ax.text(
            x1, y1 - 5,
            f"{det.class_name}\n{det.confidence:.2f}",
            fontsize=10,
            color='red',
            weight='bold'
        )

    ax.set_title('Detection Heatmap', fontsize=16, weight='bold')
    ax.set_xlabel('X (pixels)')
    ax.set_ylabel('Y (pixels)')

    # 保存或显示
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    else:
        plt.show()

    # 转换为 PIL Image
    fig.canvas.draw()
    img_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    img_array = img_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    img = Image.fromarray(img_array)

    plt.close()

    return img
