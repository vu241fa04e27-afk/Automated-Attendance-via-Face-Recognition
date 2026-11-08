"""
FastAPI Routes for Safety Rules, Hazard Zones, and Detector Settings.
"""

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

import config

router = APIRouter(prefix="/api/settings", tags=["Safety Settings"])

class SettingsUpdate(BaseModel):
    mandatory_ppe: Optional[List[str]] = None
    hazard_zone_ppe: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None
    iou_threshold: Optional[float] = None
    audio_alert_enabled: Optional[bool] = None

@router.get("")
async def get_settings():
    """Returns current safety configuration and detection settings."""
    return {
        "status": "success",
        "settings": {
            "mandatory_ppe": config.DEFAULT_MANDATORY_PPE,
            "hazard_zone_ppe": config.HAZARD_ZONE_REQUIRED_PPE,
            "confidence_threshold": config.CONF_THRESHOLD,
            "iou_threshold": config.IOU_THRESHOLD,
            "audio_alert_enabled": config.AUDIO_ALERT_ENABLED,
            "available_classes": config.PPE_CLASSES,
            "hazard_zones": [
                "General Site",
                "Welding & Grinding Zone",
                "Chemical Handling Area",
                "Scaffolding & Heights",
                "Excavation & Trenching",
            ],
        }
    }

@router.post("")
async def update_settings(update: SettingsUpdate):
    """Updates safety rules and detection thresholds."""
    if update.mandatory_ppe is not None:
        config.DEFAULT_MANDATORY_PPE = update.mandatory_ppe
    if update.hazard_zone_ppe is not None:
        config.HAZARD_ZONE_REQUIRED_PPE = update.hazard_zone_ppe
    if update.confidence_threshold is not None:
        config.CONF_THRESHOLD = update.confidence_threshold
    if update.iou_threshold is not None:
        config.IOU_THRESHOLD = update.iou_threshold
    if update.audio_alert_enabled is not None:
        config.AUDIO_ALERT_ENABLED = update.audio_alert_enabled

    return {"status": "success", "message": "Safety settings updated successfully"}
