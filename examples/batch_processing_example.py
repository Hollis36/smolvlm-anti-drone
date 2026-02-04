#!/usr/bin/env python3
"""
批量处理示例
"""

import sys
from pathlib import Path
import argparse
from tqdm import tqdm
import json

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.config_loader import get_config
from applications.anti_drone import AntiDroneSystem
from utils.visualization import Visualizer


def batch_process_images(
    image_dir: str,
    output_dir: str,
    save_annotations: bool = True,
    save_json: bool = True
):
    """批量处理图像"""
    print("=" * 60)
    print("Batch Image Processing")
    print("=" * 60)

    # 1. 初始化系统
    print("\n[1/4] Initializing system...")
    config = get_config()
    system = AntiDroneSystem(config.config)
    visualizer = Visualizer()
    print("✓ System initialized")

    # 2. 查找图像文件
    print(f"\n[2/4] Scanning directory: {image_dir}")
    image_dir = Path(image_dir)
    image_files = []

    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
        image_files.extend(list(image_dir.glob(ext)))

    print(f"✓ Found {len(image_files)} images")

    if len(image_files) == 0:
        print("No images found. Exiting.")
        return

    # 3. 创建输出目录
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if save_annotations:
        annotations_dir = output_dir / "annotations"
        annotations_dir.mkdir(exist_ok=True)

    # 4. 批量处理
    print(f"\n[3/4] Processing {len(image_files)} images...")

    results = []

    for image_file in tqdm(image_files, desc="Processing"):
        try:
            # 执行威胁评估
            result = system.process_frame(str(image_file))

            # 保存结果
            result_data = {
                'filename': image_file.name,
                'threat_level': result.threat_level.value,
                'confidence': result.confidence,
                'num_detections': len(result.detections),
                'detections': [d.to_dict() for d in result.detections],
                'scene_description': result.scene_description,
                'processing_time_ms': result.processing_time_ms
            }

            results.append(result_data)

            # 保存标注图像
            if save_annotations:
                from PIL import Image
                image = Image.open(image_file)

                # 绘制检测框
                annotated = visualizer.draw_detections(image, result.detections)

                # 绘制威胁横幅
                annotated = visualizer.draw_threat_banner(
                    annotated,
                    result.threat_level,
                    result.confidence,
                    len(result.detections)
                )

                # 保存
                output_path = annotations_dir / image_file.name
                annotated.save(output_path)

        except Exception as e:
            print(f"\nError processing {image_file.name}: {e}")
            continue

    # 5. 保存 JSON 结果
    if save_json:
        json_path = output_dir / "results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {json_path}")

    # 6. 显示统计
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)

    print(f"\nTotal images processed: {len(results)}")

    # 威胁等级统计
    threat_counts = {}
    for result in results:
        level = result['threat_level']
        threat_counts[level] = threat_counts.get(level, 0) + 1

    print("\nThreat Level Distribution:")
    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        count = threat_counts.get(level, 0)
        percentage = (count / len(results)) * 100 if results else 0
        print(f"  {level}: {count} ({percentage:.1f}%)")

    # 检测统计
    total_detections = sum(r['num_detections'] for r in results)
    avg_detections = total_detections / len(results) if results else 0
    print(f"\nTotal detections: {total_detections}")
    print(f"Average detections per image: {avg_detections:.2f}")

    # 性能统计
    avg_time = sum(r['processing_time_ms'] for r in results) / len(results) if results else 0
    print(f"\nAverage processing time: {avg_time:.2f} ms")

    # 获取系统指标
    metrics = system.get_metrics_summary()

    if 'total_processing' in metrics:
        total_time = metrics['total_processing']
        print(f"\nTotal processing statistics:")
        print(f"  Mean: {total_time['mean']*1000:.2f} ms")
        print(f"  Min: {total_time['min']*1000:.2f} ms")
        print(f"  Max: {total_time['max']*1000:.2f} ms")
        print(f"  P95: {total_time['p95']*1000:.2f} ms")

    print(f"\n✓ Annotated images saved to: {annotations_dir}")
    print("\n✅ Batch processing complete!")


def create_summary_report(results_json: str, output_path: str):
    """创建摘要报告"""
    print("=" * 60)
    print("Creating Summary Report")
    print("=" * 60)

    # 加载结果
    with open(results_json, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print(f"\n✓ Loaded {len(results)} results")

    # 生成报告
    report = []
    report.append("# Anti-Drone System - Batch Processing Report\n")
    report.append(f"**Total Images**: {len(results)}\n\n")

    # 威胁等级分布
    report.append("## Threat Level Distribution\n\n")

    threat_counts = {}
    for result in results:
        level = result['threat_level']
        threat_counts[level] = threat_counts.get(level, 0) + 1

    report.append("| Threat Level | Count | Percentage |\n")
    report.append("|--------------|-------|------------|\n")

    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        count = threat_counts.get(level, 0)
        percentage = (count / len(results)) * 100 if results else 0
        report.append(f"| {level} | {count} | {percentage:.1f}% |\n")

    # 检测统计
    report.append("\n## Detection Statistics\n\n")

    total_detections = sum(r['num_detections'] for r in results)
    avg_detections = total_detections / len(results) if results else 0

    report.append(f"- **Total Detections**: {total_detections}\n")
    report.append(f"- **Average per Image**: {avg_detections:.2f}\n\n")

    # 性能统计
    report.append("## Performance Statistics\n\n")

    avg_time = sum(r['processing_time_ms'] for r in results) / len(results) if results else 0
    min_time = min(r['processing_time_ms'] for r in results) if results else 0
    max_time = max(r['processing_time_ms'] for r in results) if results else 0

    report.append(f"- **Average Processing Time**: {avg_time:.2f} ms\n")
    report.append(f"- **Min Processing Time**: {min_time:.2f} ms\n")
    report.append(f"- **Max Processing Time**: {max_time:.2f} ms\n\n")

    # 高威胁图像
    high_threat_images = [
        r for r in results
        if r['threat_level'] in ['HIGH', 'CRITICAL']
    ]

    if high_threat_images:
        report.append("## High Threat Images\n\n")
        report.append("| Image | Threat Level | Confidence | Detections |\n")
        report.append("|-------|--------------|------------|------------|\n")

        for r in sorted(high_threat_images, key=lambda x: x['confidence'], reverse=True)[:10]:
            report.append(
                f"| {r['filename']} | {r['threat_level']} | "
                f"{r['confidence']:.2f} | {r['num_detections']} |\n"
            )

    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(report)

    print(f"\n✓ Report saved to: {output_path}")
    print("\n✅ Report generation complete!")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Batch Processing Examples")
    subparsers = parser.add_subparsers(dest='mode', help='Processing mode')

    # 批量处理模式
    process_parser = subparsers.add_parser('process', help='Batch process images')
    process_parser.add_argument('input_dir', help='Input directory containing images')
    process_parser.add_argument('output_dir', help='Output directory for results')
    process_parser.add_argument('--no-annotations', action='store_true', help='Skip saving annotated images')
    process_parser.add_argument('--no-json', action='store_true', help='Skip saving JSON results')

    # 报告生成模式
    report_parser = subparsers.add_parser('report', help='Generate summary report')
    report_parser.add_argument('results_json', help='Path to results.json')
    report_parser.add_argument('--output', '-o', default='report.md', help='Output report file')

    args = parser.parse_args()

    if args.mode == 'process':
        batch_process_images(
            args.input_dir,
            args.output_dir,
            save_annotations=not args.no_annotations,
            save_json=not args.no_json
        )

    elif args.mode == 'report':
        create_summary_report(args.results_json, args.output)

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
