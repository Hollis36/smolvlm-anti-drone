"""
视频流处理模块
"""

import cv2
from typing import Optional, Callable, List
from queue import Queue, Empty
from threading import Thread, Event
from pathlib import Path
import time
import numpy as np

from .anti_drone import AntiDroneSystem, ThreatAssessment
from ..utils.logger import get_logger
from ..utils.metrics import MetricsTracker


class VideoProcessor:
    """视频处理器（支持文件和实时流）"""

    def __init__(
        self,
        anti_drone_system: AntiDroneSystem,
        frame_skip: int = 5,
        queue_size: int = 30
    ):
        """
        初始化视频处理器

        Args:
            anti_drone_system: 反无人机系统实例
            frame_skip: 跳帧数（处理每 N 帧）
            queue_size: 帧队列大小
        """
        self.system = anti_drone_system
        self.frame_skip = frame_skip
        self.frame_queue = Queue(maxsize=queue_size)
        self.result_queue = Queue(maxsize=queue_size)
        self.logger = get_logger(__name__)
        self.metrics = MetricsTracker()

        self.running = Event()
        self.capture_thread: Optional[Thread] = None
        self.process_thread: Optional[Thread] = None

    def process_video_file(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        draw_results: bool = True
    ) -> List[ThreatAssessment]:
        """
        处理视频文件

        Args:
            video_path: 视频文件路径
            output_path: 输出视频路径（可选）
            draw_results: 是否在视频上绘制结果

        Returns:
            威胁评估结果列表
        """
        self.logger.info(f"Processing video file: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        # 获取视频信息
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.logger.info(
            f"Video info: {width}x{height} @ {fps} FPS, "
            f"{total_frames} frames"
        )

        # 创建输出视频（如果需要）
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        results = []
        frame_count = 0

        with self.metrics.timer('total_video_processing'):
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 跳帧处理
                if frame_count % self.frame_skip == 0:
                    # 转换为 RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # 执行威胁评估
                    with self.metrics.timer('frame_processing'):
                        result = self.system.process_frame(frame_rgb)

                    results.append(result)

                    self.logger.info(
                        f"Frame {frame_count}/{total_frames}: "
                        f"{result.threat_level.value} "
                        f"({result.confidence:.2f})"
                    )

                    # 绘制结果
                    if draw_results:
                        frame = self._draw_results(frame, result)

                # 写入输出视频
                if writer:
                    writer.write(frame)

                frame_count += 1

        # 清理
        cap.release()
        if writer:
            writer.release()

        self.logger.info(
            f"Video processing complete: {len(results)} frames analyzed"
        )

        return results

    def start_realtime_stream(
        self,
        source: int = 0,
        callback: Optional[Callable] = None
    ):
        """
        启动实时流处理

        Args:
            source: 视频源（0 = 默认摄像头，或 RTSP URL）
            callback: 结果回调函数
        """
        self.logger.info(f"Starting realtime stream from source: {source}")

        self.running.set()

        # 启动捕获线程
        self.capture_thread = Thread(
            target=self._capture_frames,
            args=(source,),
            daemon=True
        )
        self.capture_thread.start()

        # 启动处理线程
        self.process_thread = Thread(
            target=self._process_frames,
            args=(callback,),
            daemon=True
        )
        self.process_thread.start()

        self.logger.info("Realtime stream started")

    def stop_realtime_stream(self):
        """停止实时流处理"""
        self.logger.info("Stopping realtime stream...")

        self.running.clear()

        # 等待线程结束
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)

        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=5)

        self.logger.info("Realtime stream stopped")

    def _capture_frames(self, source):
        """捕获视频帧（线程函数）"""
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            self.logger.error(f"Cannot open video source: {source}")
            return

        frame_count = 0

        while self.running.is_set():
            ret, frame = cap.read()
            if not ret:
                self.logger.warning("Failed to read frame")
                break

            # 跳帧
            if frame_count % self.frame_skip == 0:
                # 转换为 RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 放入队列（非阻塞）
                try:
                    self.frame_queue.put_nowait((frame_count, frame_rgb))
                except:
                    # 队列满，跳过此帧
                    pass

            frame_count += 1

        cap.release()
        self.logger.info("Frame capture stopped")

    def _process_frames(self, callback: Optional[Callable]):
        """处理视频帧（线程函数）"""
        while self.running.is_set():
            try:
                # 从队列获取帧（超时 1 秒）
                frame_count, frame = self.frame_queue.get(timeout=1)

                # 执行威胁评估
                with self.metrics.timer('realtime_processing'):
                    result = self.system.process_frame(frame)

                # 存储结果
                self.result_queue.put((frame_count, result))

                self.logger.info(
                    f"Frame {frame_count}: {result.threat_level.value} "
                    f"({result.confidence:.2f})"
                )

                # 回调
                if callback:
                    callback(frame_count, frame, result)

            except Empty:
                # 队列为空，继续等待
                continue

            except Exception as e:
                self.logger.error(f"Error processing frame: {e}")

        self.logger.info("Frame processing stopped")

    def _draw_results(
        self,
        frame: np.ndarray,
        result: ThreatAssessment
    ) -> np.ndarray:
        """
        在视频帧上绘制结果

        Args:
            frame: 视频帧 (BGR)
            result: 威胁评估结果

        Returns:
            标注后的视频帧
        """
        # 复制帧
        frame = frame.copy()

        # 获取帧尺寸
        height, width = frame.shape[:2]

        # 威胁等级颜色映射
        color_map = {
            'LOW': (0, 255, 0),      # 绿色
            'MEDIUM': (0, 255, 255),  # 黄色
            'HIGH': (0, 165, 255),    # 橙色
            'CRITICAL': (0, 0, 255)   # 红色
        }

        color = color_map.get(result.threat_level.value, (255, 255, 255))

        # 绘制检测框
        for det in result.detections:
            x1, y1, x2, y2 = map(int, det.bbox)

            # 边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # 标签
            label = f"{det.class_name} {det.confidence:.2f}"
            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )

            cv2.rectangle(
                frame,
                (x1, y1 - label_h - 5),
                (x1 + label_w, y1),
                color,
                -1
            )

            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

        # 绘制威胁等级横幅
        banner_height = 50
        cv2.rectangle(
            frame,
            (0, 0),
            (width, banner_height),
            color,
            -1
        )

        # 威胁等级文字
        text = f"THREAT: {result.threat_level.value}"
        (text_w, text_h), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2
        )

        cv2.putText(
            frame,
            text,
            (10, banner_height - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2
        )

        # 置信度
        conf_text = f"Conf: {result.confidence:.2f}"
        cv2.putText(
            frame,
            conf_text,
            (width - 150, banner_height - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        return frame

    def get_results(self, max_results: int = 10) -> List[ThreatAssessment]:
        """
        获取最近的评估结果

        Args:
            max_results: 最多返回的结果数

        Returns:
            威胁评估结果列表
        """
        results = []

        while not self.result_queue.empty() and len(results) < max_results:
            try:
                _, result = self.result_queue.get_nowait()
                results.append(result)
            except Empty:
                break

        return results

    def get_metrics_summary(self):
        """获取性能指标摘要"""
        return self.metrics.get_summary()

    def __repr__(self) -> str:
        return f"VideoProcessor(frame_skip={self.frame_skip}, running={self.running.is_set()})"
