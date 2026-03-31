#!/usr/bin/env python3
"""
SmartStore Intelligence — Performance Benchmark
Measures real-time inference speed and detection accuracy.

Usage:
    python eval/benchmark.py [--frames 200] [--warmup 10]
"""

import argparse
import sys
import time
import os
import json
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def benchmark_detection(model, frame: np.ndarray, n_frames: int, warmup: int) -> dict:
    """Measure detection FPS over n_frames."""
    # Warmup
    for _ in range(warmup):
        model.detect(frame)

    times = []
    detections_per_frame = []
    for _ in range(n_frames):
        t0 = time.perf_counter()
        dets = model.detect(frame)
        times.append(time.perf_counter() - t0)
        detections_per_frame.append(len(dets))

    return {
        "fps": round(1.0 / (sum(times) / len(times)), 2),
        "latency_ms_mean": round(np.mean(times) * 1000, 1),
        "latency_ms_p99": round(np.percentile(times, 99) * 1000, 1),
        "avg_detections": round(np.mean(detections_per_frame), 1),
        "total_frames": n_frames,
    }


def benchmark_pipeline(model, tracker, frame: np.ndarray, n_frames: int) -> dict:
    """Measure end-to-end detect + track FPS."""
    times = []
    unique_ids = set()

    for _ in range(n_frames):
        t0 = time.perf_counter()
        dets = model.detect(frame)
        tracks = tracker.update(dets, frame)
        times.append(time.perf_counter() - t0)
        for t in tracks:
            unique_ids.add(int(t[4]))

    return {
        "pipeline_fps": round(1.0 / (sum(times) / len(times)), 2),
        "pipeline_latency_ms": round(np.mean(times) * 1000, 1),
        "unique_track_ids": len(unique_ids),
    }


def get_model_info(model_name: str = "yolov8n.pt") -> dict:
    """Return model metadata."""
    from ultralytics import YOLO
    import torch
    m = YOLO(model_name)
    params = sum(p.numel() for p in m.model.parameters())
    return {
        "model": model_name,
        "parameters_M": round(params / 1e6, 2),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
    }


def main():
    parser = argparse.ArgumentParser(description="SmartStore Intelligence Benchmark")
    parser.add_argument("--frames", type=int, default=200, help="Frames to benchmark")
    parser.add_argument("--warmup", type=int, default=10, help="Warmup frames")
    parser.add_argument("--output", type=str, default="eval_results/benchmark.json")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  SmartStore Intelligence — Benchmark")
    print("=" * 60)

    # Load test frame (bus.jpg has pedestrians — COCO class 0)
    import ultralytics as _ul
    pkg_dir = os.path.dirname(_ul.__file__)
    test_img = os.path.join(pkg_dir, "assets", "bus.jpg")
    frame = cv2.imread(test_img)
    if frame is None:
        # Fallback: create synthetic frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        print("  Using synthetic frames (test image not found)")
    else:
        frame = cv2.resize(frame, (640, 480))
        print(f"  Test image: bus.jpg ({frame.shape[1]}×{frame.shape[0]})")

    # Import our modules
    from app.detector import PersonDetector
    from app.tracker import PersonTracker

    print("\n  Loading models...")
    model_info = get_model_info()
    detector = PersonDetector(confidence=0.4)
    tracker = PersonTracker(max_age=30)

    print(f"  Model:      {model_info['model']}")
    print(f"  Parameters: {model_info['parameters_M']}M")
    print(f"  Device:     {model_info['device']}")
    print(f"  Benchmark:  {args.frames} frames  ({args.warmup} warmup)\n")

    # Detection benchmark
    print("  [1/2] Detection benchmark...")
    det_results = benchmark_detection(detector, frame, args.frames, args.warmup)
    print(f"        FPS:             {det_results['fps']}")
    print(f"        Latency (mean):  {det_results['latency_ms_mean']} ms")
    print(f"        Latency (p99):   {det_results['latency_ms_p99']} ms")
    print(f"        Avg detections:  {det_results['avg_detections']}")

    # Pipeline benchmark (detect + track)
    print("\n  [2/2] Full pipeline benchmark (detect + track)...")
    pipe_results = benchmark_pipeline(detector, tracker, frame, min(args.frames, 100))
    print(f"        Pipeline FPS:    {pipe_results['pipeline_fps']}")
    print(f"        Pipeline latency:{pipe_results['pipeline_latency_ms']} ms")
    print(f"        Unique IDs seen: {pipe_results['unique_track_ids']}")

    # Compile results
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_info": model_info,
        "detection": det_results,
        "pipeline": pipe_results,
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Model:             YOLOv8n ({model_info['parameters_M']}M params)")
    print(f"  Device:            {model_info['device'].upper()}")
    print(f"  Detection FPS:     {det_results['fps']}")
    print(f"  Pipeline FPS:      {pipe_results['pipeline_fps']}")
    print(f"  Detection latency: {det_results['latency_ms_mean']} ms (mean)")
    print("=" * 60)
    print(f"\n  Results saved: {args.output}\n")

    return results


if __name__ == "__main__":
    main()
