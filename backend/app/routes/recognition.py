"""
Face Recognition API Routes for Classroom Images and Live Webcam Stream.
Uses real FaceNet InceptionResnetV1 model and MTCNN/Haar Cascade face detection.
"""

import cv2
import base64
import numpy as np
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from database.db_manager import DatabaseManager
from modules.face_detection import FaceDetector
from modules.face_embedding import FaceEmbeddingExtractor
from modules.face_matching import FaceMatcher
from modules.attendance_manager import AttendanceManager
from backend.app.schemas.schemas import WebcamFrameRequest
from backend.app.auth.security import get_current_admin

router = APIRouter(prefix="/api/recognition", tags=["Face Recognition"])
db = DatabaseManager()
detector = FaceDetector()
extractor = FaceEmbeddingExtractor()
matcher = FaceMatcher()
attendance_mgr = AttendanceManager(
    db_manager=db, detector=detector, extractor=extractor, matcher=matcher
)


@router.post("/upload")
async def recognize_classroom_image(
    file: UploadFile = File(...),
    attendance_date: Optional[str] = Form(None),
    admin=Depends(get_current_admin),
):
    """
    Process classroom photograph for automated attendance.
    Detects all visible faces, runs FaceNet embedding extraction, matches against enrolled students,
    records attendance in SQLite, and returns bounding boxes + annotated image base64.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None or img.size == 0:
        raise HTTPException(status_code=400, detail="Invalid image file or format.")

    result = attendance_mgr.process_image_array(
        img=img,
        attendance_date=attendance_date,
        save_output=True,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Error analyzing classroom image.")

    return result


@router.post("/webcam")
def recognize_webcam_frame(
    req: WebcamFrameRequest,
    admin=Depends(get_current_admin),
):
    """
    Process a single webcam video frame from browser client.
    Detects faces, matches identities, and marks attendance once per student per date.
    """
    raw_b64 = req.image_base64
    if "," in raw_b64:
        raw_b64 = raw_b64.split(",")[1]

    try:
        img_bytes = base64.b64decode(raw_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode webcam frame: {e}")

    if frame is None or frame.size == 0:
        raise HTTPException(status_code=400, detail="Decoded image frame was empty.")

    detections = attendance_mgr.process_webcam_frame(
        frame_bgr=frame,
        attendance_date=req.attendance_date,
    )

    return {
        "success": True,
        "faces_detected": len(detections),
        "detections": detections,
    }

