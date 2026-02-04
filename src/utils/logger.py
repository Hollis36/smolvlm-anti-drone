"""
统一日志系统
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    设置并返回配置好的 logger

    Args:
        name: Logger 名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件备份数
        console_output: 是否输出到控制台

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台 handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件 handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str, config: Optional[dict] = None) -> logging.Logger:
    """
    获取 logger（便捷函数）

    Args:
        name: Logger 名称
        config: 日志配置字典（可选）

    Returns:
        Logger 实例
    """
    if config is None:
        # 默认配置
        return setup_logger(name)

    return setup_logger(
        name=name,
        level=config.get('level', 'INFO'),
        log_file=config.get('file', {}).get('path') if config.get('file', {}).get('enabled') else None,
        max_bytes=config.get('file', {}).get('max_bytes', 10485760),
        backup_count=config.get('file', {}).get('backup_count', 5),
        console_output=config.get('console', {}).get('enabled', True)
    )


class LoggerMixin:
    """Logger Mixin 类，可被其他类继承"""

    @property
    def logger(self) -> logging.Logger:
        """获取 logger 实例"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
