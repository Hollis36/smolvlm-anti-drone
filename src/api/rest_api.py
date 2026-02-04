"""
REST API 服务
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from PIL import Image
import io
import time

from ..core.config_loader import get_config
from ..applications.anti_drone import AntiDroneSystem, ThreatLevel
from ..utils.logger import get_logger


# Pydantic 模型
class ThreatAssessmentResponse(BaseModel):
    """威胁评估响应"""
    threat_level: str
    confidence: float
    scene_description: str
    recommended_action: str
    processing_time_ms: float
    num_detections: int
    detections: List[dict] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    model_loaded: bool
    detector_loaded: bool
    uptime_seconds: float


class MetricsResponse(BaseModel):
    """性能指标响应"""
    total_requests: int
    total_errors: int
    average_processing_time_ms: float
    metrics: dict


# 创建 FastAPI 应用
app = FastAPI(
    title="SmolVLM Anti-Drone API",
    description="基于 SmolVLM 的反无人机检测系统 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局变量
anti_drone_system: Optional[AntiDroneSystem] = None
logger = get_logger(__name__)
startup_time = time.time()


# 依赖注入
def get_system() -> AntiDroneSystem:
    """获取系统实例"""
    if anti_drone_system is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    return anti_drone_system


# CORS 配置
def setup_cors(app: FastAPI, config: dict):
    """配置 CORS"""
    cors_config = config.get('api', {}).get('cors', {})

    if cors_config.get('enabled', True):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_config.get('allow_origins', ["*"]),
            allow_credentials=True,
            allow_methods=cors_config.get('allow_methods', ["*"]),
            allow_headers=cors_config.get('allow_headers', ["*"]),
        )


@app.on_event("startup")
async def startup_event():
    """启动时初始化系统"""
    global anti_drone_system, startup_time

    logger.info("Starting Anti-Drone API server...")

    try:
        # 加载配置
        config = get_config()

        # 设置 CORS
        setup_cors(app, config.config)

        # 初始化系统
        logger.info("Initializing Anti-Drone System...")
        anti_drone_system = AntiDroneSystem(config.config)

        startup_time = time.time()
        logger.info("✓ Anti-Drone API server started successfully")

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    logger.info("Shutting down Anti-Drone API server...")

    if anti_drone_system:
        # 显示最终指标
        metrics = anti_drone_system.get_metrics_summary()
        logger.info(f"Final metrics: {metrics}")

    logger.info("✓ Server shutdown complete")


# API 路由

@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "message": "SmolVLM Anti-Drone API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check(system: AntiDroneSystem = Depends(get_system)):
    """
    健康检查

    Returns:
        系统健康状态
    """
    uptime = time.time() - startup_time

    return HealthResponse(
        status="healthy",
        model_loaded=system.vlm.is_loaded,
        detector_loaded=system.detector.is_loaded,
        uptime_seconds=uptime
    )


@app.post("/api/v1/analyze", response_model=ThreatAssessmentResponse)
async def analyze_image(
    file: UploadFile = File(...),
    system: AntiDroneSystem = Depends(get_system)
):
    """
    分析上传的图像

    Args:
        file: 上传的图像文件

    Returns:
        威胁评估结果
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Expected image."
            )

        # 读取图像
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        logger.info(f"Processing image: {file.filename} ({image.size})")

        # 执行威胁评估
        result = system.process_frame(image)

        # 返回响应
        return ThreatAssessmentResponse(
            threat_level=result.threat_level.value,
            confidence=result.confidence,
            scene_description=result.scene_description,
            recommended_action=result.recommended_action,
            processing_time_ms=result.processing_time_ms,
            num_detections=len(result.detections),
            detections=[d.to_dict() for d in result.detections]
        )

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze/url")
async def analyze_image_url(
    url: str,
    system: AntiDroneSystem = Depends(get_system)
):
    """
    分析图像 URL

    Args:
        url: 图像 URL

    Returns:
        威胁评估结果
    """
    try:
        logger.info(f"Processing image from URL: {url}")

        # 执行威胁评估
        result = system.process_frame(url)

        return ThreatAssessmentResponse(
            threat_level=result.threat_level.value,
            confidence=result.confidence,
            scene_description=result.scene_description,
            recommended_action=result.recommended_action,
            processing_time_ms=result.processing_time_ms,
            num_detections=len(result.detections),
            detections=[d.to_dict() for d in result.detections]
        )

    except Exception as e:
        logger.error(f"Error processing image URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics(system: AntiDroneSystem = Depends(get_system)):
    """
    获取性能指标

    Returns:
        系统性能指标
    """
    try:
        metrics_summary = system.get_metrics_summary()

        # 提取关键指标
        counters = metrics_summary.get('counters', {})
        total_requests = counters.get('frames_processed', 0)
        total_errors = counters.get('processing_errors', 0)

        # 平均处理时间
        processing_time = metrics_summary.get('processing_time_ms', {})
        avg_time = processing_time.get('mean', 0)

        return MetricsResponse(
            total_requests=total_requests,
            total_errors=total_errors,
            average_processing_time_ms=avg_time,
            metrics=metrics_summary
        )

    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/metrics/reset")
async def reset_metrics(system: AntiDroneSystem = Depends(get_system)):
    """
    重置性能指标

    Returns:
        确认消息
    """
    try:
        system.reset_metrics()
        logger.info("Metrics reset")
        return {"message": "Metrics reset successfully"}

    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/threat-levels")
async def get_threat_levels():
    """
    获取威胁等级列表

    Returns:
        威胁等级枚举
    """
    return {
        "threat_levels": [level.value for level in ThreatLevel],
        "descriptions": {
            "LOW": "正常操作，维持意识",
            "MEDIUM": "提高警惕，持续监控",
            "HIGH": "高度警戒，准备反制措施",
            "CRITICAL": "立即行动，启动反制措施"
        }
    }


# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


def start_api(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1
):
    """
    启动 API 服务器

    Args:
        host: 监听地址
        port: 端口
        reload: 是否启用自动重载（开发模式）
        workers: 工作进程数
    """
    uvicorn.run(
        "api.rest_api:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level="info"
    )


if __name__ == "__main__":
    # 开发模式启动
    start_api(reload=True)
