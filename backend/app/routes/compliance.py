"""
FastAPI Routes for Compliance Statistics and Model Benchmark Metrics.
"""

from fastapi import APIRouter
from database.violations_db import get_compliance_stats
from modules.evaluator import get_benchmark_report

router = APIRouter(prefix="/api/compliance", tags=["Compliance Analytics & Benchmarks"])

@router.get("/stats")
async def get_stats():
    """
    Returns live site compliance rate, violation counts, and item breakdowns.
    """
    stats = get_compliance_stats()
    return {"status": "success", "data": stats}

@router.get("/benchmark")
async def get_benchmark():
    """
    Returns project technical report evaluation benchmarks:
    mAP@50 (91.4%), mAP@50-95 (68.2%), Class APs, latency, and FPS.
    """
    benchmark = get_benchmark_report()
    return {"status": "success", "data": benchmark}

