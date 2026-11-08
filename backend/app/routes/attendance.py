"""
Attendance Records and Management API Routes.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, status
from database.db_manager import DatabaseManager
from backend.app.schemas.schemas import AttendanceMarkRequest, AttendanceRecord
from backend.app.auth.security import get_current_admin
import datetime

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
db = DatabaseManager()


@router.get("/today")
def get_today_attendance(admin=Depends(get_current_admin)):
    """Retrieve today's attendance summary and full student roster status."""
    today = datetime.date.today().isoformat()
    all_students = db.get_all_students()
    today_records = db.get_attendance_by_date(today)
    present_map = {r["student_id"]: r for r in today_records}

    roster = []
    present_count = 0
    absent_count = 0

    for s in all_students:
        sid = s["student_id"]
        sname = s["student_name"]
        dept = s.get("department") or "General"
        yr = s.get("year") or "-"

        if sid in present_map:
            rec = present_map[sid]
            roster.append(
                {
                    "attendance_id": rec["attendance_id"],
                    "student_id": sid,
                    "student_name": sname,
                    "department": dept,
                    "year": yr,
                    "attendance_date": today,
                    "attendance_time": rec["attendance_time"],
                    "status": "PRESENT",
                    "matching_distance": rec.get("matching_distance"),
                }
            )
            present_count += 1
        else:
            roster.append(
                {
                    "attendance_id": None,
                    "student_id": sid,
                    "student_name": sname,
                    "department": dept,
                    "year": yr,
                    "attendance_date": today,
                    "attendance_time": "-",
                    "status": "ABSENT",
                    "matching_distance": None,
                }
            )
            absent_count += 1

    total = len(all_students)
    pct = round((present_count / total * 100), 1) if total > 0 else 0.0

    return {
        "date": today,
        "total_students": total,
        "present_count": present_count,
        "absent_count": absent_count,
        "attendance_percentage": pct,
        "records": roster,
    }


@router.get("/history", response_model=List[AttendanceRecord])
def get_attendance_history(
    date: Optional[str] = Query(None, description="Filter by date YYYY-MM-DD"),
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status (PRESENT/ABSENT)"),
    search: Optional[str] = Query(None, description="Search query"),
    admin=Depends(get_current_admin),
):
    """Retrieve full or filtered attendance records log."""
    records = db.get_filtered_attendance(
        target_date=date if isinstance(date, str) else None,
        student_id=student_id if isinstance(student_id, str) else None,
        department=department if isinstance(department, str) else None,
        status=status if isinstance(status, str) else None,
        search=search if isinstance(search, str) else None,
    )
    return records


@router.get("/student/{student_id}", response_model=List[AttendanceRecord])
def get_student_attendance(student_id: str, admin=Depends(get_current_admin)):
    """Retrieve attendance entries for a specific student."""
    if not db.student_exists(student_id):
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")
    return db.get_attendance_by_student(student_id)


@router.post("/mark", status_code=status.HTTP_201_CREATED)
def mark_attendance_manual(
    req: AttendanceMarkRequest,
    admin=Depends(get_current_admin),
):
    """
    Manually mark or update attendance for a student.
    Enforces uniqueness per date.
    """
    if not db.student_exists(req.student_id):
        raise HTTPException(status_code=404, detail=f"Student ID '{req.student_id}' not found.")

    success, msg = db.mark_attendance(
        student_id=req.student_id,
        attendance_date=req.attendance_date,
        attendance_time=req.attendance_time,
        status=req.status,
        matching_distance=req.matching_distance,
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg}
