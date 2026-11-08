"""
System Settings and Recognition Thresholds API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from database.db_manager import DatabaseManager
from backend.app.schemas.schemas import SettingsUpdate
from backend.app.auth.security import get_current_admin
import config

router = APIRouter(prefix="/api/settings", tags=["Settings"])
db = DatabaseManager()


@router.get("")
def get_system_settings(admin=Depends(get_current_admin)):
    """Retrieve current Computer Vision hyperparameters and database settings."""
    db_settings = db.get_all_settings()

    return {
        "euclidean_threshold": float(
            db_settings.get("euclidean_threshold", config.EUCLIDEAN_THRESHOLD)
        ),
        "cosine_threshold": float(
            db_settings.get("cosine_threshold", config.COSINE_THRESHOLD)
        ),
        "ambiguity_margin": float(
            db_settings.get("ambiguity_margin", config.AMBIGUITY_MARGIN)
        ),
        "default_detector": db_settings.get("default_detector", config.DEFAULT_DETECTOR),
        "matching_metric": db_settings.get("matching_metric", config.DEFAULT_MATCHING_METRIC),
        "embedding_model": "FaceNet InceptionResnetV1 (vggface2)",
        "embedding_dimension": config.EMBEDDING_DIMENSION,
        "face_resolution": "160x160",
    }


@router.put("")
def update_system_settings(settings: SettingsUpdate, admin=Depends(get_current_admin)):
    """Update runtime recognition thresholds and detection methods."""
    if settings.euclidean_threshold is not None:
        if not (0.2 <= settings.euclidean_threshold <= 1.5):
            raise HTTPException(status_code=400, detail="Euclidean threshold must be between 0.2 and 1.5")
        db.set_setting("euclidean_threshold", str(settings.euclidean_threshold))
        config.EUCLIDEAN_THRESHOLD = settings.euclidean_threshold

    if settings.cosine_threshold is not None:
        if not (0.3 <= settings.cosine_threshold <= 0.99):
            raise HTTPException(status_code=400, detail="Cosine threshold must be between 0.3 and 0.99")
        db.set_setting("cosine_threshold", str(settings.cosine_threshold))
        config.COSINE_THRESHOLD = settings.cosine_threshold

    if settings.ambiguity_margin is not None:
        db.set_setting("ambiguity_margin", str(settings.ambiguity_margin))
        config.AMBIGUITY_MARGIN = settings.ambiguity_margin

    if settings.default_detector is not None:
        db.set_setting("default_detector", settings.default_detector)
        config.DEFAULT_DETECTOR = settings.default_detector

    if settings.matching_metric is not None:
        db.set_setting("matching_metric", settings.matching_metric)
        config.DEFAULT_MATCHING_METRIC = settings.matching_metric

    return {"message": "Settings updated successfully."}

