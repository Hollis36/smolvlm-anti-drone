"""
视觉-语言模型基础抽象类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union, Optional
from PIL import Image
import time

from ..utils.logger import LoggerMixin
from ..utils.metrics import MetricsTracker
from ..utils.image_utils import load_image


class BaseVisionLanguageModel(ABC, LoggerMixin):
    """视觉-语言模型抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化模型

        Args:
            config: 模型配置字典
        """
        self.config = config
        self.model = None
        self.processor = None
        self.metrics = MetricsTracker()
        self.is_loaded = False

    @abstractmethod
    def load_model(self) -> None:
        """加载模型（子类必须实现）"""
        pass

    @abstractmethod
    def _inference_impl(
        self,
        image: Image.Image,
        prompt: str,
        **kwargs
    ) -> str:
        """
        推理实现（子类必须实现）

        Args:
            image: PIL Image
            prompt: 文本提示
            **kwargs: 其他参数

        Returns:
            模型输出文本
        """
        pass

    def inference(
        self,
        image: Union[str, Image.Image],
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        执行推理（带验证和监控）

        Args:
            image: 图像（路径、URL 或 PIL Image）
            prompt: 文本提示
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            模型输出
        """
        # 验证模型已加载
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # 验证输入
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Invalid prompt: must be non-empty string")

        try:
            # 加载图像
            image = load_image(image)

            # 使用配置中的默认值
            max_tokens = max_tokens or self.config.get('max_tokens', 100)
            temperature = temperature or self.config.get('temperature', 0.6)

            # 计时推理
            with self.metrics.timer('inference_time'):
                result = self._inference_impl(
                    image,
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

            # 记录指标
            self.metrics.increment('inference_count')
            self.logger.debug(
                f"Inference completed: {len(result)} chars, "
                f"{self.metrics.get_latest('inference_time')[0]:.2f}s"
            )

            return result

        except Exception as e:
            self.logger.error(f"Inference failed: {e}")
            self.metrics.increment('inference_errors')
            raise

    def batch_inference(
        self,
        images: List[Union[str, Image.Image]],
        prompts: List[str],
        batch_size: Optional[int] = None,
        **kwargs
    ) -> List[str]:
        """
        批量推理

        Args:
            images: 图像列表
            prompts: 提示列表
            batch_size: 批处理大小
            **kwargs: 其他参数

        Returns:
            输出列表
        """
        if len(images) != len(prompts):
            raise ValueError(
                f"Number of images ({len(images)}) and prompts ({len(prompts)}) must match"
            )

        batch_size = batch_size or self.config.get('batch_size', 4)
        results = []

        with self.metrics.timer('batch_inference_time'):
            for i in range(0, len(images), batch_size):
                batch_images = images[i:i + batch_size]
                batch_prompts = prompts[i:i + batch_size]

                self.logger.info(f"Processing batch {i // batch_size + 1}/{(len(images) + batch_size - 1) // batch_size}")

                batch_results = [
                    self.inference(img, prompt, **kwargs)
                    for img, prompt in zip(batch_images, batch_prompts)
                ]

                results.extend(batch_results)

        self.logger.info(f"Batch inference completed: {len(results)} items")
        return results

    def get_metrics_summary(self) -> Dict:
        """获取性能指标摘要"""
        return self.metrics.get_summary()

    def reset_metrics(self):
        """重置性能指标"""
        self.metrics.reset()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(loaded={self.is_loaded})"
