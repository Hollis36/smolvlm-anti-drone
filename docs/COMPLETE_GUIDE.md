# SmolVLM Anti-Drone System - 完整使用指南

> 从零到生产的完整指南

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [详细配置](#详细配置)
4. [API 使用](#api-使用)
5. [批量处理](#批量处理)
6. [视频处理](#视频处理)
7. [性能优化](#性能优化)
8. [部署指南](#部署指南)
9. [故障排除](#故障排除)
10. [最佳实践](#最佳实践)

---

## 快速开始

### 安装

```bash
# 1. 克隆项目
cd refactored

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装项目（开发模式）
pip install -e ".[dev]"
```

### 5 分钟快速测试

```bash
# 运行快速开始示例
python examples/quickstart.py
```

预期输出：
```
=============================================================
SmolVLM Anti-Drone System - Quickstart
=============================================================

[1/3] Loading configuration...
✓ Configuration loaded

[2/3] Initializing Anti-Drone System...
✓ System initialized successfully

[3/3] Running test analysis...

=============================================================
THREAT ASSESSMENT RESULTS
=============================================================

🎯 Threat Level: LOW
📊 Confidence: 0.85
🔍 Detections: 1 objects
...
```

---

## 核心概念

### 1. 系统架构

```
┌─────────────────────────────────────────┐
│         Anti-Drone System               │
│  ┌──────────────────────────────────┐   │
│  │   SmolVLM (Scene Understanding)  │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │   Detector (Object Detection)    │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │   Threat Assessment Logic        │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
           ↓
    ThreatAssessment
```

### 2. 核心组件

#### SmolVLM
- **功能**: 视觉-语言理解
- **输入**: 图像 + 文本提示
- **输出**: 场景描述
- **后端**: MLX (Apple Silicon) 或 Transformers

#### Detector
- **功能**: 目标检测
- **支持**: YOLOv8/v10, SAM, Grounding DINO
- **输出**: DetectionResult 列表

#### AntiDroneSystem
- **功能**: 综合威胁评估
- **流程**: 检测 → 理解 → 评估 → 建议

### 3. 数据类型

```python
@dataclass
class DetectionResult:
    bbox: Tuple[float, float, float, float]
    confidence: float
    class_name: str
    class_id: int

@dataclass
class ThreatAssessment:
    threat_level: ThreatLevel  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float
    detections: List[DetectionResult]
    scene_description: str
    recommended_action: str
    processing_time_ms: float
```

---

## 详细配置

### 配置文件结构

`config/base_config.yaml`:

```yaml
# 模型配置
model:
  smolvlm:
    name: "mlx-community/SmolVLM-Instruct-bf16"
    backend: "mlx"  # mlx or transformers
    device: "mps"   # mps, cuda, cpu
    max_tokens: 100
    temperature: 0.6
    repetition_penalty: 1.2

# 检测器配置
detectors:
  default: "yolov10"
  yolov10:
    model_path: "yolov10n.pt"
    conf_threshold: 0.25
    iou_threshold: 0.45

# 反无人机配置
anti_drone:
  threat_levels:
    low: 0.3
    medium: 0.5
    high: 0.7
    critical: 0.9
  frame_skip: 5
  batch_size: 4
```

### 环境变量覆盖

```bash
# 覆盖后端
export SMOLVLM_MODEL_BACKEND=transformers

# 覆盖设备
export SMOLVLM_MODEL_DEVICE=cuda

# 覆盖日志级别
export SMOLVLM_LOGGING_LEVEL=DEBUG
```

### 程序化配置

```python
from core.smolvlm import SmolVLM

# 自定义配置
config = {
    'name': 'mlx-community/SmolVLM-Instruct-bf16',
    'backend': 'mlx',
    'max_tokens': 150,
    'temperature': 0.7
}

vlm = SmolVLM(config)
```

---

## API 使用

### 启动 API 服务器

```bash
# 方式 1: 直接运行
python -m src.api.rest_api

# 方式 2: 使用 uvicorn
uvicorn src.api.rest_api:app --host 0.0.0.0 --port 8000 --reload

# 方式 3: Docker
docker-compose up -d api
```

### API 端点

#### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

响应：
```json
{
  "status": "healthy",
  "model_loaded": true,
  "detector_loaded": true,
  "uptime_seconds": 123.45
}
```

#### 2. 分析图像（文件上传）

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@image.jpg"
```

响应：
```json
{
  "threat_level": "MEDIUM",
  "confidence": 0.75,
  "scene_description": "...",
  "recommended_action": "...",
  "processing_time_ms": 234.56,
  "num_detections": 2,
  "detections": [...]
}
```

#### 3. 分析图像（URL）

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/url?url=https://example.com/image.jpg"
```

#### 4. 获取性能指标

```bash
curl http://localhost:8000/api/v1/metrics
```

### Python 客户端

```python
import requests

# 上传文件
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/analyze',
        files={'file': f}
    )

result = response.json()
print(f"Threat Level: {result['threat_level']}")

# 使用 URL
response = requests.post(
    'http://localhost:8000/api/v1/analyze/url',
    params={'url': 'https://example.com/image.jpg'}
)
```

### JavaScript 客户端

```javascript
// 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Threat Level:', result.threat_level);
```

---

## 批量处理

### 批量处理图像

```bash
python examples/batch_processing_example.py process \
  /path/to/images \
  /path/to/output \
  --no-annotations  # 可选：跳过标注图像
```

### 生成报告

```bash
python examples/batch_processing_example.py report \
  /path/to/output/results.json \
  --output summary_report.md
```

### 编程方式

```python
from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem
from pathlib import Path

config = get_config()
system = AntiDroneSystem(config.config)

image_dir = Path('/path/to/images')
results = []

for image_file in image_dir.glob('*.jpg'):
    result = system.process_frame(str(image_file))
    results.append(result)

    print(f"{image_file.name}: {result.threat_level.value}")
```

---

## 视频处理

### 处理视频文件

```bash
python examples/video_processing_example.py file \
  input_video.mp4 \
  --output output_video.mp4
```

### 实时流处理

```bash
# 默认摄像头
python examples/video_processing_example.py stream

# 指定源和时长
python examples/video_processing_example.py stream \
  --source 0 \
  --duration 60
```

### 编程方式

```python
from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem
from applications.video_processor import VideoProcessor

config = get_config()
system = AntiDroneSystem(config.config)
processor = VideoProcessor(system, frame_skip=5)

# 处理视频文件
results = processor.process_video_file(
    'input.mp4',
    output_path='output.mp4',
    draw_results=True
)

print(f"Processed {len(results)} frames")
```

---

## 性能优化

### 1. 模型量化（即将支持）

```python
# 4-bit 量化
config = {
    'name': 'mlx-community/SmolVLM-Instruct-bf16',
    'backend': 'mlx',
    'quantization': {
        'enabled': True,
        'bits': 4
    }
}
```

**预期提升**:
- 速度: 2-2.5x
- 内存: 50-60% ↓

### 2. 批处理

```python
# 批量推理
images = ['img1.jpg', 'img2.jpg', 'img3.jpg']
prompts = ['<image>Describe'] * 3

results = vlm.batch_inference(images, prompts, batch_size=8)
```

### 3. 缓存

```yaml
# config/base_config.yaml
performance:
  cache:
    enabled: true
    cache_dir: ".cache/inference"
    max_size_mb: 1024
```

### 4. 跳帧处理（视频）

```python
# 每 10 帧处理一次
processor = VideoProcessor(system, frame_skip=10)
```

### 5. 调整参数

```yaml
model:
  smolvlm:
    max_tokens: 80  # 减少生成长度
    temperature: 0.5  # 降低随机性
```

---

## 部署指南

### Docker 部署

```bash
# 1. 构建镜像
docker build -t anti-drone:latest -f docker/Dockerfile .

# 2. 运行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --name anti-drone-api \
  anti-drone:latest

# 3. 查看日志
docker logs -f anti-drone-api
```

### Docker Compose 部署

```bash
# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 查看状态
docker-compose -f docker/docker-compose.yml ps

# 停止服务
docker-compose -f docker/docker-compose.yml down
```

### 生产环境配置

```yaml
# config/production_config.yaml
logging:
  level: "INFO"
  file:
    enabled: true
    path: "/var/log/anti-drone/app.log"

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors:
    enabled: true
    allow_origins: ["https://yourdomain.com"]

performance:
  cache:
    enabled: true
  batch_processing:
    enabled: true
    batch_size: 8
```

---

## 故障排除

### 问题 1: 模型加载失败

**错误**: `Failed to load model: ...`

**解决方案**:
```bash
# 清除缓存
rm -rf ~/.cache/huggingface

# 手动下载模型
python -c "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/SmolVLM-Instruct-bf16')"
```

### 问题 2: 内存不足

**错误**: `Out of memory`

**解决方案**:
1. 减少 `max_tokens`
2. 增加 `frame_skip`（视频处理）
3. 减少 `batch_size`
4. 启用模型量化（即将支持）

### 问题 3: 推理速度慢

**解决方案**:
1. 使用 MLX 后端（Apple Silicon）
2. 启用批处理
3. 调整 `frame_skip`
4. 减少 `max_tokens`

### 问题 4: API 返回 503

**错误**: `System not initialized`

**解决方案**:
```bash
# 检查日志
docker logs anti-drone-api

# 重启服务
docker restart anti-drone-api
```

---

## 最佳实践

### 1. 配置管理

✅ **推荐**:
```python
# 使用配置文件
config = get_config()
system = AntiDroneSystem(config.config)
```

❌ **不推荐**:
```python
# 硬编码配置
system = AntiDroneSystem({
    'model': {...},  # 难以维护
    'detectors': {...}
})
```

### 2. 错误处理

✅ **推荐**:
```python
try:
    result = system.process_frame(image)
except Exception as e:
    logger.error(f"Processing failed: {e}")
    # 降级处理
    result = create_default_result()
```

### 3. 性能监控

✅ **推荐**:
```python
# 定期检查指标
metrics = system.get_metrics_summary()

if metrics.get('processing_time_ms', {}).get('mean', 0) > 500:
    logger.warning("Processing time exceeds threshold")
```

### 4. 资源清理

✅ **推荐**:
```python
# 使用上下文管理器
with VideoProcessor(system) as processor:
    processor.process_video_file('input.mp4')
# 自动清理
```

### 5. 日志记录

✅ **推荐**:
```python
logger.info("Processing started")
logger.debug(f"Image size: {image.size}")
logger.error("Processing failed", exc_info=True)
```

---

## 高级主题

### 自定义检测器

```python
from detectors.base_detector import BaseDetector, DetectionResult

class MyCustomDetector(BaseDetector):
    def load_model(self):
        # 加载你的模型
        self.model = ...

    def _detect_impl(self, image, **kwargs):
        # 实现检测逻辑
        results = []
        # ... 处理 ...
        return results

# 注册
DetectorFactory.register_detector('my_detector', MyCustomDetector)
```

### 自定义威胁评估

```python
from applications.anti_drone import AntiDroneSystem, ThreatLevel

class CustomAntiDroneSystem(AntiDroneSystem):
    def _assess_threat(self, detections, scene_description):
        # 自定义逻辑
        if 'weapon' in scene_description.lower():
            return ThreatLevel.CRITICAL, 0.95
        # ... 其他逻辑 ...
        return super()._assess_threat(detections, scene_description)
```

---

## 附录

### A. 配置参数完整列表

见 [config/base_config.yaml](../config/base_config.yaml)

### B. API 端点完整列表

见 [API 文档](API.md)

### C. 性能基准测试

见 [BENCHMARKS.md](BENCHMARKS.md)

### D. 贡献指南

见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

**需要更多帮助？**
- 📧 联系: your.email@example.com
- 🐛 问题: https://github.com/yourusername/smolvlm-anti-drone/issues
- 📚 文档: https://github.com/yourusername/smolvlm-anti-drone/wiki
