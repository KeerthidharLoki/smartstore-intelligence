#!/usr/bin/env python3
"""
MOT17 Evaluation Script — SmartStore Intelligence
Measures MOTA, IDF1, MOTP using the BoT-SORT tracker on MOT17 sequences.

Usage:
    python eval/mot17_eval.py --mot17-path /path/to/MOT17 --sequence MOT17-02-FRCNN

Download MOT17: https://motchallenge.net/data/MOT17/
Install deps:   pip install motmetrics

Output: Prints a results table and saves to --output-dir/results.txt
"""

import argparse
import os
import time
import numpy as np
import cv2
from pathlib import Path


def parse_mot_gt(gt_path: str) -> dict:
    """
    Parse MOT17 ground truth file.
    Format: frame,id,x,y,w,h,conf,class,visibility
    Returns: dict mapping frame_id -> list of (id, x1, y1, x2, y2)
    """
    gt = {}
    with open(gt_path) as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 7:
                continue
            frame, tid, x, y, w, h = (
                int(parts[0]), int(parts[1]),
                float(parts[2]), float(parts[3]),
                float(parts[4]), float(parts[5]),
            )
            conf = float(parts[6]) if len(parts) > 6 else 1.0
            cls = int(parts[7]) if len(parts) > 7 else 1
            # Only evaluate pedestrian class (class=1) with conf=1
            if cls != 1 or conf < 1:
                continue
            if frame not in gt:
                gt[frame] = []
            gt[frame].append((tid, x, y, x + w, y + h))
    return gt


def run_tracker_on_sequence(seq_path: str, detector, tracker) -> dict:
    """
    Run YOLOv8 + BoT-SORT on a MOT17 sequence (image folder).
    Returns: dict mapping frame_id -> list of (id, x1, y1, x2, y2)
    """
    img_dir = os.path.join(seq_path, 'img1')
    if not os.path.exists(img_dir):
        raise FileNotFoundError(f"Image directory not found: {img_dir}")

    image_files = sorted(Path(img_dir).glob('*.jpg')) + sorted(Path(img_dir).glob('*.png'))
    predictions = {}

    print(f"Processing {len(image_files)} frames...")
    for i, img_path in enumerate(image_files):
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue

        detections = detector.detect(frame)
        tracks = tracker.update(detections, frame)

        frame_id = i + 1
        predictions[frame_id] = [(int(t[4]), t[0], t[1], t[2], t[3]) for t in tracks]

        if (i + 1) % 50 == 0:
            print(f"  Frame {i+1}/{len(image_files)}")

    return predictions


def compute_metrics(gt: dict, pred: dict) -> dict:
    """
    Compute MOTA, IDF1, MOTP using motmetrics.
    Falls back to basic metrics if motmetrics not installed.
    """
    try:
        import motmetrics as mm

        acc = mm.MOTAccumulator(auto_id=True)

        all_frames = sorted(set(list(gt.keys()) + list(pred.keys())))
        for frame_id in all_frames:
            gt_dets = gt.get(frame_id, [])
            pr_dets = pred.get(frame_id, [])

            gt_ids = [d[0] for d in gt_dets]
            pr_ids = [d[0] for d in pr_dets]

            if not gt_ids and not pr_ids:
                continue

            # Compute IoU distance matrix
            if gt_dets and pr_dets:
                gt_boxes = np.array([[d[1], d[2], d[3], d[4]] for d in gt_dets])
                pr_boxes = np.array([[d[1], d[2], d[3], d[4]] for d in pr_dets])
                dist = mm.distances.iou_matrix(gt_boxes, pr_boxes, max_iou=0.5)
            else:
                dist = np.empty((len(gt_ids), len(pr_ids)))

            acc.update(gt_ids, pr_ids, dist)

        mh = mm.metrics.create()
        summary = mh.compute(
            acc,
            metrics=['mota', 'idf1', 'motp', 'num_switches',
                     'num_misses', 'num_false_positives'],
            name='results',
        )

        return {
            'MOTA': float(summary['mota'].iloc[0]),
            'IDF1': float(summary['idf1'].iloc[0]),
            'MOTP': float(summary['motp'].iloc[0]),
            'ID_Switches': int(summary['num_switches'].iloc[0]),
            'Missed': int(summary['num_misses'].iloc[0]),
            'FP': int(summary['num_false_positives'].iloc[0]),
        }
    except ImportError:
        print("WARNING: motmetrics not installed. Run: pip install motmetrics")
        return {'error': 'motmetrics not installed'}


def main():
    parser = argparse.ArgumentParser(
        description='MOT17 Evaluation for SmartStore Intelligence'
    )
    parser.add_argument('--mot17-path', required=True,
                        help='Path to MOT17 dataset root')
    parser.add_argument('--sequence', default='MOT17-02-FRCNN',
                        help='Sequence name to evaluate')
    parser.add_argument('--output-dir', default='eval_results',
                        help='Directory to save results')
    parser.add_argument('--confidence', type=float, default=0.4,
                        help='Detection confidence threshold')
    args = parser.parse_args()

    seq_path = os.path.join(args.mot17_path, 'train', args.sequence)
    gt_path = os.path.join(seq_path, 'gt', 'gt.txt')

    if not os.path.exists(seq_path):
        print(f"ERROR: Sequence not found: {seq_path}")
        print("Download MOT17 from: https://motchallenge.net/data/MOT17/")
        return 1

    print(f"\n{'='*60}")
    print(f"SmartStore Intelligence — MOT17 Evaluation")
    print(f"Sequence: {args.sequence}")
    print(f"{'='*60}\n")

    # Import pipeline components
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from app.detector import PersonDetector
    from app.tracker import PersonTracker

    print("Loading models...")
    detector = PersonDetector(confidence=args.confidence)
    tracker = PersonTracker()

    print("Loading ground truth...")
    gt = parse_mot_gt(gt_path)
    print(f"  {len(gt)} frames with annotations")

    print("\nRunning tracker...")
    t0 = time.time()
    predictions = run_tracker_on_sequence(seq_path, detector, tracker)
    elapsed = time.time() - t0
    total_frames = len(predictions)
    fps = total_frames / elapsed if elapsed > 0 else 0

    print(f"\nProcessed {total_frames} frames in {elapsed:.1f}s ({fps:.1f} FPS)")

    print("\nComputing metrics...")
    metrics = compute_metrics(gt, predictions)

    # Print results table
    print(f"\n{'='*60}")
    print(f"{'Metric':<20} {'Value':>10}")
    print(f"{'-'*30}")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k:<18} {v*100:>9.2f}%")
        else:
            print(f"  {k:<18} {v:>10}")
    print(f"{'='*60}")
    print(f"  Processing Speed:    {fps:>9.1f} FPS")
    print(f"  Total Time:          {elapsed:>8.1f}s")
    print(f"{'='*60}\n")

    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    results_path = os.path.join(args.output_dir, 'results.txt')
    with open(results_path, 'w') as f:
        f.write("SmartStore Intelligence — MOT17 Evaluation Results\n")
        f.write(f"Sequence: {args.sequence}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for k, v in metrics.items():
            if isinstance(v, float):
                f.write(f"{k}: {v*100:.2f}%\n")
            else:
                f.write(f"{k}: {v}\n")
        f.write(f"FPS: {fps:.1f}\n")

    print(f"Results saved to: {results_path}")
    return 0


if __name__ == '__main__':
    exit(main())
