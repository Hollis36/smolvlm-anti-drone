"""
性能指标追踪器单元测试
"""

import pytest
import time
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from utils.metrics import MetricsTracker, get_metrics, reset_metrics


class TestMetricsTracker:
    """指标追踪器测试"""

    def setup_method(self):
        """每个测试前创建新的追踪器"""
        self.tracker = MetricsTracker()

    def test_record_metric(self):
        """测试记录指标"""
        self.tracker.record('test_metric', 1.5)
        self.tracker.record('test_metric', 2.5)

        summary = self.tracker.get_summary('test_metric')
        assert summary['count'] == 2
        assert summary['mean'] == 2.0
        assert summary['min'] == 1.5
        assert summary['max'] == 2.5

    def test_increment_counter(self):
        """测试计数器"""
        self.tracker.increment('test_counter')
        self.tracker.increment('test_counter', 5)

        summary = self.tracker.get_summary()
        assert summary['counters']['test_counter'] == 6

    def test_timer(self):
        """测试计时器"""
        self.tracker.start_timer('test_timer')
        time.sleep(0.1)
        elapsed = self.tracker.stop_timer('test_timer')

        assert elapsed >= 0.1
        assert len(self.tracker.metrics['test_timer']) == 1

    def test_timer_context(self):
        """测试计时器上下文管理器"""
        with self.tracker.timer('context_timer'):
            time.sleep(0.05)

        summary = self.tracker.get_summary('context_timer')
        assert summary['count'] == 1
        assert summary['mean'] >= 0.05

    def test_get_latest(self):
        """测试获取最新指标"""
        self.tracker.record('metric', 1.0)
        self.tracker.record('metric', 2.0)
        self.tracker.record('metric', 3.0)

        latest = self.tracker.get_latest('metric', n=2)
        assert latest == [2.0, 3.0]

    def test_reset(self):
        """测试重置"""
        self.tracker.record('metric', 1.0)
        self.tracker.increment('counter')

        self.tracker.reset()

        assert len(self.tracker.metrics) == 0
        assert len(self.tracker.counters) == 0

    def test_global_metrics(self):
        """测试全局指标追踪器"""
        metrics1 = get_metrics()
        metrics2 = get_metrics()

        # 应该是同一个实例
        assert metrics1 is metrics2

        reset_metrics()

        # 重置后应该是新实例
        metrics3 = get_metrics()
        assert metrics3 is not metrics1
