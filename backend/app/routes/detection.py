"""
FastAPI Routes for Object Detection, Worker Tracking, and PPE Compliance Evaluation.
"""

import base64
import time
from pathlib import Path
from typing import Optional, List
import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel

import config
from modules.pipeline import SafeSitePipeline

router = APIRouter(prefix="/api/detect", tags=["PPE Detection & Compliance"])

# Shared pipeline instance
pipeline = SafeSitePipeline()

class FrameRequest(BaseModel):
    image_base64: str
    hazard_zone: Optional[str] = "General Site"
    record_violations: Optional[bool] = False

@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
    hazard_zone: str = Form("General Site"),
    record_violations: bool = Form(True)
):
    """
    Processes an uploaded image through the YOLOv8 PPE detection and compliance pipeline.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")

    result = pipeline.process_frame(
        frame=img,
        hazard_zone=hazard_zone,
        record_violations=record_violations
    )

    # Save output image to disk
    out_filename = f"detection_{int(time.time() * 1000)}.jpg"
    out_path = config.OUTPUT_DIR / out_filename
    cv2.imwrite(str(out_path), result["annotated_frame"])

    # Also encode base64 for instant rendering in frontend
    _, buffer = cv2.imencode(".jpg", result["annotated_frame"])
    b64_str = base64.b64encode(buffer).decode("utf-8")

    return {
        "status": "success",
        "output_image_url": f"/static/output/{out_filename}",
        "annotated_base64": f"data:image/jpeg;base64,{b64_str}",
        "hazard_zone": hazard_zone,
        "total_workers": result["total_workers"],
        "compliant_count": result["compliant_count"],
        "violation_count": result["violation_count"],
        "fps": result["fps"],
        "latency_ms": result["latency_ms"],
        "workers": result["workers"],
        "ppe_items": result["ppe_items"],
        "violations": result["violations"],
    }

@router.post("/frame")
async def detect_frame(request: FrameRequest):
    """
    Fast endpoint for processing real-time video frames streamed from client webcam via base64.
    """
    try:
        # Strip data URL prefix if present
        data_str = request.image_base64
        if "," in data_str:
            data_str = data_str.split(",", 1)[1]

        image_bytes = base64.b64decode(data_str)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Could not decode base64 frame")

        result = pipeline.process_frame(
            frame=img,
            hazard_zone=request.hazard_zone or "General Site",
            record_violations=request.record_violations or False
        )

        _, buffer = cv2.imencode(".jpg", result["annotated_frame"], [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        b64_out = base64.b64encode(buffer).decode("utf-8")

        return {
            "status": "success",
            "annotated_base64": f"data:image/jpeg;base64,{b64_out}",
            "total_workers": result["total_workers"],
            "compliant_count": result["compliant_count"],
            "violation_count": result["violation_count"],
            "fps": result["fps"],
            "latency_ms": result["latency_ms"],
            "workers": result["workers"],
            "violations": result["violations"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/samples")
async def get_samples():
    """
    Returns list of available pre-generated test sample images for one-click testing.
    """
    sample_dir = config.DATASET_DIR / "images" / "train"
    samples = []
    if sample_dir.exists():
        for f in sample_dir.glob("*.jpg"):
            desc = "Sample PPE Test Case"
            f_name = f.name
            if "compliant" in f_name:
                desc = "Fully Compliant Worker (Hard Hat, Vest & Goggles)"
            elif "missing_hat" in f_name:
                desc = "Violation: Worker Missing Hard Hat"
            elif "missing_vest" in f_name:
                desc = "Violation: Worker Missing Safety Vest"
            elif "no_ppe" in f_name:
                desc = "Critical Violation: Worker with No Safety Gear"

            samples.append({
                "filename": f_name,
                "name": f_name.replace("_", " ").replace(".jpg", "").title(),
                "description": desc,
                "path": str(f),
            })
    return {"samples": samples}

@router.post("/process-sample/{filename}")
async def process_sample(filename: str, hazard_zone: str = "General Site"):
    """
    Runs PPE detection directly on a pre-generated sample image.
    """
    sample_path = config.DATASET_DIR / "images" / "train" / filename
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample {filename} not found")

    img = cv2.imread(str(sample_path))
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to read sample image")

    result = pipeline.process_frame(img, hazard_zone=hazard_zone, record_violations=True)

    out_filename = f"sample_{filename}"
    out_path = config.OUTPUT_DIR / out_filename
    cv2.imwrite(str(out_path), result["annotated_frame"])

    _, buffer = cv2.imencode(".jpg", result["annotated_frame"])
    b64_str = base64.b64encode(buffer).decode("utf-8")

    return {
        "status": "success",
        "output_image_url": f"/static/output/{out_filename}",
        "annotated_base64": f"data:image/jpeg;base64,{b64_str}",
        "hazard_zone": hazard_zone,
        "total_workers": result["total_workers"],
        "compliant_count": result["compliant_count"],
        "violation_count": result["violation_count"],
        "fps": result["fps"],
        "latency_ms": result["latency_ms"],
        "workers": result["workers"],
        "violations": result["violations"],
    }

