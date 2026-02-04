# 迁移指南 - 从原项目到重构版

本指南帮助您从原项目平滑迁移到重构后的版本。

## 目录

1. [整体对比](#整体对比)
2. [API 变更](#api-变更)
3. [配置迁移](#配置迁移)
4. [代码示例对比](#代码示例对比)
5. [逐步迁移](#逐步迁移)

---

## 整体对比

### 目录结构对比

**原项目**:
```
hugging——demo1/
├── smolvlm_demo.py
├── examples/anti_drone_optimized.py
├── advanced_detectors.py
└── ... (各种脚本分散)
```

**重构版**:
```
refactored/
├── config/                 # 新增：配置文件
├── src/                    # 新增：统一源代码目录
│   ├── core/
│   ├── detectors/
│   ├── applications/
│   └── utils/
├── tests/                  # 新增：测试框架
└── examples/
```

---

## API 变更

### 1. SmolVLM 使用

#### 原代码
```python
from smolvlm_demo import SmolVLMDemo

model = SmolVLMDemo("HuggingFaceTB/SmolVLM-Instruct")
result = model.inference("image.jpg", "Describe this image")
```

#### 重构版
```python
from core.config_loader import get_config
from core.smolvlm import SmolVLM

config = get_config()
model = SmolVLM(config.get_model_config()['smolvlm'])
result = model.inference("image.jpg", "<image>Describe this image")
```

**主要变更**:
- ✅ 统一配置管理
- ✅ 自动日志记录
- ✅ 内置性能监控
- ✅ 更好的错误处理

### 2. 反无人机系统

#### 原代码
```python
from examples.anti_drone_optimized import OptimizedAntiDroneSystem

system = OptimizedAntiDroneSystem()
system.analyze_threat("image.jpg", "drone detection")
```

#### 重构版
```python
from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem

config = get_config()
system = AntiDroneSystem(config.config)
result = system.process_frame("image.jpg")

# 获取详细信息
print(result.threat_level.value)
print(result.scene_description)
print(result.recommended_action)
```

**主要变更**:
- ✅ 返回结构化数据（ThreatAssessment）
- ✅ 统一的威胁等级枚举
- ✅ 自动性能追踪
- ✅ 更清晰的 API

### 3. 目标检测

#### 原代码
```python
from advanced_detectors import detect_with_yolov10

results = detect_with_yolov10("image.jpg")
```

#### 重构版
```python
from detectors.detector_factory import DetectorFactory

config = {
    'model_path': 'yolov10n.pt',
    'conf_threshold': 0.25,
    'device': 'mps'
}

detector = DetectorFactory.create_detector('yolov10', config)
results = detector.detect("image.jpg")

# 使用结构化的 DetectionResult
for det in results:
    print(f"{det.class_name}: {det.confidence:.2f}")
    print(f"BBox: {det.bbox}")
```

**主要变更**:
- ✅ 工厂模式创建检测器
- ✅ 统一的 DetectionResult 数据类
- ✅ 更好的类型提示
- ✅ 内置 NMS 和过滤

---

## 配置迁移

### 从硬编码到配置文件

#### 原代码（硬编码）
```python
class SmolVLMDemo:
    def __init__(self):
        self.model_name = "HuggingFaceTB/SmolVLM-Instruct"  # 硬编码
        self.max_tokens = 200  # 硬编码
        self.temperature = 0.6  # 硬编码
```

#### 重构版（配置文件）

创建 `config/base_config.yaml`:
```yaml
model:
  smolvlm:
    name: "mlx-community/SmolVLM-Instruct-bf16"
    max_tokens: 100
    temperature: 0.6
    repetition_penalty: 1.2
```

代码中使用:
```python
from core.config_loader import get_config

config = get_config()
# 所有配置从文件读取
```

**优势**:
- ✅ 无需修改代码即可调整参数
- ✅ 支持环境变量覆盖
- ✅ 配置版本控制
- ✅ 多环境配置（开发、生产）

---

## 代码示例对比

### 示例 1: 基础图像分析

#### 原代码
```python
from smolvlm_demo import SmolVLMDemo
from PIL import Image

model = SmolVLMDemo()
image = Image.open("test.jpg")
result = model.inference(image, "What do you see?", max_tokens=150)
print(result)
```

#### 重构版
```python
from core.config_loader import get_config
from core.smolvlm import SmolVLM

config = get_config()
vlm = SmolVLM(config.get_model_config()['smolvlm'])

# 更简洁 - 自动加载图像
result = vlm.visual_qa("test.jpg", "What do you see?")
print(result)

# 获取性能指标
metrics = vlm.get_metrics_summary()
print(f"Average inference time: {metrics['inference_time']['mean']:.2f}s")
```

### 示例 2: 批量处理

#### 原代码
```python
images = ["img1.jpg", "img2.jpg", "img3.jpg"]
results = []

for img in images:
    result = model.inference(img, "Describe")
    results.append(result)
```

#### 重构版
```python
images = ["img1.jpg", "img2.jpg", "img3.jpg"]
prompts = ["<image>Describe this image"] * 3

# 自动批处理和性能追踪
results = vlm.batch_inference(images, prompts, batch_size=4)

# 查看性能
print(f"Batch processing time: {vlm.metrics.get_latest('batch_inference_time')[0]:.2f}s")
```

### 示例 3: 威胁检测

#### 原代码
```python
from examples.anti_drone_optimized import OptimizedAntiDroneSystem

system = OptimizedAntiDroneSystem()

# 分散的方法
scene = system.scene_description("image.jpg")
threat = system.analyze_threat("image.jpg")
scan = system.quick_scan("image.jpg")
```

#### 重构版
```python
from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem

config = get_config()
system = AntiDroneSystem(config.config)

# 统一的接口
result = system.process_frame("image.jpg")

# 结构化的结果
print(f"Level: {result.threat_level.value}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Detections: {len(result.detections)}")
print(f"Scene: {result.scene_description}")
print(f"Action: {result.recommended_action}")
print(f"Time: {result.processing_time_ms:.2f}ms")

# 转换为字典（方便序列化）
result_dict = result.to_dict()
```

---

## 逐步迁移

### 步骤 1: 安装重构版

```bash
cd refactored
pip install -r requirements.txt
```

### 步骤 2: 复制模型文件

```bash
# 复制 YOLO 模型
cp ../yolov10n.pt ./models/

# 或在配置中指向原路径
```

编辑 `config/base_config.yaml`:
```yaml
detectors:
  yolov10:
    model_path: "../yolov10n.pt"  # 指向原项目
```

### 步骤 3: 测试配置

```bash
python examples/quickstart.py
```

### 步骤 4: 迁移自定义代码

#### 如果您有自定义的推理逻辑

**原代码** (`my_custom_script.py`):
```python
from smolvlm_demo import SmolVLMDemo

model = SmolVLMDemo()

def my_analysis(image_path):
    result = model.inference(image_path, "My prompt")
    # 自定义处理
    return process(result)
```

**迁移到重构版**:
```python
from core.config_loader import get_config
from core.smolvlm import SmolVLM

config = get_config()
model = SmolVLM(config.get_model_config()['smolvlm'])

def my_analysis(image_path):
    result = model.inference(image_path, "<image>My prompt")
    # 自定义处理（逻辑不变）
    return process(result)
```

#### 如果您有自定义的检测器

**原代码**:
```python
from advanced_detectors import detect_with_yolov10

detections = detect_with_yolov10("image.jpg")
```

**迁移到重构版**:
```python
from detectors.detector_factory import DetectorFactory

detector = DetectorFactory.create_detector('yolov10', {
    'model_path': 'yolov10n.pt',
    'conf_threshold': 0.25
})

detections = detector.detect("image.jpg")

# 如果需要与原格式兼容
detections_dict = [d.to_dict() for d in detections]
```

### 步骤 5: 添加日志和监控

重构版自动添加了日志和性能监控：

```python
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Processing started")
logger.debug(f"Image size: {image.size}")
logger.error("An error occurred")

# 查看性能
from applications.anti_drone import AntiDroneSystem

system = AntiDroneSystem(config.config)
result = system.process_frame("image.jpg")

metrics = system.get_metrics_summary()
print(metrics)
```

---

## 兼容性层（可选）

如果您想保持与原 API 的兼容性，可以创建适配器：

```python
# compat/legacy_api.py

from core.config_loader import get_config
from core.smolvlm import SmolVLM as NewSmolVLM

class SmolVLMDemo:
    """向后兼容的包装器"""

    def __init__(self, model_name=None):
        config = get_config()
        vlm_config = config.get_model_config()['smolvlm']

        if model_name:
            vlm_config['name'] = model_name

        self._model = NewSmolVLM(vlm_config)

    def inference(self, image, prompt, max_tokens=200):
        """兼容旧 API"""
        # 自动添加 <image> 标签
        if not prompt.startswith('<image>'):
            prompt = f"<image>{prompt}"

        return self._model.inference(image, prompt, max_tokens=max_tokens)
```

使用兼容层：
```python
# 原代码无需修改！
from compat.legacy_api import SmolVLMDemo

model = SmolVLMDemo()
result = model.inference("image.jpg", "Describe")
```

---

## 常见问题

### Q: 性能会下降吗？

A: **不会**。重构版在保持性能的同时增加了以下功能：
- 自动性能监控（可禁用）
- 更好的错误处理
- 统一的日志系统

实际上，通过批处理优化和配置调优，性能可能会**提升**。

### Q: 必须使用配置文件吗？

A: 不是必须的。您可以直接传递配置字典：

```python
from core.smolvlm import SmolVLM

vlm = SmolVLM({
    'name': 'mlx-community/SmolVLM-Instruct-bf16',
    'backend': 'mlx',
    'max_tokens': 100
})
```

### Q: 如何禁用日志？

A: 在配置中设置：

```yaml
logging:
  level: "ERROR"  # 只显示错误
  console:
    enabled: false  # 禁用控制台输出
```

或代码中：
```python
import logging
logging.getLogger('applications').setLevel(logging.ERROR)
```

### Q: 原项目的数据集和实验结果还能用吗？

A: **完全兼容**。重构版可以读取原项目的所有数据和模型：

```yaml
# config/base_config.yaml
dataset:
  anti_uav:
    data_dir: "../data/train"  # 指向原项目
    rgb_dir: "../data/train/new2_train"

detectors:
  yolov10:
    model_path: "../yolov10n.pt"  # 使用原模型
```

---

## 下一步

迁移完成后，建议：

1. **运行测试** - `pytest tests/` 确保一切正常
2. **阅读文档** - 查看 [README.md](README.md) 了解新功能
3. **探索示例** - `examples/` 目录有更多用法
4. **性能调优** - 根据需求调整 `config/base_config.yaml`

---

**需要帮助？**
- 提交 [Issue](https://github.com/yourusername/smolvlm-anti-drone/issues)
- 查看 [FAQ](docs/FAQ.md)
- 阅读 [API 文档](docs/API.md)
