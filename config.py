"""
Configuration module for SafeSite: Real-Time PPE Detection and Safety Compliance Monitoring.
Defines paths, model hyperparameters, YOLOv8-nano settings, spatial containment ratios, and site rules.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = Path(os.environ["DB_PATH"]) if os.environ.get("DB_PATH") else DATABASE_DIR / "violations.db"

# Data & Model directories
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = Path(os.environ["OUTPUT_DIR"]) if os.environ.get("OUTPUT_DIR") else BASE_DIR / "output"
REPORTS_DIR = Path(os.environ["REPORTS_DIR"]) if os.environ.get("REPORTS_DIR") else BASE_DIR / "reports"

# Ensure all vital directories exist
for directory in [
    DATABASE_DIR,
    DATASET_DIR,
    MODELS_DIR,
    OUTPUT_DIR,
    REPORTS_DIR,
    DB_PATH.parent,
]:
    directory.mkdir(parents=True, exist_ok=True)

# YOLOv8-nano PPE Model Configuration
# 6 Classes as specified in the case study:
# hard_hat, safety_vest, goggles, person, no_helmet, no_vest
PPE_CLASSES = [
    "hard_hat",
    "safety_vest",
    "goggles",
    "person",
    "no_helmet",
    "no_vest",
]

CLASS_TO_ID = {name: idx for idx, name in enumerate(PPE_CLASSES)}
ID_TO_CLASS = {idx: name for idx, name in enumerate(PPE_CLASSES)}

# Detection Hyperparameters
CONF_THRESHOLD = float(os.environ.get("CONF_THRESHOLD", 0.35))
IOU_THRESHOLD = float(os.environ.get("IOU_THRESHOLD", 0.45))
INPUT_IMAGE_SIZE = (640, 640)
YOLO_MODEL_NAME = "yolov8n.pt"

# Spatial Containment Ratios on Worker Bounding Box (ymin_ratio, ymax_ratio)
# Head region: top 0% to 22% of person height
HEAD_CONTAINMENT_RATIO = (0.00, 0.22)
# Eye/Face region: 10% to 24% of person height
EYE_CONTAINMENT_RATIO = (0.10, 0.24)
# Torso region: 25% to 75% of person height
TORSO_CONTAINMENT_RATIO = (0.25, 0.75)

# Safety Rules Configuration
# Mandatory site-wide PPE
DEFAULT_MANDATORY_PPE = ["hard_hat", "safety_vest"]
# PPE required only in designated hazard zones (e.g. grinding, welding, chemical)
HAZARD_ZONE_REQUIRED_PPE = ["goggles"]

# Worker Tracking Configuration (IoU-based tracker)
TRACKER_IOU_THRESHOLD = 0.30
TRACKER_MAX_DISAPPEARED_FRAMES = 20

# Audio Alert Settings
AUDIO_ALERT_ENABLED = True
AUDIO_ALERT_DEBOUNCE_SECONDS = 2.0  # Avoid ringing on every frame

# Technical Report Benchmark Metrics (From Case Study Report)
BENCHMARK_METRICS = {
    "model": "YOLOv8-nano (anchor-free)",
    "resolution": "640x640",
    "mAP_50": 91.4,
    "mAP_50_95": 68.2,
    "class_AP_50": {
        "hard_hat": 94.2,
        "safety_vest": 92.8,
        "goggles": 83.5,
        "person": 96.1,
        "no_helmet": 89.7,
        "no_vest": 88.5,
    },
    "inference_latency_ms": 14.8,
    "target_fps": 35.0,
}
