"""
SmolVLM 模型实现（统一 MLX 和 Transformers 后端）
"""

from typing import Optional, Dict, Any, Union
from PIL import Image

from .base_model import BaseVisionLanguageModel


class SmolVLM(BaseVisionLanguageModel):
    """SmolVLM 2B 参数视觉-语言模型"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 SmolVLM

        Args:
            config: 模型配置，包含:
                - name: 模型名称
                - backend: 'mlx' 或 'transformers'
                - device: 设备 ('mps', 'cuda', 'cpu')
                - max_tokens: 最大生成 token 数
                - temperature: 温度参数
                - repetition_penalty: 重复惩罚
        """
        super().__init__(config)
        self.backend = config.get('backend', 'mlx')
        self.device = config.get('device', 'mps')
        self.load_model()

    def load_model(self) -> None:
        """加载模型（自动选择后端）"""
        self.logger.info(f"Loading SmolVLM with {self.backend} backend")

        try:
            if self.backend == 'mlx':
                self._load_mlx()
            else:
                self._load_transformers()

            self.is_loaded = True
            self.logger.info("Model loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

    def _load_mlx(self) -> None:
        """加载 MLX 后端"""
        try:
            from mlx_vlm import load
        except ImportError:
            raise ImportError(
                "MLX not installed. Install with: pip install mlx-vlm"
            )

        # MLX 社区版本
        mlx_model_name = self.config.get('name', 'mlx-community/SmolVLM-Instruct-bf16')
        self.model, self.processor = load(mlx_model_name)
        self.logger.info(f"Loaded MLX model: {mlx_model_name}")

    def _load_transformers(self) -> None:
        """加载 Transformers 后端"""
        try:
            from transformers import AutoProcessor, AutoModelForVision2Seq
            import torch
        except ImportError:
            raise ImportError(
                "Transformers not installed. Install with: pip install transformers torch"
            )

        model_name = self.config.get('name', 'HuggingFaceTB/SmolVLM-Instruct')

        self.processor = AutoProcessor.from_pretrained(model_name)

        # 设备选择
        if self.device == 'mps' and torch.backends.mps.is_available():
            device = torch.device("mps")
            self.logger.info("Using MPS (Metal Performance Shaders)")
        elif self.device == 'cuda' and torch.cuda.is_available():
            device = torch.device("cuda")
            self.logger.info("Using CUDA")
        else:
            device = torch.device("cpu")
            self.logger.warning("Using CPU (slower performance)")

        self.model = AutoModelForVision2Seq.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map=device
        )

        self.torch_device = device
        self.logger.info(f"Loaded Transformers model: {model_name}")

    def _inference_impl(
        self,
        image: Image.Image,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.6,
        **kwargs
    ) -> str:
        """
        推理实现

        Args:
            image: PIL Image
            prompt: 文本提示
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        if self.backend == 'mlx':
            return self._inference_mlx(image, prompt, max_tokens, temperature, **kwargs)
        else:
            return self._inference_transformers(image, prompt, max_tokens, temperature, **kwargs)

    def _inference_mlx(
        self,
        image: Image.Image,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """MLX 推理"""
        from mlx_vlm import generate

        repetition_penalty = kwargs.get(
            'repetition_penalty',
            self.config.get('repetition_penalty', 1.2)
        )

        output = generate(
            self.model,
            self.processor,
            image,
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            repetition_penalty=repetition_penalty
        )

        return output

    def _inference_transformers(
        self,
        image: Image.Image,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Transformers 推理"""
        import torch

        repetition_penalty = kwargs.get(
            'repetition_penalty',
            self.config.get('repetition_penalty', 1.2)
        )

        # 准备输入
        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        ).to(self.torch_device)

        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
                do_sample=temperature > 0
            )

        # 解码
        generated_text = self.processor.decode(
            outputs[0],
            skip_special_tokens=True
        )

        return generated_text

    def quick_description(self, image: Union[str, Image.Image]) -> str:
        """
        快速图像描述（预设提示词）

        Args:
            image: 图像

        Returns:
            图像描述
        """
        prompt = "<image>Describe this image concisely in 1-2 sentences."
        return self.inference(image, prompt, max_tokens=80)

    def visual_qa(
        self,
        image: Union[str, Image.Image],
        question: str
    ) -> str:
        """
        视觉问答

        Args:
            image: 图像
            question: 问题

        Returns:
            答案
        """
        prompt = f"<image>{question}"
        return self.inference(image, prompt, max_tokens=100)

    def scene_understanding(
        self,
        image: Union[str, Image.Image],
        focus: Optional[str] = None
    ) -> str:
        """
        场景理解

        Args:
            image: 图像
            focus: 关注点（如 "threats", "objects", "activities"）

        Returns:
            场景描述
        """
        if focus:
            prompt = f"<image>Analyze this scene focusing on {focus}. Be specific and concise."
        else:
            prompt = "<image>Analyze this scene. What do you see? Be specific."

        return self.inference(image, prompt, max_tokens=120)
