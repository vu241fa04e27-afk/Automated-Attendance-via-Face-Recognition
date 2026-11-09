"""
FastAPI Application Entrypoint for SafeSite: Real-Time PPE Detection & Safety Compliance Monitoring.
Integrates YOLOv8-nano Computer Vision pipeline, IoU worker tracking, spatial containment compliance,
RESTful APIs, and static artifact serving.
"""

import sys
from pathlib import Path

# Add project root to Python path so modules and database can be imported cleanly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

import config
from backend.app.routes import (
    auth,
    detection,
    violations,
    compliance,
    settings,
    students,
    attendance,
    analytics,
    reports,
)

# Initialize FastAPI application
app = FastAPI(
    title="SafeSite & AutoAttend Unified API",
    description="Real-time Computer Vision (YOLOv8 PPE Detection + FaceNet Face Recognition) REST API.",
    version="2.0.0",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local development, Vite, and Vercel domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for viewing generated outputs and reports
app.mount("/static/output", StaticFiles(directory=str(config.OUTPUT_DIR)), name="output")
app.mount("/static/reports", StaticFiles(directory=str(config.REPORTS_DIR)), name="reports")

# Include Routers
app.include_router(auth.router)
app.include_router(detection.router)
app.include_router(violations.router)
app.include_router(compliance.router)
app.include_router(settings.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(analytics.router)
app.include_router(reports.router)

@app.get("/api/health", tags=["System Health"])
def health_check():
    """Returns application health status, active model, and database path."""
    return {
        "status": "healthy",
        "service": "SafeSite PPE Detection and Compliance System",
        "version": "2.0.0",
        "model": config.YOLO_MODEL_NAME,
        "classes": config.PPE_CLASSES,
        "database_connected": config.DB_PATH.exists(),
    }

@app.get("/", tags=["Root"])
def root_redirect():
    """Root redirect with project summary."""
    return JSONResponse(
        content={
            "project": "SafeSite: Real-Time PPE Detection and Safety Compliance Monitoring",
            "docs_url": "/docs",
            "health_url": "/api/health",
            "classes": config.PPE_CLASSES,
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
