"""
目标检测器基础抽象类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass, asdict
from PIL import Image
import numpy as np

from ..utils.logger import LoggerMixin
from ..utils.metrics import MetricsTracker
from ..utils.image_utils import load_image, calculate_iou


@dataclass
class DetectionResult:
    """检测结果数据类"""
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    class_name: str
    class_id: int

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    def area(self) -> float:
        """计算边界框面积"""
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)

    def iou(self, other: 'DetectionResult') -> float:
        """计算与另一个检测结果的 IoU"""
        return calculate_iou(self.bbox, other.bbox)

    def __repr__(self) -> str:
        return (
            f"DetectionResult(class={self.class_name}, "
            f"conf={self.confidence:.2f}, bbox={self.bbox})"
        )


class BaseDetector(ABC, LoggerMixin):
    """目标检测器抽象基类"""

    def __init__(self, config: Dict):
        """
        初始化检测器

        Args:
            config: 检测器配置
        """
        self.config = config
        self.model = None
        self.metrics = MetricsTracker()
        self.is_loaded = False

    @abstractmethod
    def load_model(self) -> None:
        """加载检测模型（子类必须实现）"""
        pass

    @abstractmethod
    def _detect_impl(
        self,
        image: Union[Image.Image, np.ndarray],
        **kwargs
    ) -> List[DetectionResult]:
        """
        检测实现（子类必须实现）

        Args:
            image: PIL Image 或 numpy 数组
            **kwargs: 其他参数

        Returns:
            检测结果列表
        """
        pass

    def detect(
        self,
        image: Union[str, Image.Image, np.ndarray],
        conf_threshold: Optional[float] = None,
        classes: Optional[List[int]] = None,
        **kwargs
    ) -> List[DetectionResult]:
        """
        执行目标检测（带验证和监控）

        Args:
            image: 图像（路径、URL、PIL Image 或 numpy 数组）
            conf_threshold: 置信度阈值
            classes: 要检测的类别列表（None 表示所有类别）
            **kwargs: 其他参数

        Returns:
            检测结果列表
        """
        # 验证模型已加载
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # 加载图像
            if isinstance(image, str):
                image = load_image(image)

            # 使用配置中的默认值
            conf_threshold = conf_threshold or self.config.get('conf_threshold', 0.25)

            # 计时检测
            with self.metrics.timer('detection_time'):
                results = self._detect_impl(image, **kwargs)

            # 过滤结果
            results = self.filter_by_confidence(results, conf_threshold)

            if classes is not None:
                results = self.filter_by_classes(results, classes)

            # 记录指标
            self.metrics.increment('detection_count')
            self.metrics.record('num_detections', len(results))
            self.logger.debug(
                f"Detection completed: {len(results)} objects, "
                f"{self.metrics.get_latest('detection_time')[0]:.2f}s"
            )

            return results

        except Exception as e:
            self.logger.error(f"Detection failed: {e}")
            self.metrics.increment('detection_errors')
            raise

    def batch_detect(
        self,
        images: List[Union[str, Image.Image, np.ndarray]],
        **kwargs
    ) -> List[List[DetectionResult]]:
        """
        批量检测

        Args:
            images: 图像列表
            **kwargs: 其他参数

        Returns:
            检测结果列表的列表
        """
        results = []

        with self.metrics.timer('batch_detection_time'):
            for i, image in enumerate(images):
                self.logger.info(f"Processing image {i + 1}/{len(images)}")
                result = self.detect(image, **kwargs)
                results.append(result)

        self.logger.info(f"Batch detection completed: {len(results)} images")
        return results

    def filter_by_confidence(
        self,
        results: List[DetectionResult],
        threshold: float
    ) -> List[DetectionResult]:
        """
        按置信度过滤结果

        Args:
            results: 检测结果列表
            threshold: 置信度阈值

        Returns:
            过滤后的结果
        """
        return [r for r in results if r.confidence >= threshold]

    def filter_by_classes(
        self,
        results: List[DetectionResult],
        classes: List[int]
    ) -> List[DetectionResult]:
        """
        按类别过滤结果

        Args:
            results: 检测结果列表
            classes: 允许的类别 ID 列表

        Returns:
            过滤后的结果
        """
        return [r for r in results if r.class_id in classes]

    def nms(
        self,
        results: List[DetectionResult],
        iou_threshold: Optional[float] = None
    ) -> List[DetectionResult]:
        """
        非极大值抑制 (NMS)

        Args:
            results: 检测结果列表
            iou_threshold: IoU 阈值

        Returns:
            NMS 后的结果
        """
        if not results:
            return []

        iou_threshold = iou_threshold or self.config.get('iou_threshold', 0.45)

        # 按置信度排序
        results = sorted(results, key=lambda x: x.confidence, reverse=True)

        keep = []
        while results:
            # 保留置信度最高的
            current = results.pop(0)
            keep.append(current)

            # 移除与当前框重叠度高的框
            results = [
                r for r in results
                if current.iou(r) < iou_threshold or r.class_id != current.class_id
            ]

        return keep

    def get_metrics_summary(self) -> Dict:
        """获取性能指标摘要"""
        return self.metrics.get_summary()

    def reset_metrics(self):
        """重置性能指标"""
        self.metrics.reset()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(loaded={self.is_loaded})"
