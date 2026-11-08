"""
IoU-Based Worker Tracker for SafeSite PPE Monitoring.
Associates worker detections across consecutive video frames to maintain stable
worker identities (e.g. Worker #1, Worker #2) and apply temporal smoothing.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
import config

def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """
    Computes Intersection over Union (IoU) between two bounding boxes.
    Boxes format: [x1, y1, x2, y2]
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interWidth = max(0.0, xB - xA)
    interHeight = max(0.0, yB - yA)
    interArea = interWidth * interHeight

    boxAArea = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    unionArea = boxAArea + boxBArea - interArea
    if unionArea <= 0:
        return 0.0

    return float(interArea / unionArea)


class TrackedWorker:
    """Represents a single tracked worker identity across video frames."""

    def __init__(self, worker_id: int, bbox: List[float], confidence: float):
        self.worker_id = worker_id
        self.display_name = f"Worker #{worker_id}"
        self.bbox = list(bbox)  # [x1, y1, x2, y2]
        self.confidence = confidence
        self.disappeared_frames = 0
        self.history: List[List[float]] = [list(bbox)]
        self.compliance_status = "UNKNOWN"
        self.missing_items: List[str] = []
        self.compliance_streak = 0
        self.violation_streak = 0

    def update(self, new_bbox: List[float], confidence: float, smoothing_alpha: float = 0.7):
        """Updates worker bounding box with exponential temporal smoothing."""
        self.disappeared_frames = 0
        self.confidence = confidence
        # Exponential moving average for smooth bounding box rendering
        smoothed = [
            smoothing_alpha * new_bbox[i] + (1.0 - smoothing_alpha) * self.bbox[i]
            for i in range(4)
        ]
        self.bbox = smoothed
        self.history.append(smoothed)
        if len(self.history) > 30:
            self.history.pop(0)

    def mark_missed(self):
        """Increments missed frame counter."""
        self.disappeared_frames += 1


class WorkerTracker:
    """
    Multi-object tracker tracking workers across frames using bipartite IoU matching.
    """

    def __init__(
        self,
        iou_threshold: float = config.TRACKER_IOU_THRESHOLD,
        max_disappeared: int = config.TRACKER_MAX_DISAPPEARED_FRAMES
    ):
        self.iou_threshold = iou_threshold
        self.max_disappeared = max_disappeared
        self.next_worker_id = 1
        self.workers: Dict[int, TrackedWorker] = {}

    def update(self, detected_person_boxes: List[Dict]) -> List[TrackedWorker]:
        """
        Updates worker tracks with new detections from the current frame.
        Input: list of dicts with 'bbox': [x1, y1, x2, y2], 'confidence': float
        Returns list of active TrackedWorker objects.
        """
        # If no active workers exist, register all detections as new workers
        if len(self.workers) == 0:
            for det in detected_person_boxes:
                self._register(det["bbox"], det.get("confidence", 0.9))
            return list(self.workers.values())

        active_worker_ids = list(self.workers.keys())
        active_bboxes = [self.workers[wid].bbox for wid in active_worker_ids]

        # If no detections in current frame, mark all active workers as missed
        if len(detected_person_boxes) == 0:
            for wid in active_worker_ids:
                self.workers[wid].mark_missed()
                if self.workers[wid].disappeared_frames > self.max_disappeared:
                    del self.workers[wid]
            return list(self.workers.values())

        # Compute IoU cost matrix between tracked workers and new detections
        num_workers = len(active_worker_ids)
        num_dets = len(detected_person_boxes)
        iou_matrix = np.zeros((num_workers, num_dets), dtype=np.float32)

        for i, wid in enumerate(active_worker_ids):
            for j, det in enumerate(detected_person_boxes):
                iou_matrix[i, j] = compute_iou(active_bboxes[i], det["bbox"])

        # Greedy bipartite matching: pick highest IoU pairs
        matched_workers = set()
        matched_dets = set()

        if num_workers > 0 and num_dets > 0:
            flat_indices = np.argsort(-iou_matrix.ravel())
            for idx in flat_indices:
                w_idx, d_idx = divmod(int(idx), num_dets)
                if iou_matrix[w_idx, d_idx] < self.iou_threshold:
                    break
                if w_idx in matched_workers or d_idx in matched_dets:
                    continue

                matched_workers.add(w_idx)
                matched_dets.add(d_idx)
                wid = active_worker_ids[w_idx]
                det = detected_person_boxes[d_idx]
                self.workers[wid].update(det["bbox"], det.get("confidence", 0.9))

        # Unmatched workers -> increment missed
        for i, wid in enumerate(active_worker_ids):
            if i not in matched_workers:
                self.workers[wid].mark_missed()
                if self.workers[wid].disappeared_frames > self.max_disappeared:
                    del self.workers[wid]

        # Unmatched detections -> register as new workers
        for j, det in enumerate(detected_person_boxes):
            if j not in matched_dets:
                self._register(det["bbox"], det.get("confidence", 0.9))

        return list(self.workers.values())

    def reset(self):
        """Clears all tracked workers and resets ID counter."""
        self.workers.clear()
        self.next_worker_id = 1

    def _register(self, bbox: List[float], confidence: float):
        """Registers a new worker track."""
        worker = TrackedWorker(self.next_worker_id, bbox, confidence)
        self.workers[self.next_worker_id] = worker
        self.next_worker_id += 1
