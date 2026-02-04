"""
性能指标追踪
"""

import time
from typing import Dict, List, Optional
from collections import defaultdict
import statistics
from contextlib import contextmanager


class MetricsTracker:
    """性能指标追踪器"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.start_times: Dict[str, float] = {}
        self.counters: Dict[str, int] = defaultdict(int)

    def record(self, metric_name: str, value: float):
        """
        记录指标值

        Args:
            metric_name: 指标名称
            value: 指标值
        """
        self.metrics[metric_name].append(value)

    def increment(self, counter_name: str, value: int = 1):
        """
        增加计数器

        Args:
            counter_name: 计数器名称
            value: 增加值
        """
        self.counters[counter_name] += value

    def start_timer(self, timer_name: str):
        """
        启动计时器

        Args:
            timer_name: 计时器名称
        """
        self.start_times[timer_name] = time.time()

    def stop_timer(self, timer_name: str) -> float:
        """
        停止计时器并记录

        Args:
            timer_name: 计时器名称

        Returns:
            经过的时间（秒）
        """
        if timer_name not in self.start_times:
            raise ValueError(f"Timer '{timer_name}' not started")

        elapsed = time.time() - self.start_times[timer_name]
        self.record(timer_name, elapsed)
        del self.start_times[timer_name]
        return elapsed

    @contextmanager
    def timer(self, metric_name: str):
        """
        计时器上下文管理器

        使用方式:
            with metrics.timer('processing_time'):
                # 需要计时的代码
                pass
        """
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.record(metric_name, elapsed)

    def get_summary(self, metric_name: Optional[str] = None) -> Dict:
        """
        获取指标摘要

        Args:
            metric_name: 指定指标名称，None 则返回所有指标

        Returns:
            指标摘要字典
        """
        if metric_name:
            return self._compute_summary(metric_name)

        summary = {}
        for name in self.metrics.keys():
            summary[name] = self._compute_summary(name)

        # 添加计数器
        if self.counters:
            summary['counters'] = dict(self.counters)

        return summary

    def _compute_summary(self, metric_name: str) -> Dict:
        """计算单个指标的摘要统计"""
        values = self.metrics.get(metric_name, [])

        if not values:
            return {'count': 0}

        return {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }

    @staticmethod
    def _percentile(values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def reset(self):
        """重置所有指标"""
        self.metrics.clear()
        self.start_times.clear()
        self.counters.clear()

    def reset_metric(self, metric_name: str):
        """重置指定指标"""
        if metric_name in self.metrics:
            self.metrics[metric_name].clear()
        if metric_name in self.counters:
            self.counters[metric_name] = 0

    def get_latest(self, metric_name: str, n: int = 1) -> List[float]:
        """
        获取最近 n 个指标值

        Args:
            metric_name: 指标名称
            n: 获取数量

        Returns:
            最近的指标值列表
        """
        values = self.metrics.get(metric_name, [])
        return values[-n:] if values else []

    def export_to_dict(self) -> Dict:
        """导出所有指标为字典"""
        return {
            'metrics': {name: list(values) for name, values in self.metrics.items()},
            'counters': dict(self.counters)
        }

    def __repr__(self) -> str:
        return f"MetricsTracker(metrics={len(self.metrics)}, counters={len(self.counters)})"


# 全局指标追踪器
_global_metrics: Optional[MetricsTracker] = None


def get_metrics() -> MetricsTracker:
    """获取全局指标追踪器（单例）"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsTracker()
    return _global_metrics


def reset_metrics():
    """重置全局指标追踪器"""
    global _global_metrics
    _global_metrics = None
