"""
配置加载器单元测试
"""

import pytest
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.config_loader import ConfigLoader, get_config, reset_config


class TestConfigLoader:
    """配置加载器测试"""

    def setup_method(self):
        """每个测试前重置配置"""
        reset_config()

    def test_load_config(self):
        """测试配置加载"""
        config_path = project_root / "config" / "base_config.yaml"
        loader = ConfigLoader(str(config_path))

        assert loader.config is not None
        assert 'model' in loader.config
        assert 'detectors' in loader.config

    def test_get_nested_value(self):
        """测试获取嵌套配置值"""
        config_path = project_root / "config" / "base_config.yaml"
        loader = ConfigLoader(str(config_path))

        # 测试嵌套访问
        backend = loader.get('model.smolvlm.backend')
        assert backend in ['mlx', 'transformers']

        # 测试默认值
        unknown = loader.get('unknown.key', 'default')
        assert unknown == 'default'

    def test_get_model_config(self):
        """测试获取模型配置"""
        config_path = project_root / "config" / "base_config.yaml"
        loader = ConfigLoader(str(config_path))

        model_config = loader.get_model_config()
        assert 'smolvlm' in model_config
        assert 'name' in model_config['smolvlm']

    def test_get_detector_config(self):
        """测试获取检测器配置"""
        config_path = project_root / "config" / "base_config.yaml"
        loader = ConfigLoader(str(config_path))

        # 测试默认检测器
        detector_config = loader.get_detector_config()
        assert detector_config is not None

        # 测试特定检测器
        yolo_config = loader.get_detector_config('yolov10')
        assert 'model_path' in yolo_config

    def test_global_config_singleton(self):
        """测试全局配置单例"""
        config1 = get_config()
        config2 = get_config()

        # 应该是同一个实例
        assert config1 is config2

    def test_update_config(self):
        """测试更新配置"""
        config_path = project_root / "config" / "base_config.yaml"
        loader = ConfigLoader(str(config_path))

        # 更新配置
        loader.update('model.smolvlm.max_tokens', 150)

        # 验证更新
        assert loader.get('model.smolvlm.max_tokens') == 150
