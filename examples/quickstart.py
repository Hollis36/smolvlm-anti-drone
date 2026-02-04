#!/usr/bin/env python3
"""
快速开始示例 - 重构后的反无人机系统
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem


def main():
    """主函数"""
    print("=" * 60)
    print("SmolVLM Anti-Drone System - Quickstart")
    print("=" * 60)

    # 1. 加载配置
    print("\n[1/3] Loading configuration...")
    config = get_config()
    print("✓ Configuration loaded")

    # 2. 初始化系统
    print("\n[2/3] Initializing Anti-Drone System...")
    system = AntiDroneSystem(config.config)
    print("✓ System initialized successfully")

    # 3. 测试示例图像
    print("\n[3/3] Running test analysis...")

    # 示例图像 URL
    test_image = "https://huggingface.co/spaces/HuggingFaceTB/SmolVLM/resolve/main/examples/dog.jpg"

    # 执行威胁评估
    result = system.quick_scan(test_image)

    # 显示结果
    print("\n" + "=" * 60)
    print("THREAT ASSESSMENT RESULTS")
    print("=" * 60)

    print(f"\n🎯 Threat Level: {result.threat_level.value}")
    print(f"📊 Confidence: {result.confidence:.2f}")
    print(f"🔍 Detections: {len(result.detections)} objects")

    print(f"\n📝 Scene Description:")
    print(result.scene_description)

    print(f"\n💡 Recommended Action:")
    print(result.recommended_action)

    print(f"\n⚡ Processing Time: {result.processing_time_ms:.2f} ms")

    # 显示检测详情
    if result.detections:
        print(f"\n🎯 Detection Details:")
        for i, det in enumerate(result.detections, 1):
            print(f"  {i}. {det.class_name} (confidence: {det.confidence:.2f})")

    # 显示性能指标
    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS")
    print("=" * 60)

    metrics = system.get_metrics_summary()

    if 'detection_time' in metrics:
        det_time = metrics['detection_time']
        print(f"\nDetection Time:")
        print(f"  Mean: {det_time['mean']*1000:.2f} ms")
        print(f"  Min/Max: {det_time['min']*1000:.2f} / {det_time['max']*1000:.2f} ms")

    if 'scene_analysis' in metrics:
        analysis_time = metrics['scene_analysis']
        print(f"\nScene Analysis Time:")
        print(f"  Mean: {analysis_time['mean']*1000:.2f} ms")

    if 'frames_processed' in metrics.get('counters', {}):
        print(f"\nFrames Processed: {metrics['counters']['frames_processed']}")

    print("\n✅ Quickstart completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
