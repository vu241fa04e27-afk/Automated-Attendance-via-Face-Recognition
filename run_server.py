"""
Server runner script for Automated Attendance System FastAPI Backend.
Executes uvicorn server on http://localhost:8000
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    print("\n" + "=" * 60)
    print("  STARTING AUTOMATED ATTENDANCE SYSTEM FASTAPI BACKEND")
    print("=" * 60)
    print(f"  Server URL:    http://{host}:{port}")
    print(f"  API Docs:      http://{host}:{port}/docs")
    print(f"  Interactive:   http://{host}:{port}/redoc")
    print("=" * 60 + "\n")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)

