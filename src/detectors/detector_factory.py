"""
检测器工厂类
"""

from typing import Dict, Any, Type
from .base_detector import BaseDetector
from .yolo_detector import YOLODetector


class DetectorFactory:
    """检测器工厂"""

    # 注册的检测器
    _detectors: Dict[str, Type[BaseDetector]] = {
        'yolov8': YOLODetector,
        'yolov10': YOLODetector,
    }

    @classmethod
    def create_detector(
        cls,
        detector_type: str,
        config: Dict[str, Any]
    ) -> BaseDetector:
        """
        创建检测器实例

        Args:
            detector_type: 检测器类型 ('yolov8', 'yolov10', 等)
            config: 检测器配置

        Returns:
            检测器实例

        Raises:
            ValueError: 如果检测器类型未注册
        """
        if detector_type not in cls._detectors:
            raise ValueError(
                f"Unknown detector type: {detector_type}. "
                f"Available: {list(cls._detectors.keys())}"
            )

        detector_class = cls._detectors[detector_type]
        return detector_class(config)

    @classmethod
    def register_detector(
        cls,
        name: str,
        detector_class: Type[BaseDetector]
    ) -> None:
        """
        注册新的检测器

        Args:
            name: 检测器名称
            detector_class: 检测器类
        """
        cls._detectors[name] = detector_class

    @classmethod
    def list_detectors(cls) -> list:
        """列出所有已注册的检测器"""
        return list(cls._detectors.keys())

    @classmethod
    def is_registered(cls, detector_type: str) -> bool:
        """检查检测器是否已注册"""
        return detector_type in cls._detectors
