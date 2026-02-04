#!/usr/bin/env python3
"""
视频处理示例
"""

import sys
from pathlib import Path
import argparse

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem
from applications.video_processor import VideoProcessor


def process_video_file(video_path: str, output_path: str):
    """处理视频文件"""
    print("=" * 60)
    print("Video File Processing Example")
    print("=" * 60)

    # 1. 初始化系统
    print("\n[1/3] Initializing system...")
    config = get_config()
    anti_drone = AntiDroneSystem(config.config)
    print("✓ System initialized")

    # 2. 创建视频处理器
    print("\n[2/3] Creating video processor...")
    processor = VideoProcessor(
        anti_drone_system=anti_drone,
        frame_skip=5  # 处理每 5 帧
    )
    print("✓ Video processor created")

    # 3. 处理视频
    print(f"\n[3/3] Processing video: {video_path}")
    results = processor.process_video_file(
        video_path=video_path,
        output_path=output_path,
        draw_results=True
    )

    # 显示统计
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)

    print(f"\nTotal frames analyzed: {len(results)}")

    # 威胁等级统计
    threat_counts = {}
    for result in results:
        level = result.threat_level.value
        threat_counts[level] = threat_counts.get(level, 0) + 1

    print("\nThreat Level Distribution:")
    for level, count in sorted(threat_counts.items()):
        percentage = (count / len(results)) * 100
        print(f"  {level}: {count} ({percentage:.1f}%)")

    # 平均处理时间
    avg_time = sum(r.processing_time_ms for r in results) / len(results)
    print(f"\nAverage processing time: {avg_time:.2f} ms per frame")

    # 性能指标
    metrics = processor.get_metrics_summary()
    if 'frame_processing' in metrics:
        frame_time = metrics['frame_processing']
        print(f"\nFrame processing statistics:")
        print(f"  Mean: {frame_time['mean']*1000:.2f} ms")
        print(f"  Min: {frame_time['min']*1000:.2f} ms")
        print(f"  Max: {frame_time['max']*1000:.2f} ms")
        print(f"  P95: {frame_time['p95']*1000:.2f} ms")

    if output_path:
        print(f"\n✓ Annotated video saved to: {output_path}")

    print("\n✅ Video processing complete!")


def process_realtime_stream(source: int = 0, duration: int = 30):
    """处理实时视频流"""
    print("=" * 60)
    print("Realtime Stream Processing Example")
    print("=" * 60)

    # 1. 初始化系统
    print("\n[1/3] Initializing system...")
    config = get_config()
    anti_drone = AntiDroneSystem(config.config)
    print("✓ System initialized")

    # 2. 创建视频处理器
    print("\n[2/3] Creating video processor...")
    processor = VideoProcessor(
        anti_drone_system=anti_drone,
        frame_skip=10  # 实时流可以跳更多帧
    )
    print("✓ Video processor created")

    # 3. 定义回调函数
    def on_result(frame_count, frame, result):
        """结果回调"""
        print(
            f"Frame {frame_count}: {result.threat_level.value} "
            f"(confidence: {result.confidence:.2f}, "
            f"detections: {len(result.detections)})"
        )

    # 4. 启动实时流
    print(f"\n[3/3] Starting realtime stream (source: {source}, duration: {duration}s)")
    print("Press Ctrl+C to stop early...\n")

    processor.start_realtime_stream(source=source, callback=on_result)

    try:
        import time
        time.sleep(duration)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    # 停止流
    processor.stop_realtime_stream()

    # 显示统计
    print("\n" + "=" * 60)
    print("STREAMING SUMMARY")
    print("=" * 60)

    results = processor.get_results(max_results=100)
    print(f"\nProcessed {len(results)} frames")

    if results:
        # 威胁等级分布
        threat_counts = {}
        for result in results:
            level = result.threat_level.value
            threat_counts[level] = threat_counts.get(level, 0) + 1

        print("\nThreat Level Distribution:")
        for level, count in sorted(threat_counts.items()):
            percentage = (count / len(results)) * 100
            print(f"  {level}: {count} ({percentage:.1f}%)")

    # 性能指标
    metrics = processor.get_metrics_summary()
    if 'realtime_processing' in metrics:
        rt_time = metrics['realtime_processing']
        print(f"\nRealtime processing statistics:")
        print(f"  Mean: {rt_time['mean']*1000:.2f} ms")
        print(f"  P95: {rt_time['p95']*1000:.2f} ms")

    print("\n✅ Stream processing complete!")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Video Processing Examples")
    subparsers = parser.add_subparsers(dest='mode', help='Processing mode')

    # 视频文件模式
    file_parser = subparsers.add_parser('file', help='Process video file')
    file_parser.add_argument('input', help='Input video file path')
    file_parser.add_argument('--output', '-o', help='Output video file path')

    # 实时流模式
    stream_parser = subparsers.add_parser('stream', help='Process realtime stream')
    stream_parser.add_argument('--source', '-s', type=int, default=0, help='Video source (default: 0)')
    stream_parser.add_argument('--duration', '-d', type=int, default=30, help='Duration in seconds (default: 30)')

    args = parser.parse_args()

    if args.mode == 'file':
        if not args.output:
            # 自动生成输出文件名
            input_path = Path(args.input)
            args.output = str(input_path.parent / f"{input_path.stem}_annotated.mp4")

        process_video_file(args.input, args.output)

    elif args.mode == 'stream':
        process_realtime_stream(args.source, args.duration)

    else:
        parser.print_help()


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
