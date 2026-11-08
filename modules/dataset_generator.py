"""
Dataset Generator & Validator for SafeSite PPE YOLO Dataset.
Prepares YOLO-format dataset folders, generates ground-truth annotated synthetic worker samples,
and exports `data.yaml` with the 6 PPE classes:
  0: hard_hat, 1: safety_vest, 2: goggles, 3: person, 4: no_helmet, 5: no_vest
"""

from pathlib import Path
from typing import Dict, Any, List
import cv2
import numpy as np

import config

def generate_yolo_dataset(base_dir: Path = config.DATASET_DIR) -> Dict[str, Any]:
    """
    Creates YOLO dataset directory structure, data.yaml, and sample annotated images.
    """
    train_img_dir = base_dir / "images" / "train"
    val_img_dir = base_dir / "images" / "val"
    train_lbl_dir = base_dir / "labels" / "train"
    val_lbl_dir = base_dir / "labels" / "val"

    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Create data.yaml
    yaml_content = f"""# SafeSite PPE Detection YOLOv8 Dataset Configuration
path: {base_dir.as_posix()}
train: images/train
val: images/val

# 6 Safety PPE Classes
names:
  0: hard_hat
  1: safety_vest
  2: goggles
  3: person
  4: no_helmet
  5: no_vest
"""
    data_yaml_path = base_dir / "data.yaml"
    with open(data_yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    # 2. Generate Realistic Sample Images
    samples = [
        {
            "filename": "compliant_worker_01.jpg",
            "has_hat": True,
            "has_vest": True,
            "has_goggles": True,
            "desc": "Fully compliant worker with hard hat, high-vis vest, and goggles",
        },
        {
            "filename": "violation_missing_hat_02.jpg",
            "has_hat": False,
            "has_vest": True,
            "has_goggles": False,
            "desc": "Violation: Worker missing hard hat, wearing safety vest",
        },
        {
            "filename": "violation_missing_vest_03.jpg",
            "has_hat": True,
            "has_vest": False,
            "has_goggles": False,
            "desc": "Violation: Worker wearing hard hat, missing safety vest",
        },
        {
            "filename": "violation_no_ppe_04.jpg",
            "has_hat": False,
            "has_vest": False,
            "has_goggles": False,
            "desc": "Critical Violation: Worker with no safety gear",
        },
    ]

    generated_files = []

    for idx, s in enumerate(samples):
        img, labels = create_synthetic_worker_image(
            width=640,
            height=640,
            has_hard_hat=s["has_hat"],
            has_vest=s["has_vest"],
            has_goggles=s["has_goggles"],
        )

        # Save to both train and val for immediate testability
        for target_img_dir, target_lbl_dir in [(train_img_dir, train_lbl_dir), (val_img_dir, val_lbl_dir)]:
            img_path = target_img_dir / s["filename"]
            lbl_path = target_lbl_dir / s["filename"].replace(".jpg", ".txt")

            cv2.imwrite(str(img_path), img)

            # Write YOLO formatted normalized labels: <class_id> <x_center> <y_center> <width> <height>
            with open(lbl_path, "w", encoding="utf-8") as f:
                for lbl in labels:
                    f.write(f"{lbl[0]} {lbl[1]:.6f} {lbl[2]:.6f} {lbl[3]:.6f} {lbl[4]:.6f}\n")

        generated_files.append(s["filename"])

    return {
        "dataset_path": str(base_dir),
        "data_yaml": str(data_yaml_path),
        "samples_generated": generated_files,
        "classes": config.PPE_CLASSES,
    }


def create_synthetic_worker_image(
    width: int = 640,
    height: int = 640,
    has_hard_hat: bool = True,
    has_vest: bool = True,
    has_goggles: bool = False
) -> (np.ndarray, List[List[float]]):
    """
    Renders an image containing a construction worker with selectable PPE attributes,
    and returns corresponding YOLO bounding box labels.
    """
    # Background: Industrial / Construction site gradient
    img = np.zeros((height, width, 3), dtype=np.uint8)
    # Slate/concrete wall background
    for y in range(height):
        ratio = y / height
        color = (int(50 + ratio * 30), int(55 + ratio * 35), int(60 + ratio * 40))
        img[y, :] = color

    # Worker Dimensions & Placement
    # Center worker at (320, 310)
    wx1, wy1, wx2, wy2 = 200, 100, 440, 560
    w_w = wx2 - wx1
    w_h = wy2 - wy1

    # Draw Worker Body
    # Legs / Pants (Dark Denim Blue)
    cv2.rectangle(img, (230, 380), (300, 540), (90, 50, 30), -1)
    cv2.rectangle(img, (340, 380), (410, 540), (90, 50, 30), -1)
    # Steel-toe Work Boots
    cv2.rectangle(img, (220, 530), (305, 555), (20, 20, 20), -1)
    cv2.rectangle(img, (335, 530), (420, 555), (20, 20, 20), -1)

    # Torso (Base shirt)
    cv2.rectangle(img, (220, 220), (420, 390), (60, 60, 80), -1)
    # Arms
    cv2.rectangle(img, (185, 230), (225, 410), (60, 60, 80), -1)
    cv2.rectangle(img, (415, 230), (455, 410), (60, 60, 80), -1)

    # Head / Neck
    cv2.rectangle(img, (295, 195), (345, 225), (150, 175, 215), -1)  # Neck
    cv2.circle(img, (320, 160), 48, (150, 175, 215), -1)            # Face/Head

    labels: List[List[float]] = []

    # 1. Person Label (Class 3)
    p_cx = (wx1 + wx2) / (2.0 * width)
    p_cy = (wy1 + wy2) / (2.0 * height)
    p_bw = w_w / width
    p_bh = w_h / height
    labels.append([3, p_cx, p_cy, p_bw, p_bh])

    # 2. Hard Hat or No Helmet (Classes 0 or 4)
    hat_x1, hat_y1, hat_x2, hat_y2 = 260, 95, 380, 155
    hat_cx = (hat_x1 + hat_x2) / (2.0 * width)
    hat_cy = (hat_y1 + hat_y2) / (2.0 * height)
    hat_bw = (hat_x2 - hat_x1) / width
    hat_bh = (hat_y2 - hat_y1) / height

    if has_hard_hat:
        # High-Vis Yellow Construction Helmet
        cv2.ellipse(img, (320, 135), (55, 38), 0, 180, 360, (0, 215, 255), -1)
        cv2.rectangle(img, (262, 130), (378, 142), (0, 190, 230), -1)  # Brim
        cv2.rectangle(img, (312, 100), (328, 135), (0, 235, 255), -1)  # Ridge
        labels.append([0, hat_cx, hat_cy, hat_bw, hat_bh])
    else:
        # Bare hair (Brown/Black)
        cv2.ellipse(img, (320, 145), (48, 32), 0, 180, 360, (25, 30, 45), -1)
        labels.append([4, hat_cx, hat_cy, hat_bw, hat_bh])

    # 3. Safety Vest or No Vest (Classes 1 or 5)
    vest_x1, vest_y1, vest_x2, vest_y2 = 220, 220, 420, 385
    vest_cx = (vest_x1 + vest_x2) / (2.0 * width)
    vest_cy = (vest_y1 + vest_y2) / (2.0 * height)
    vest_bw = (vest_x2 - vest_x1) / width
    vest_bh = (vest_y2 - vest_y1) / height

    if has_vest:
        # Neon Orange/Yellow Safety Vest
        cv2.rectangle(img, (vest_x1, vest_y1), (vest_x2, vest_y2), (0, 140, 255), -1)
        # Silver/Grey Reflective Stripes
        cv2.rectangle(img, (vest_x1, vest_y1 + 50), (vest_x2, vest_y1 + 70), (220, 220, 220), -1)
        cv2.rectangle(img, (vest_x1, vest_y1 + 105), (vest_x2, vest_y1 + 125), (220, 220, 220), -1)
        cv2.rectangle(img, (260, vest_y1), (280, vest_y2), (220, 220, 220), -1)
        cv2.rectangle(img, (360, vest_y1), (380, vest_y2), (220, 220, 220), -1)
        labels.append([1, vest_cx, vest_cy, vest_bw, vest_bh])
    else:
        labels.append([5, vest_cx, vest_cy, vest_bw, vest_bh])

    # 4. Goggles (Class 2)
    if has_goggles:
        gog_x1, gog_y1, gog_x2, gog_y2 = 280, 145, 360, 175
        # Clear reflective protective lens with high-glare glass reflection
        cv2.rectangle(img, (gog_x1, gog_y1), (gog_x2, gog_y2), (250, 250, 250), -1)
        cv2.rectangle(img, (gog_x1, gog_y1), (gog_x2, gog_y2), (40, 40, 40), 2)  # Dark rim
        cv2.line(img, (gog_x1 + 10, gog_y1 + 5), (gog_x1 + 35, gog_y2 - 5), (255, 255, 255), 3)  # Glare shine
        cv2.line(img, (gog_x2 - 35, gog_y1 + 5), (gog_x2 - 10, gog_y2 - 5), (255, 255, 255), 3)  # Glare shine
        g_cx = (gog_x1 + gog_x2) / (2.0 * width)
        g_cy = (gog_y1 + gog_y2) / (2.0 * height)
        g_bw = (gog_x2 - gog_x1) / width
        g_bh = (gog_y2 - gog_y1) / height
        labels.append([2, g_cx, g_cy, g_bw, g_bh])

    return img, labels
