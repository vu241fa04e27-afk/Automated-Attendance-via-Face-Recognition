"""
Real-Time Visualizer for SafeSite PPE Detection and Safety Compliance Monitoring.
Draws color-coded worker bounding boxes, compliance badges, anatomical containment regions,
and a modern telemetry HUD banner.
"""

from typing import List, Dict, Any, Optional
import cv2
import numpy as np

# Color Definitions (BGR for OpenCV)
COLOR_COMPLIANT = (40, 200, 40)      # Vivid Green
COLOR_VIOLATION = (40, 40, 230)      # High-Alert Red
COLOR_WARNING = (30, 210, 255)       # Amber / Yellow
COLOR_PPE_ITEM = (255, 180, 50)      # Sky Blue / Cyan
COLOR_HUD_BG = (20, 24, 30)          # Dark Slate
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

class PPEVisualizer:
    """
    Renders bounding boxes, alert headers, missing PPE tags, and telemetry overlay.
    """

    def __init__(self, show_hud: bool = True, show_ppe_boxes: bool = True):
        self.show_hud = show_hud
        self.show_ppe_boxes = show_ppe_boxes

    def draw_frame(
        self,
        image: np.ndarray,
        workers: List[Dict[str, Any]],
        ppe_items: Optional[List[Dict[str, Any]]] = None,
        fps: float = 30.0,
        hazard_zone: str = "General Site"
    ) -> np.ndarray:
        """
        Draws visual annotations onto a copy of the input frame.
        """
        annotated = image.copy()
        h, w = annotated.shape[:2]

        total_workers = len(workers)
        compliant_count = sum(1 for w_info in workers if w_info.get("compliance_status") == "COMPLIANT")
        violation_count = total_workers - compliant_count

        # 1. Optionally draw individual PPE item bounding boxes
        if self.show_ppe_boxes and ppe_items:
            for ppe in ppe_items:
                cls_name = ppe.get("class_name", "")
                box = [int(v) for v in ppe.get("bbox", [0, 0, 0, 0])]
                conf = ppe.get("confidence", 0.0)

                if cls_name == "hard_hat":
                    color = (0, 220, 255)  # Yellow
                    label = f"Hard Hat {int(conf*100)}%"
                elif cls_name == "safety_vest":
                    color = (0, 255, 150)  # Neon Green
                    label = f"Vest {int(conf*100)}%"
                elif cls_name == "goggles":
                    color = (255, 200, 0)  # Cyan
                    label = f"Goggles {int(conf*100)}%"
                elif cls_name in ["no_helmet", "no_vest"]:
                    color = (0, 0, 255)    # Red
                    label = f"NO {cls_name.replace('no_', '').upper()}"
                else:
                    color = (200, 200, 200)
                    label = cls_name

                # Draw dashed or thin rectangle for item
                cv2.rectangle(annotated, (box[0], box[1]), (box[2], box[3]), color, 1, cv2.LINE_AA)
                cv2.putText(
                    annotated,
                    label,
                    (box[0] + 4, max(15, box[1] - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.38,
                    color,
                    1,
                    cv2.LINE_AA,
                )

        # 2. Draw worker bounding boxes and compliance status
        for worker in workers:
            bbox = [int(v) for v in worker.get("bbox", [0, 0, 0, 0])]
            worker_id = worker.get("display_name", f"Worker #{worker.get('worker_id', 1)}")
            status = worker.get("compliance_status", "UNKNOWN")
            missing = worker.get("missing_items", [])

            is_compliant = (status == "COMPLIANT")
            box_color = COLOR_COMPLIANT if is_compliant else COLOR_VIOLATION

            # Outer bounding box
            thickness = 3 if not is_compliant else 2
            cv2.rectangle(annotated, (bbox[0], bbox[1]), (bbox[2], bbox[3]), box_color, thickness, cv2.LINE_AA)

            # Corner accents
            c_len = min(20, (bbox[2] - bbox[0]) // 4, (bbox[3] - bbox[1]) // 4)
            cv2.line(annotated, (bbox[0], bbox[1]), (bbox[0] + c_len, bbox[1]), box_color, 4)
            cv2.line(annotated, (bbox[0], bbox[1]), (bbox[0], bbox[1] + c_len), box_color, 4)
            cv2.line(annotated, (bbox[2], bbox[1]), (bbox[2] - c_len, bbox[1]), box_color, 4)
            cv2.line(annotated, (bbox[2], bbox[1]), (bbox[2], bbox[1] + c_len), box_color, 4)
            cv2.line(annotated, (bbox[0], bbox[3]), (bbox[0] + c_len, bbox[3]), box_color, 4)
            cv2.line(annotated, (bbox[0], bbox[3]), (bbox[0], bbox[3] - c_len), box_color, 4)
            cv2.line(annotated, (bbox[2], bbox[3]), (bbox[2] - c_len, bbox[3]), box_color, 4)
            cv2.line(annotated, (bbox[2], bbox[3]), (bbox[2], bbox[3] - c_len), box_color, 4)

            # Top Badge Header
            header_text = f"{worker_id}: {'COMPLIANT' if is_compliant else 'VIOLATION'}"
            (tw, th), _ = cv2.getTextSize(header_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            badge_y1 = max(0, bbox[1] - th - 12)
            badge_y2 = bbox[1]
            badge_x1 = bbox[0]
            badge_x2 = bbox[0] + tw + 14

            cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), box_color, -1)
            cv2.putText(
                annotated,
                header_text,
                (badge_x1 + 6, badge_y2 - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                COLOR_WHITE,
                2,
                cv2.LINE_AA,
            )

            # Missing items warning banner underneath worker box
            if not is_compliant and len(missing) > 0:
                missing_str = "MISSING: " + ", ".join(missing).upper()
                (mw, mh), _ = cv2.getTextSize(missing_str, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                sub_y1 = bbox[3]
                sub_y2 = bbox[3] + mh + 10
                cv2.rectangle(annotated, (bbox[0], sub_y1), (bbox[0] + mw + 12, sub_y2), (0, 0, 160), -1)
                cv2.putText(
                    annotated,
                    missing_str,
                    (bbox[0] + 6, sub_y2 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

        # 3. Draw Telemetry HUD at the top
        if self.show_hud:
            hud_h = 50
            overlay = annotated.copy()
            cv2.rectangle(overlay, (0, 0), (w, hud_h), COLOR_HUD_BG, -1)
            cv2.addWeighted(overlay, 0.85, annotated, 0.15, 0, annotated)

            # Brand
            cv2.putText(annotated, "SafeSite PPE Monitor", (14, 30), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 220, 255), 2, cv2.LINE_AA)

            # Telemetry Metrics
            stats_str = f"Workers: {total_workers}  |  Compliant: {compliant_count}  |  Violations: {violation_count}  |  Zone: {hazard_zone}"
            cv2.putText(annotated, stats_str, (240, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.50, COLOR_WHITE, 1, cv2.LINE_AA)

            # FPS
            fps_str = f"FPS: {fps:.1f}"
            cv2.putText(annotated, fps_str, (max(w - 110, 500), 30), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (100, 255, 100), 2, cv2.LINE_AA)

        return annotated

