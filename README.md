# SmolVLM Anti-Drone System (Refactored)

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MLX](https://img.shields.io/badge/MLX-0.20+-orange.svg)](https://github.com/ml-explore/mlx)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub Stars](https://img.shields.io/github/stars/Hollis36/smolvlm-anti-drone?style=social)](https://github.com/Hollis36/smolvlm-anti-drone)

> 基于 SmolVLM (2B 参数) 的轻量级多模态反无人机检测系统 - 重构版

## 项目特点

- **模块化架构** - 清晰的分层设计，易于维护和扩展
- **配置驱动** - YAML 配置文件，灵活调整参数
- **统一接口** - 抽象基类设计，支持多种后端
- **性能监控** - 内置指标追踪，实时性能分析
- **高度可测试** - 完整的单元测试框架
- **生产就绪** - 日志系统、错误处理、性能优化

## 项目结构

```
refactored/
├── config/                  # 配置文件
│   └── base_config.yaml     # 基础配置
├── src/                     # 源代码
│   ├── core/                # 核心模块
│   │   ├── base_model.py    # VLM 抽象基类
│   │   ├── smolvlm.py       # SmolVLM 实现
│   │   └── config_loader.py # 配置加载器
│   ├── detectors/           # 检测器模块
│   │   ├── base_detector.py # 检测器抽象基类
│   │   ├── yolo_detector.py # YOLO 实现
│   │   └── detector_factory.py # 工厂模式
│   ├── applications/        # 应用层
│   │   └── anti_drone.py    # 反无人机系统
│   └── utils/               # 工具模块
│       ├── logger.py        # 日志系统
│       ├── metrics.py       # 性能指标
│       └── image_utils.py   # 图像处理
├── tests/                   # 测试
│   ├── unit/                # 单元测试
│   └── integration/         # 集成测试
├── examples/                # 示例
│   └── quickstart.py        # 快速开始
├── setup.py                 # 安装配置
└── requirements.txt         # 依赖

```

## 快速开始

### 1. 安装依赖

```bash
cd refactored

# 安装基础依赖
pip install -r requirements.txt

# （可选）开发依赖
pip install -e ".[dev]"

# （可选）API 依赖
pip install -e ".[api]"
```

### 2. 配置系统

编辑 `config/base_config.yaml`:

```yaml
model:
  smolvlm:
    backend: "mlx"  # or "transformers"
    max_tokens: 100
    temperature: 0.6

detectors:
  default: "yolov10"
  yolov10:
    model_path: "../yolov10n.pt"  # 指向原项目的模型
```

### 3. 运行示例

```bash
python examples/quickstart.py
```

## 使用示例

### 基础使用

```python
from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem

# 加载配置
config = get_config()

# 初始化系统
system = AntiDroneSystem(config.config)

# 执行威胁评估
result = system.process_frame("path/to/image.jpg")

print(f"Threat Level: {result.threat_level.value}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Scene: {result.scene_description}")
```

### 自定义配置

```python
from core.smolvlm import SmolVLM

# 自定义 VLM 配置
vlm_config = {
    'name': 'mlx-community/SmolVLM-Instruct-bf16',
    'backend': 'mlx',
    'max_tokens': 120,
    'temperature': 0.7
}

vlm = SmolVLM(vlm_config)
response = vlm.inference("image.jpg", "<image>Describe this scene")
```

### 使用检测器

```python
from detectors.detector_factory import DetectorFactory

# 创建 YOLO 检测器
detector_config = {
    'model_path': 'yolov10n.pt',
    'conf_threshold': 0.25,
    'device': 'mps'
}

detector = DetectorFactory.create_detector('yolov10', detector_config)
detections = detector.detect("image.jpg")

for det in detections:
    print(f"{det.class_name}: {det.confidence:.2f}")
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/

# 查看覆盖率
open htmlcov/index.html
```

## 性能指标

在 **MacBook Pro M4 Pro (24GB RAM)** 上的性能:

| 指标 | 值 |
|------|---|
| 推理速度 | 61 tokens/s (bf16) |
| 内存占用 | 5.5 GB |
| 检测延迟 | < 50ms |
| 端到端延迟 | 150-200ms |

## 配置选项

### 模型配置

```yaml
model:
  smolvlm:
    name: "mlx-community/SmolVLM-Instruct-bf16"
    backend: "mlx"  # mlx or transformers
    device: "mps"   # mps, cuda, cpu
    max_tokens: 100
    temperature: 0.6
    repetition_penalty: 1.2
```

### 检测器配置

```yaml
detectors:
  yolov10:
    model_path: "yolov10n.pt"
    conf_threshold: 0.25
    iou_threshold: 0.45
    device: "mps"
```

### 反无人机配置

```yaml
anti_drone:
  threat_levels:
    low: 0.3
    medium: 0.5
    high: 0.7
    critical: 0.9
  frame_skip: 5
  batch_size: 4
```

## 架构设计

### 分层架构

```
应用层 (Anti-Drone System)
    ↓
理解层 (SmolVLM)
    ↓
检测层 (YOLO/SAM)
    ↓
数据层 (Image Utils)
```

### 设计模式

- **工厂模式** - DetectorFactory 动态创建检测器
- **策略模式** - 多种检测模型可选
- **单例模式** - 全局配置和指标追踪器
- **模板方法** - 基类定义流程，子类实现细节

## 扩展指南

### 添加新的检测器

```python
from detectors.base_detector import BaseDetector, DetectionResult

class MyDetector(BaseDetector):
    def load_model(self):
        # 加载你的模型
        pass

    def _detect_impl(self, image, **kwargs):
        # 实现检测逻辑
        return detections

# 注册检测器
DetectorFactory.register_detector('my_detector', MyDetector)
```

### 添加新的 VLM

```python
from core.base_model import BaseVisionLanguageModel

class MyVLM(BaseVisionLanguageModel):
    def load_model(self):
        # 加载模型
        pass

    def _inference_impl(self, image, prompt, **kwargs):
        # 实现推理
        return output
```

## 与原项目的对比

| 方面 | 原项目 | 重构版 |
|------|--------|--------|
| 代码结构 | 文件分散 | 模块化清晰 |
| 配置管理 | 硬编码 | YAML 配置文件 |
| 日志系统 | print 语句 | 统一日志框架 |
| 错误处理 | 基础 | 完善的异常处理 |
| 性能监控 | 无 | 内置指标追踪 |
| 测试覆盖 | 0% | 单元测试框架 |
| 可维护性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 迁移指南

从原项目迁移到重构版:

```python
# 原代码
from smolvlm_demo import SmolVLMDemo
model = SmolVLMDemo()
result = model.inference("image.jpg", "Describe")

# 重构版
from core.config_loader import get_config
from core.smolvlm import SmolVLM

config = get_config()
model = SmolVLM(config.get_model_config()['smolvlm'])
result = model.inference("image.jpg", "<image>Describe")
```

## 常见问题

### Q: 如何切换后端（MLX vs Transformers）？

A: 在 `config/base_config.yaml` 中修改:

```yaml
model:
  smolvlm:
    backend: "transformers"  # 从 "mlx" 改为 "transformers"
```

### Q: 如何使用自己的模型？

A: 修改配置文件中的 model_path:

```yaml
detectors:
  yolov10:
    model_path: "/path/to/your/model.pt"
```

### Q: 性能如何优化？

A: 参考以下优化:
1. 使用 MLX 后端（Apple Silicon）
2. 降低 max_tokens
3. 增加 frame_skip（视频处理）
4. 启用模型量化（即将支持）

## 贡献指南

欢迎贡献！请遵循以下步骤:

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目主页: [GitHub](https://github.com/yourusername/smolvlm-anti-drone)
- 问题反馈: [Issues](https://github.com/yourusername/smolvlm-anti-drone/issues)

## 致谢

- [SmolVLM](https://huggingface.co/HuggingFaceTB/SmolVLM-Instruct) - Hugging Face 团队
- [MLX](https://github.com/ml-explore/mlx) - Apple ML Research
- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLOv8/v10

---

**⭐ 如果这个项目对您有帮助，请给一个 Star！**
