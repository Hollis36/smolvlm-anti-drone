"""
配置加载器
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os


class ConfigLoader:
    """配置加载和管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为 config/base_config.yaml
        """
        if config_path is None:
            # 默认配置路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "base_config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 环境变量覆盖
        config = self._apply_env_overrides(config)

        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        # 示例: SMOLVLM_MODEL_BACKEND=transformers
        env_prefix = "SMOLVLM_"

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # 解析配置路径: MODEL_BACKEND -> model.smolvlm.backend
                config_key = key[len(env_prefix):].lower().replace('_', '.')
                self._set_nested_value(config, config_key, value)

        return config

    def _set_nested_value(self, config: Dict, key_path: str, value: Any):
        """设置嵌套配置值"""
        keys = key_path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 类型转换
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif self._is_float(value):
            value = float(value)

        current[keys[-1]] = value

    @staticmethod
    def _is_float(value: str) -> bool:
        """检查字符串是否为浮点数"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key_path: 配置键路径，如 "model.smolvlm.backend"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split('.')
        current = self.config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.get("model", {})

    def get_detector_config(self, detector_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取检测器配置

        Args:
            detector_type: 检测器类型，如 "yolov10"，None 则返回默认检测器配置
        """
        if detector_type is None:
            detector_type = self.get("detectors.default", "yolov10")

        return self.get(f"detectors.{detector_type}", {})

    def get_anti_drone_config(self) -> Dict[str, Any]:
        """获取反无人机配置"""
        return self.get("anti_drone", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get("logging", {})

    def get_api_config(self) -> Dict[str, Any]:
        """获取 API 配置"""
        return self.get("api", {})

    def update(self, key_path: str, value: Any):
        """
        更新配置值

        Args:
            key_path: 配置键路径
            value: 新值
        """
        self._set_nested_value(self.config, key_path, value)

    def save(self, output_path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            output_path: 输出路径，None 则覆盖原文件
        """
        if output_path is None:
            output_path = self.config_path

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def __repr__(self) -> str:
        return f"ConfigLoader(config_path='{self.config_path}')"


# 全局配置实例（单例）
_global_config: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    获取全局配置实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigLoader 实例
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader(config_path)

    return _global_config


def reset_config():
    """重置全局配置"""
    global _global_config
    _global_config = None
