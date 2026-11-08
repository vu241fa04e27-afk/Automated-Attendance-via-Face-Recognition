"""
Analytics and Statistics API Routes for Dashboard and Charts.
"""

from fastapi import APIRouter, Depends
from database.db_manager import DatabaseManager
from backend.app.auth.security import get_current_admin
import datetime

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
db = DatabaseManager()


@router.get("/dashboard")
def get_dashboard_data(admin=Depends(get_current_admin)):
    """Retrieve all high-level statistics, 7-day daily trends, and recent records."""
    return db.get_dashboard_analytics()


@router.get("/daily")
def get_daily_trends(days: int = 14, admin=Depends(get_current_admin)):
    """Retrieve daily attendance metrics for the past N days."""
    all_students = db.get_all_students()
    total_students = len(all_students)
    trends = []

    for i in range(days - 1, -1, -1):
        day_d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        records = db.get_attendance_by_date(day_d)
        present_count = len({r["student_id"] for r in records})
        absent_count = max(0, total_students - present_count)
        pct = round((present_count / total_students * 100), 1) if total_students > 0 else 0.0

        trends.append(
            {
                "date": day_d,
                "label": datetime.date.fromisoformat(day_d).strftime("%b %d"),
                "present": present_count,
                "absent": absent_count,
                "rate": pct,
            }
        )

    return {"days": days, "trends": trends}


@router.get("/student-percentages")
def get_student_percentages(admin=Depends(get_current_admin)):
    """Calculate overall attendance percentage for each enrolled student."""
    all_students = db.get_all_students()
    distinct_dates = db.get_distinct_attendance_dates()
    total_sessions = len(distinct_dates)
    results = []

    for s in all_students:
        sid = s["student_id"]
        attended = len(db.get_attendance_by_student(sid))
        pct = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 0.0
        results.append(
            {
                "student_id": sid,
                "student_name": s["student_name"],
                "department": s.get("department") or "General",
                "attended": attended,
                "total_sessions": total_sessions,
                "percentage": pct,
            }
        )

    return {"total_sessions": total_sessions, "students": results}

