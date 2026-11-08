"""
Student Management and Face Enrollment API Routes.
Integrates with SQLite, MTCNN, and FaceNet.
"""

import os
import cv2
import numpy as np
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, status
from database.db_manager import DatabaseManager
from modules.face_detection import FaceDetector
from modules.face_embedding import FaceEmbeddingExtractor
from modules.student_registration import StudentRegistrationManager
from backend.app.schemas.schemas import StudentCreate, StudentUpdate, StudentResponse
from backend.app.auth.security import get_current_admin
import config

router = APIRouter(prefix="/api/students", tags=["Students"])
db = DatabaseManager()
detector = FaceDetector()
extractor = FaceEmbeddingExtractor()
registration_mgr = StudentRegistrationManager(db_manager=db, detector=detector, extractor=extractor)


@router.get("", response_model=List[StudentResponse])
def list_students(
    search: Optional[str] = Query(None, description="Search by name or ID"),
    department: Optional[str] = Query(None, description="Filter by department"),
    year: Optional[str] = Query(None, description="Filter by year"),
    admin=Depends(get_current_admin),
):
    """List all registered students with sample counts and optional filters."""
    search_str = search if isinstance(search, str) else None
    dept_str = department if isinstance(department, str) else None
    year_str = year if isinstance(year, str) else None

    all_students = db.get_all_students()
    results = []

    for s in all_students:
        sid = s["student_id"]
        sname = s["student_name"]
        dept = s.get("department") or ""
        yr = s.get("year") or ""

        # Filter logic
        if dept_str and dept.lower() != dept_str.lower():
            continue
        if year_str and yr.lower() != year_str.lower():
            continue
        if search_str:
            q = search_str.lower()
            if q not in sid.lower() and q not in sname.lower():
                continue

        count = db.get_embedding_count(sid)
        results.append(
            StudentResponse(
                student_id=sid,
                student_name=sname,
                department=dept or None,
                year=yr or None,
                registration_date=s.get("registration_date", ""),
                face_samples_count=count,
            )
        )

    return results


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_student_with_faces(
    student_id: str = Form(...),
    student_name: str = Form(...),
    department: Optional[str] = Form(None),
    year: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    admin=Depends(get_current_admin),
):
    """
    Register a new student with face photographs.
    Detects faces, generates FaceNet embeddings, and stores in SQLite.
    """
    sid = student_id.strip()
    sname = student_name.strip()

    if not sid:
        raise HTTPException(status_code=400, detail="Student ID cannot be empty.")
    if not sname:
        raise HTTPException(status_code=400, detail="Student Name cannot be empty.")
    if db.student_exists(sid):
        raise HTTPException(status_code=400, detail=f"Student ID '{sid}' is already registered.")

    # Read and decode uploaded face images
    image_arrays: List[np.ndarray] = []
    for file in images:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None and img.size > 0:
            image_arrays.append(img)

    if not image_arrays:
        # If no face photos were provided, register student details only
        success = db.register_student(
            student_id=sid,
            student_name=sname,
            department=department,
            year=year,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register student record in database.")
        return {
            "success": True,
            "message": f"Student '{sname}' registered successfully (without face images).",
            "samples_enrolled": 0,
        }

    # Process faces and extract embeddings
    success, msg, count = registration_mgr.register_student_from_images(
        student_id=sid,
        student_name=sname,
        department=department,
        year=year,
        images_bgr=image_arrays,
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": msg,
        "samples_enrolled": count,
    }


@router.get("/{student_id}")
def get_student_details(student_id: str, admin=Depends(get_current_admin)):
    """Retrieve individual student profile, attendance summary, and sample count."""
    student = db.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    sample_count = db.get_embedding_count(student_id)
    history = db.get_attendance_by_student(student_id)
    distinct_dates = db.get_distinct_attendance_dates()
    total_sessions = len(distinct_dates)
    attended_count = len(history)
    pct = round((attended_count / total_sessions * 100), 1) if total_sessions > 0 else 0.0

    return {
        "student": student,
        "face_samples_count": sample_count,
        "attended_sessions": attended_count,
        "total_sessions": total_sessions,
        "attendance_percentage": pct,
        "recent_history": history[:5],
    }


@router.put("/{student_id}")
def update_student_info(
    student_id: str,
    update_data: StudentUpdate,
    admin=Depends(get_current_admin),
):
    """Update student profile details."""
    if not db.student_exists(student_id):
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    success = db.update_student(
        student_id=student_id,
        student_name=update_data.student_name,
        department=update_data.department,
        year=update_data.year,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update student profile.")

    return {"message": f"Student '{update_data.student_name}' updated successfully."}


@router.delete("/{student_id}")
def delete_student_record(student_id: str, admin=Depends(get_current_admin)):
    """
    Delete a student record permanently.
    Cascades to delete face embeddings, attendance records, and stored photos.
    """
    student = db.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    success = db.delete_student(student_id)
    if not success:
        raise HTTPException(status_code=500, detail="Database deletion failed.")

    # Remove stored image directory on disk
    student_dir = config.STUDENT_IMAGES_DIR / student_id
    if student_dir.exists():
        try:
            for f in student_dir.iterdir():
                f.unlink()
            student_dir.rmdir()
        except Exception as e:
            print(f"[Notice] Could not clean up disk photos: {e}")

    return {"message": f"Student '{student['student_name']}' (ID: {student_id}) deleted successfully."}


@router.post("/{student_id}/faces")
async def add_student_face_samples(
    student_id: str,
    images: List[UploadFile] = File(...),
    admin=Depends(get_current_admin),
):
    """Add additional face photographs and embeddings to an existing student."""
    student = db.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    student_dir = config.STUDENT_IMAGES_DIR / student_id
    student_dir.mkdir(parents=True, exist_ok=True)

    added_count = 0
    existing_count = db.get_embedding_count(student_id)

    for idx, file in enumerate(images):
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None or img.size == 0:
            continue

        detections = detector.detect_faces(img)
        if not detections:
            continue
        if len(detections) > 1:
            detections.sort(key=lambda d: d["box"][2] * d["box"][3], reverse=True)

        face_rgb = detections[0]["cropped_face"]
        emb = extractor.extract_embedding(face_rgb)
        if db.add_embedding(student_id, emb):
            added_count += 1
            save_path = student_dir / f"sample_{existing_count + added_count}.jpg"
            cv2.imwrite(str(save_path), cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR))

    if added_count == 0:
        raise HTTPException(status_code=400, detail="No valid faces detected in the provided images.")

    return {
        "success": True,
        "message": f"Added {added_count} new face sample(s) for {student['student_name']}.",
        "total_samples": existing_count + added_count,
    }
