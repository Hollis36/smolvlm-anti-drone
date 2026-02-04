"""
YOLO 系列检测器实现
"""

from typing import List, Union, Dict
from PIL import Image
import numpy as np

from .base_detector import BaseDetector, DetectionResult


class YOLODetector(BaseDetector):
    """YOLO 检测器（支持 YOLOv8, YOLOv10）"""

    def __init__(self, config: Dict):
        """
        初始化 YOLO 检测器

        Args:
            config: 配置，包含:
                - model_path: 模型路径 (如 'yolov10n.pt')
                - conf_threshold: 置信度阈值
                - iou_threshold: IoU 阈值
                - device: 设备 ('mps', 'cuda', 'cpu')
        """
        super().__init__(config)
        self.load_model()

    def load_model(self) -> None:
        """加载 YOLO 模型"""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "Ultralytics not installed. Install with: pip install ultralytics"
            )

        model_path = self.config.get('model_path', 'yolov10n.pt')
        device = self.config.get('device', 'mps')

        self.logger.info(f"Loading YOLO model: {model_path}")

        try:
            self.model = YOLO(model_path)

            # 设置设备
            if device == 'mps':
                # YOLOv8/v10 在 MPS 上需要特殊处理
                import torch
                if torch.backends.mps.is_available():
                    self.model.to('mps')
                    self.logger.info("Using MPS device")
                else:
                    self.logger.warning("MPS not available, using CPU")
                    self.model.to('cpu')
            else:
                self.model.to(device)

            self.is_loaded = True
            self.logger.info("YOLO model loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            raise

    def _detect_impl(
        self,
        image: Union[Image.Image, np.ndarray],
        **kwargs
    ) -> List[DetectionResult]:
        """
        YOLO 检测实现

        Args:
            image: PIL Image 或 numpy 数组
            **kwargs: 其他参数

        Returns:
            检测结果列表
        """
        # 执行检测
        results = self.model(
            image,
            verbose=False,
            conf=self.config.get('conf_threshold', 0.25)
        )

        # 解析结果
        detections = []

        for result in results:
            boxes = result.boxes

            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                # 边界框坐标
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy

                # 置信度
                confidence = float(box.conf[0].cpu().numpy())

                # 类别
                class_id = int(box.cls[0].cpu().numpy())
                class_name = result.names[class_id]

                detection = DetectionResult(
                    bbox=(float(x1), float(y1), float(x2), float(y2)),
                    confidence=confidence,
                    class_name=class_name,
                    class_id=class_id
                )

                detections.append(detection)

        return detections

    def detect_specific_classes(
        self,
        image: Union[str, Image.Image, np.ndarray],
        target_classes: List[str]
    ) -> List[DetectionResult]:
        """
        检测特定类别

        Args:
            image: 图像
            target_classes: 目标类别列表（如 ['person', 'car', 'drone']）

        Returns:
            检测结果列表
        """
        all_detections = self.detect(image)

        # 过滤目标类别
        filtered = [
            d for d in all_detections
            if d.class_name.lower() in [c.lower() for c in target_classes]
        ]

        self.logger.info(
            f"Detected {len(filtered)} objects from {len(target_classes)} target classes"
        )

        return filtered
