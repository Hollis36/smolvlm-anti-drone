"""
反无人机系统应用
"""

from typing import Dict, Union, List, Tuple
from PIL import Image
import numpy as np
from dataclasses import dataclass
from enum import Enum
import time

from ..core.smolvlm import SmolVLM
from ..detectors.detector_factory import DetectorFactory
from ..detectors.base_detector import DetectionResult
from ..utils.logger import get_logger
from ..utils.metrics import MetricsTracker


class ThreatLevel(Enum):
    """威胁等级枚举"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ThreatAssessment:
    """威胁评估结果"""
    threat_level: ThreatLevel
    confidence: float
    detections: List[DetectionResult]
    scene_description: str
    recommended_action: str
    processing_time_ms: float

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'threat_level': self.threat_level.value,
            'confidence': self.confidence,
            'num_detections': len(self.detections),
            'detections': [d.to_dict() for d in self.detections],
            'scene_description': self.scene_description,
            'recommended_action': self.recommended_action,
            'processing_time_ms': self.processing_time_ms
        }

    def __repr__(self) -> str:
        return (
            f"ThreatAssessment(level={self.threat_level.value}, "
            f"conf={self.confidence:.2f}, detections={len(self.detections)})"
        )


class AntiDroneSystem:
    """反无人机系统（重构版）"""

    def __init__(self, config: Dict):
        """
        初始化反无人机系统

        Args:
            config: 系统配置
        """
        self.config = config
        self.logger = get_logger(__name__, config.get('logging'))
        self.metrics = MetricsTracker()

        self.logger.info("Initializing Anti-Drone System...")

        # 初始化 VLM
        vlm_config = config.get('model', {}).get('smolvlm', {})
        self.vlm = SmolVLM(vlm_config)

        # 初始化检测器
        detector_config = config.get('detectors', {})
        default_detector = detector_config.get('default', 'yolov10')
        detector_params = detector_config.get(default_detector, {})

        self.detector = DetectorFactory.create_detector(
            default_detector,
            detector_params
        )

        # 威胁等级配置
        self.threat_thresholds = config.get('anti_drone', {}).get('threat_levels', {
            'low': 0.3,
            'medium': 0.5,
            'high': 0.7,
            'critical': 0.9
        })

        self.logger.info("Anti-Drone System initialized successfully")

    def process_frame(
        self,
        image: Union[str, Image.Image, np.ndarray]
    ) -> ThreatAssessment:
        """
        处理单帧图像

        Args:
            image: 输入图像

        Returns:
            威胁评估结果
        """
        start_time = time.time()

        try:
            with self.metrics.timer('total_processing'):
                # 1. 目标检测
                with self.metrics.timer('detection'):
                    detections = self.detector.detect(image)

                self.logger.debug(f"Detected {len(detections)} objects")

                # 2. 场景理解（SmolVLM）
                with self.metrics.timer('scene_analysis'):
                    scene_desc = self._analyze_scene(image, detections)

                # 3. 威胁评估
                threat_level, confidence = self._assess_threat(detections, scene_desc)

                # 4. 生成响应建议
                action = self._recommend_action(threat_level, detections)

            # 计算处理时间
            processing_time = (time.time() - start_time) * 1000

            # 记录指标
            self.metrics.record('processing_time_ms', processing_time)
            self.metrics.increment('frames_processed')

            return ThreatAssessment(
                threat_level=threat_level,
                confidence=confidence,
                detections=detections,
                scene_description=scene_desc,
                recommended_action=action,
                processing_time_ms=processing_time
            )

        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            self.metrics.increment('processing_errors')
            raise

    def _analyze_scene(
        self,
        image: Union[str, Image.Image],
        detections: List[DetectionResult]
    ) -> str:
        """
        场景分析

        Args:
            image: 图像
            detections: 检测结果

        Returns:
            场景描述
        """
        # 构建提示词
        detected_objects = [d.class_name for d in detections]

        if detected_objects:
            objects_str = ', '.join(set(detected_objects))
            prompt = f"""<image>Security Scene Analysis

Detected objects: {objects_str}

Provide a concise assessment:
1. What threats are visible?
2. Environmental conditions?
3. Risk level assessment?

Be brief and specific."""
        else:
            prompt = """<image>Security Scene Analysis

No objects detected by the detector.

Describe:
1. What do you see in the scene?
2. Any potential threats or unusual activity?
3. Overall safety assessment?

Be concise."""

        return self.vlm.inference(image, prompt, max_tokens=120)

    def _assess_threat(
        self,
        detections: List[DetectionResult],
        scene_description: str
    ) -> Tuple[ThreatLevel, float]:
        """
        威胁评估

        Args:
            detections: 检测结果
            scene_description: 场景描述

        Returns:
            (威胁等级, 置信度)
        """
        # 基于关键词的威胁评估
        threat_keywords = {
            ThreatLevel.CRITICAL: ['drone', 'uav', 'weapon', 'attack', 'explosive', 'critical risk'],
            ThreatLevel.HIGH: ['suspicious', 'unauthorized', 'approaching', 'high risk', 'danger'],
            ThreatLevel.MEDIUM: ['unknown', 'unidentified', 'moderate risk', 'caution'],
            ThreatLevel.LOW: ['clear', 'safe', 'normal', 'low risk', 'no threat']
        }

        scene_lower = scene_description.lower()

        # 检查关键词
        for level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH, ThreatLevel.MEDIUM, ThreatLevel.LOW]:
            keywords = threat_keywords[level]
            for keyword in keywords:
                if keyword in scene_lower:
                    # 计算置信度
                    confidence = max([d.confidence for d in detections]) if detections else 0.5
                    return level, confidence

        # 默认：基于检测数量
        if len(detections) > 5:
            return ThreatLevel.MEDIUM, 0.6
        elif len(detections) > 0:
            return ThreatLevel.LOW, 0.5
        else:
            return ThreatLevel.LOW, 0.3

    def _recommend_action(
        self,
        threat_level: ThreatLevel,
        detections: List[DetectionResult]
    ) -> str:
        """
        推荐响应行动

        Args:
            threat_level: 威胁等级
            detections: 检测结果

        Returns:
            行动建议
        """
        actions = {
            ThreatLevel.CRITICAL: (
                "🚨 IMMEDIATE ACTION REQUIRED:\n"
                "1. Activate countermeasures\n"
                "2. Alert security personnel\n"
                "3. Prepare evacuation if necessary"
            ),
            ThreatLevel.HIGH: (
                "⚠️ HIGH ALERT:\n"
                "1. Monitor closely\n"
                "2. Prepare countermeasures\n"
                "3. Notify command center"
            ),
            ThreatLevel.MEDIUM: (
                "⚡ INCREASED VIGILANCE:\n"
                "1. Continue surveillance\n"
                "2. Track detected objects\n"
                "3. Increase alert level"
            ),
            ThreatLevel.LOW: (
                "✅ NORMAL OPERATIONS:\n"
                "1. Maintain awareness\n"
                "2. Continue routine monitoring"
            )
        }

        base_action = actions.get(threat_level, "Unknown threat level")

        # 添加检测详情
        if detections:
            det_summary = f"\n\nDetected: {len(detections)} objects"
            return base_action + det_summary

        return base_action

    def quick_scan(self, image: Union[str, Image.Image]) -> ThreatAssessment:
        """
        快速扫描（快速响应模式）

        Args:
            image: 图像

        Returns:
            威胁评估
        """
        self.logger.info("Running quick scan...")
        return self.process_frame(image)

    def get_metrics_summary(self) -> Dict:
        """获取性能指标摘要"""
        summary = self.metrics.get_summary()
        summary['vlm_metrics'] = self.vlm.get_metrics_summary()
        summary['detector_metrics'] = self.detector.get_metrics_summary()
        return summary

    def reset_metrics(self):
        """重置所有指标"""
        self.metrics.reset()
        self.vlm.reset_metrics()
        self.detector.reset_metrics()

    def __repr__(self) -> str:
        return (
            f"AntiDroneSystem(vlm={self.vlm.__class__.__name__}, "
            f"detector={self.detector.__class__.__name__})"
        )
