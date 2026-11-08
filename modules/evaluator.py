"""
Evaluation & Benchmark Metrics Module for SafeSite PPE YOLOv8-nano Model.
Provides mAP@50, mAP@50-95, precision, recall, per-class Average Precision (AP),
latency, and FPS metrics matching the project technical report.
"""

from typing import Dict, Any, List
import time
import numpy as np

import config

def get_benchmark_report() -> Dict[str, Any]:
    """
    Returns full evaluation report and benchmark measurements from the case study technical report.
    """
    return {
        "model_architecture": "YOLOv8-nano (Anchor-Free)",
        "input_resolution": "640x640",
        "parameters": "3.2M",
        "gflops": 8.7,
        "mAP_50": 91.4,
        "mAP_50_95": 68.2,
        "precision": 92.6,
        "recall": 89.8,
        "f1_score": 91.2,
        "class_metrics": [
            {"class_name": "hard_hat", "display": "Hard Hat", "ap_50": 94.2, "precision": 95.1, "recall": 93.3},
            {"class_name": "safety_vest", "display": "Safety Vest", "ap_50": 92.8, "precision": 94.0, "recall": 91.6},
            {"class_name": "goggles", "display": "Protective Goggles", "ap_50": 83.5, "precision": 86.2, "recall": 80.9},
            {"class_name": "person", "display": "Worker / Person", "ap_50": 96.1, "precision": 97.4, "recall": 94.8},
            {"class_name": "no_helmet", "display": "No Helmet (Violation)", "ap_50": 89.7, "precision": 91.0, "recall": 88.4},
            {"class_name": "no_vest", "display": "No Vest (Violation)", "ap_50": 88.5, "precision": 89.8, "recall": 87.2},
        ],
        "latency_metrics": {
            "preprocess_ms": 1.8,
            "inference_ms": 14.8,
            "nms_ms": 1.4,
            "tracking_and_containment_ms": 2.1,
            "total_latency_ms": 20.1,
            "fps_cpu": 35.2,
            "fps_edge_tpu": 72.0,
        },
        "learning_objectives": [
            "Anchor-free bounding-box regression eliminating anchor-tuning overhead",
            "Complete IoU (CIoU) loss for rapid bounding box convergence",
            "IoU-based worker tracking across frames to suppress ID switching",
            "Spatial containment rules matching equipment to anatomical sub-regions (head, torso, eye)",
            "Real-time visual and acoustic alerts with permanent SQLite audit trail",
        ],
    }

