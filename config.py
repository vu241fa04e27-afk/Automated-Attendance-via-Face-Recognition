"""
Configuration module for Automated Attendance System using Face Recognition.
Contains all directory paths, model hyperparameters, detection, and recognition thresholds.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "attendance.db"

# Data directories
DATASET_DIR = BASE_DIR / "dataset"
STUDENT_IMAGES_DIR = DATASET_DIR / "student_images"
CLASSROOM_IMAGES_DIR = DATASET_DIR / "classroom_images"

# Models and Output directories
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"

# Haar Cascade path (check project models directory first, then OpenCV default if present)
HAAR_CASCADE_PATH = MODELS_DIR / "haarcascade_frontalface_default.xml"

# Face Detection Settings
# Supported detector options: "mtcnn", "haar"
DEFAULT_DETECTOR = "mtcnn"
FACE_IMAGE_SIZE = (160, 160)  # Standard input resolution for FaceNet InceptionResnetV1
MTCNN_MIN_FACE_SIZE = 40
MTCNN_THRESHOLDS = [0.6, 0.7, 0.7]  # P-Net, R-Net, O-Net thresholds

# Face Recognition Settings
# Pretrained weight dataset: 'vggface2' or 'casia-webface'
FACENET_PRETRAINED_DATASET = "vggface2"
EMBEDDING_DIMENSION = 512

# Matching Metrics & Thresholds
# Euclidean distance threshold: smaller distance means closer identity.
# Since FaceNet outputs L2-normalized embeddings (unit sphere),
# Euclidean distance typically falls between [0.0, 1.4].
# A threshold between 0.75 - 0.88 is recommended; 0.85 provides a balanced False Accept vs False Reject rate.
EUCLIDEAN_THRESHOLD = 0.85

# Cosine similarity threshold: higher similarity (closer to 1.0) means closer identity.
# Typically > 0.65 to 0.75 indicates same identity.
COSINE_THRESHOLD = 0.68

# Default matching metric: "euclidean" or "cosine"
DEFAULT_MATCHING_METRIC = "euclidean"

# Ambiguity threshold: If top match and second match have distance difference < AMBIGUITY_MARGIN,
# the face match is deemed uncertain and classified as UNKNOWN.
AMBIGUITY_MARGIN = 0.08

# Webcam Settings
DEFAULT_WEBCAM_INDEX = 0
WEBCAM_FRAME_WIDTH = 640
WEBCAM_FRAME_HEIGHT = 480
WEBCAM_FPS_DISPLAY = True

# Registration Settings
MIN_REGISTRATION_SAMPLES = 1
MAX_REGISTRATION_SAMPLES = 10

# Create required directories automatically
for directory in [
    DATABASE_DIR,
    DATASET_DIR,
    STUDENT_IMAGES_DIR,
    CLASSROOM_IMAGES_DIR,
    MODELS_DIR,
    OUTPUT_DIR,
    REPORTS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

