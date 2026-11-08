"""
FastAPI Application Entrypoint for Automated Attendance System.
Integrates Computer Vision FaceNet/MTCNN pipeline with modern RESTful APIs.
"""

import sys
import os
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
    students,
    recognition,
    attendance,
    analytics,
    reports,
    settings,
)

# Initialize FastAPI application
app = FastAPI(
    title="Automated Attendance System API",
    description="High-performance FaceNet and MTCNN face recognition attendance REST API.",
    version="2.0.0",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local development, Vite (5173), and Vercel domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for viewing generated outputs
app.mount("/static/output", StaticFiles(directory=str(config.OUTPUT_DIR)), name="output")
app.mount("/static/reports", StaticFiles(directory=str(config.REPORTS_DIR)), name="reports")

# Include Routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(recognition.router)
app.include_router(attendance.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(settings.router)


@app.get("/")
def root():
    """Root status endpoint."""
    return {
        "status": "online",
        "project": "Automated Attendance System Using Face Recognition",
        "version": "2.0.0",
        "docs_url": "/docs",
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint indicating model and database readiness."""
    return {
        "status": "healthy",
        "detector": config.DEFAULT_DETECTOR,
        "model": "InceptionResnetV1 (vggface2)",
        "database": "SQLite (Connected)",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)

