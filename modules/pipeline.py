"""
SafeSite Unified PPE Processing Pipeline.
Integrates YOLOv8 object detection, IoU worker tracking, spatial containment compliance checking,
acoustic alerts, and SQLite audit logging.
"""

from typing import List, Dict, Any, Optional
import time
import cv2
import numpy as np

import config
from modules.ppe_detector import PPEDetector
from modules.worker_tracker import WorkerTracker
from modules.compliance_checker import ComplianceChecker
from modules.visualizer import PPEVisualizer
from modules.audio_alert import trigger_violation_alarm
from database.violations_db import log_violation, log_detection_event

class SafeSitePipeline:
    """
    Orchestrates the entire SafeSite PPE computer vision pipeline.
    """

    def __init__(
        self,
        conf_threshold: float = config.CONF_THRESHOLD,
        iou_threshold: float = config.IOU_THRESHOLD,
        mandatory_ppe: Optional[List[str]] = None,
    ):
        self.detector = PPEDetector(conf_threshold=conf_threshold, iou_threshold=iou_threshold)
        self.tracker = WorkerTracker(iou_threshold=config.TRACKER_IOU_THRESHOLD)
        self.checker = ComplianceChecker(mandatory_ppe=mandatory_ppe)
        self.visualizer = PPEVisualizer(show_hud=True, show_ppe_boxes=True)
        self.fps_history: List[float] = []

    def reset_tracker(self):
        """Resets the tracking state for new video feeds or distinct static images."""
        self.tracker.reset()

    def process_frame(
        self,
        frame: np.ndarray,
        hazard_zone: str = "General Site",
        record_violations: bool = True,
        is_static_image: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a single video/webcam/image frame.
        """
        if is_static_image:
            self.tracker.reset()

        start_time = time.time()

        # 1. Object Detection (YOLOv8-nano)
        det_result = self.detector.detect(frame)
        person_detections = det_result["persons"]
        ppe_items = det_result["ppe_items"]

        # 2. Worker Tracking (IoU-based)
        tracked_workers = self.tracker.update(person_detections)

        # 3. Spatial Containment & Compliance Checking
        evaluated_workers: List[Dict[str, Any]] = []
        violations: List[Dict[str, Any]] = []

        for tw in tracked_workers:
            eval_res = self.checker.evaluate_worker(tw.bbox, ppe_items, hazard_zone=hazard_zone)
            status = eval_res["compliance_status"]
            missing = eval_res["missing_items"]

            tw.compliance_status = status
            tw.missing_items = missing

            worker_summary = {
                "worker_id": tw.worker_id,
                "display_name": tw.display_name,
                "bbox": [round(c, 1) for c in tw.bbox],
                "confidence": tw.confidence,
                "compliance_status": status,
                "missing_items": missing,
                "has_hard_hat": eval_res["has_hard_hat"],
                "has_safety_vest": eval_res["has_safety_vest"],
                "has_goggles": eval_res["has_goggles"],
                "hazard_zone": hazard_zone,
            }
            evaluated_workers.append(worker_summary)

            # Audit logging & alert triggers on violation
            if status == "VIOLATION":
                violations.append(worker_summary)
                if record_violations:
                    trigger_violation_alarm()
                    log_violation(
                        worker_id=tw.display_name,
                        missing_items=missing,
                        hazard_zone=hazard_zone,
                        confidence=tw.confidence,
                        notes=f"Missing: {', '.join(missing)}",
                    )
            elif record_violations:
                log_detection_event(
                    worker_id=tw.display_name,
                    compliance_status="COMPLIANT",
                    has_hard_hat=eval_res["has_hard_hat"],
                    has_vest=eval_res["has_safety_vest"],
                    has_goggles=eval_res["has_goggles"],
                    hazard_zone=hazard_zone,
                )

        # 4. Calculate FPS
        elapsed = max(1e-4, time.time() - start_time)
        current_fps = 1.0 / elapsed
        self.fps_history.append(current_fps)
        if len(self.fps_history) > 30:
            self.fps_history.pop(0)
        avg_fps = sum(self.fps_history) / len(self.fps_history)

        # 5. Visualization overlay
        annotated_frame = self.visualizer.draw_frame(
            image=frame,
            workers=evaluated_workers,
            ppe_items=ppe_items,
            fps=avg_fps,
            hazard_zone=hazard_zone,
        )

        compliant_count = sum(1 for w in evaluated_workers if w["compliance_status"] == "COMPLIANT")
        violation_count = len(violations)

        return {
            "annotated_frame": annotated_frame,
            "workers": evaluated_workers,
            "ppe_items": ppe_items,
            "violations": violations,
            "fps": round(avg_fps, 1),
            "latency_ms": round(elapsed * 1000.0, 1),
            "compliant_count": compliant_count,
            "violation_count": violation_count,
            "total_workers": len(evaluated_workers),
        }
