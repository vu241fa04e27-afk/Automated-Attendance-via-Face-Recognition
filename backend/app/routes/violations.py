"""
FastAPI Routes for Safety Violation Audit Logs and CSV Reporting.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database.violations_db import (
    get_violations,
    resolve_violation,
    export_violations_csv,
    log_violation,
)

router = APIRouter(prefix="/api/violations", tags=["Violation Audit Logs"])

class ResolveRequest(BaseModel):
    notes: Optional[str] = "Resolved by safety officer"

@router.get("")
async def list_violations(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    date: Optional[str] = Query(None)
):
    """
    Returns paginated list of logged safety violations.
    """
    records = get_violations(limit=limit, offset=offset, status=status, date_filter=date)
    return {
        "status": "success",
        "count": len(records),
        "violations": records,
    }

@router.post("/{violation_id}/resolve")
async def resolve(violation_id: int, req: ResolveRequest):
    """
    Marks a safety violation as resolved with inspection notes.
    """
    success = resolve_violation(violation_id, notes=req.notes or "Resolved")
    if not success:
        raise HTTPException(status_code=404, detail="Violation record not found")
    return {"status": "success", "message": f"Violation #{violation_id} marked as RESOLVED"}

@router.get("/export-csv")
async def download_csv():
    """
    Exports all safety violation records as a downloadable CSV report.
    """
    csv_file_path = export_violations_csv()
    return FileResponse(
        path=csv_file_path,
        media_type="text/csv",
        filename="safesite_ppe_violations_audit.csv",
    )

