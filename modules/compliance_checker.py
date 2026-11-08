"""
Spatial Containment Compliance Checker for SafeSite.
Associates PPE detections (hard hat, vest, goggles, no_helmet, no_vest) with
individual workers using geometric overlap on anatomical sub-regions (head, torso, eye).
Determines site compliance rules (mandatory vs hazard zone) and violation triggers.
"""

from typing import List, Dict, Any, Tuple
import config

def get_sub_region(worker_bbox: List[float], y_min_ratio: float, y_max_ratio: float) -> List[float]:
    """
    Extracts an anatomical sub-region of a worker's bounding box.
    worker_bbox: [x1, y1, x2, y2]
    """
    x1, y1, x2, y2 = worker_bbox
    height = y2 - y1
    sub_y1 = y1 + y_min_ratio * height
    sub_y2 = y1 + y_max_ratio * height
    return [x1, sub_y1, x2, sub_y2]

def compute_overlap_ratio(sub_region: List[float], ppe_bbox: List[float]) -> float:
    """
    Computes containment ratio: what fraction of the PPE bounding box
    falls inside the worker's anatomical sub-region.
    """
    rx1, ry1, rx2, ry2 = sub_region
    px1, py1, px2, py2 = ppe_bbox

    inter_x1 = max(rx1, px1)
    inter_y1 = max(ry1, py1)
    inter_x2 = min(rx2, px2)
    inter_y2 = min(ry2, py2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    ppe_area = max(1e-5, (px2 - px1) * (py2 - py1))
    return float(inter_area / ppe_area)


class ComplianceChecker:
    """
    Evaluates individual worker PPE compliance using anatomical containment and site rules.
    """

    def __init__(
        self,
        mandatory_ppe: List[str] = None,
        hazard_zone_ppe: List[str] = None,
        containment_threshold: float = 0.25
    ):
        self.mandatory_ppe = mandatory_ppe or list(config.DEFAULT_MANDATORY_PPE)
        self.hazard_zone_ppe = hazard_zone_ppe or list(config.HAZARD_ZONE_REQUIRED_PPE)
        self.containment_threshold = containment_threshold

    def evaluate_worker(
        self,
        worker_bbox: List[float],
        ppe_detections: List[Dict[str, Any]],
        hazard_zone: str = "General Site"
    ) -> Dict[str, Any]:
        """
        Evaluates safety compliance for a single worker.

        ppe_detections: List of dicts with:
          'class_name': str ('hard_hat', 'safety_vest', 'goggles', 'no_helmet', 'no_vest')
          'bbox': [x1, y1, x2, y2]
          'confidence': float

        Returns:
          Dict containing compliance_status ('COMPLIANT' or 'VIOLATION'),
          has_hard_hat, has_safety_vest, has_goggles, missing_items, associated_ppe
        """
        # Define worker anatomical sub-regions
        head_region = get_sub_region(worker_bbox, *config.HEAD_CONTAINMENT_RATIO)
        torso_region = get_sub_region(worker_bbox, *config.TORSO_CONTAINMENT_RATIO)
        eye_region = get_sub_region(worker_bbox, *config.EYE_CONTAINMENT_RATIO)

        has_hard_hat = False
        explicit_no_helmet = False
        has_vest = False
        explicit_no_vest = False
        has_goggles = False
        associated_ppe = []

        # Associate PPE items with worker via containment
        for ppe in ppe_detections:
            cls = ppe["class_name"]
            p_box = ppe["bbox"]

            if cls == "hard_hat":
                overlap = compute_overlap_ratio(head_region, p_box)
                if overlap >= self.containment_threshold:
                    has_hard_hat = True
                    associated_ppe.append({**ppe, "region": "head", "overlap": overlap})

            elif cls == "no_helmet":
                overlap = compute_overlap_ratio(head_region, p_box)
                if overlap >= self.containment_threshold:
                    explicit_no_helmet = True
                    associated_ppe.append({**ppe, "region": "head", "overlap": overlap})

            elif cls == "safety_vest":
                overlap = compute_overlap_ratio(torso_region, p_box)
                if overlap >= self.containment_threshold:
                    has_vest = True
                    associated_ppe.append({**ppe, "region": "torso", "overlap": overlap})

            elif cls == "no_vest":
                overlap = compute_overlap_ratio(torso_region, p_box)
                if overlap >= self.containment_threshold:
                    explicit_no_vest = True
                    associated_ppe.append({**ppe, "region": "torso", "overlap": overlap})

            elif cls == "goggles":
                overlap = compute_overlap_ratio(eye_region, p_box)
                if overlap >= self.containment_threshold:
                    has_goggles = True
                    associated_ppe.append({**ppe, "region": "eye", "overlap": overlap})

        # Apply Site Compliance Rules
        missing_items = []

        # 1. Hard Hat Rule (Mandatory)
        if "hard_hat" in self.mandatory_ppe:
            if not has_hard_hat or explicit_no_helmet:
                missing_items.append("Hard Hat")

        # 2. Safety Vest Rule (Mandatory)
        if "safety_vest" in self.mandatory_ppe:
            if not has_vest or explicit_no_vest:
                missing_items.append("Safety Vest")

        # 3. Goggles Rule (Required if hazard zone or site-wide rule enabled)
        is_hazard_zone = hazard_zone.lower() not in ["general site", "none", "safe"]
        if is_hazard_zone or "goggles" in self.mandatory_ppe:
            if not has_goggles:
                missing_items.append("Protective Goggles")

        compliance_status = "VIOLATION" if len(missing_items) > 0 else "COMPLIANT"

        return {
            "compliance_status": compliance_status,
            "has_hard_hat": has_hard_hat,
            "has_safety_vest": has_vest,
            "has_goggles": has_goggles,
            "missing_items": missing_items,
            "associated_ppe": associated_ppe,
            "hazard_zone": hazard_zone,
            "head_region": head_region,
            "torso_region": torso_region,
            "eye_region": eye_region,
        }

