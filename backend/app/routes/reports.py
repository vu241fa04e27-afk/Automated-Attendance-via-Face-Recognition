"""
Attendance CSV Reports Export API Route.
Uses Pandas to stream download reports to the client.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from modules.reports import AttendanceReporter
from database.db_manager import DatabaseManager
from backend.app.auth.security import get_current_admin
import os

router = APIRouter(prefix="/api/reports", tags=["Reports"])
db = DatabaseManager()
reporter = AttendanceReporter(db_manager=db)


@router.get("/export")
def export_csv_report(
    date: Optional[str] = Query(None, description="Target date for report (YYYY-MM-DD). If omitted, exports all history."),
    admin=Depends(get_current_admin),
):
    """
    Generate and stream an attendance CSV file for direct browser download.
    """
    csv_file_path = reporter.export_attendance_report(target_date=date)
    if not csv_file_path or not os.path.exists(csv_file_path):
        raise HTTPException(status_code=404, detail="No attendance records available to export.")

    filename = os.path.basename(csv_file_path)
    return FileResponse(
        path=csv_file_path,
        media_type="text/csv",
        filename=filename,
    )

