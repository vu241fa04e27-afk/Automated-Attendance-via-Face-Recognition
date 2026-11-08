"""
Automated Backend API Integration Test Suite.
Tests FastAPI endpoints using TestClient.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def run_api_tests():
    print("\n" + "=" * 60)
    print("      FASTAPI BACKEND API INTEGRATION TEST SUITE")
    print("=" * 60)

    # 1. Health check
    print("\n[TEST 1] Testing Health Check endpoint...")
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    print(f"  -> PASS: {resp.json()}")

    # 2. Login
    print("\n[TEST 2] Testing Admin Login...")
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  -> PASS: Admin logged in, bearer token acquired.")

    # 3. Get current user profile
    print("\n[TEST 3] Testing /api/auth/me...")
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200, f"Auth me failed: {me_resp.text}"
    print(f"  -> PASS: User: {me_resp.json()['admin']['username']}")

    # 4. List students
    print("\n[TEST 4] Testing /api/students...")
    students_resp = client.get("/api/students", headers=headers)
    assert students_resp.status_code == 200
    students = students_resp.json()
    print(f"  -> PASS: Found {len(students)} enrolled student(s).")

    # 5. Dashboard analytics
    print("\n[TEST 5] Testing /api/analytics/dashboard...")
    analytics_resp = client.get("/api/analytics/dashboard", headers=headers)
    assert analytics_resp.status_code == 200
    data = analytics_resp.json()
    print(f"  -> PASS: Total students: {data['total_students']}, Present today: {data['present_today']}")

    # 6. Today's attendance
    print("\n[TEST 6] Testing /api/attendance/today...")
    today_resp = client.get("/api/attendance/today", headers=headers)
    assert today_resp.status_code == 200
    print(f"  -> PASS: Today's roster records: {len(today_resp.json()['records'])}")

    # 7. Classroom image recognition
    print("\n[TEST 7] Testing /api/recognition/upload...")
    sample_img_path = PROJECT_ROOT / "dataset" / "classroom_images" / "classroom.jpg"
    with open(sample_img_path, "rb") as f:
        upload_resp = client.post(
            "/api/recognition/upload",
            files={"file": ("classroom.jpg", f, "image/jpeg")},
            headers=headers,
        )
    assert upload_resp.status_code == 200, f"Upload recognition failed: {upload_resp.text}"
    upload_data = upload_resp.json()
    assert "annotated_image_base64" in upload_data
    assert len(upload_data["detections"]) > 0
    print(f"  -> PASS: Detected {len(upload_data['detections'])} faces in classroom photo.")
    print(f"  -> Summary: Present: {upload_data['present_count']}, Absent: {upload_data['absent_count']}, Unknown: {upload_data['unknown_faces']}")

    # 8. CSV report download
    print("\n[TEST 8] Testing /api/reports/export...")
    report_resp = client.get("/api/reports/export", headers=headers)
    assert report_resp.status_code == 200
    assert "text/csv" in report_resp.headers["content-type"]
    print(f"  -> PASS: CSV exported successfully, length: {len(report_resp.content)} bytes.")

    # 9. Settings
    print("\n[TEST 9] Testing /api/settings...")
    settings_resp = client.get("/api/settings", headers=headers)
    assert settings_resp.status_code == 200
    print(f"  -> PASS: Settings: {settings_resp.json()['embedding_model']}")

    print("\n" + "=" * 60)
    print("  ALL FASTAPI BACKEND INTEGRATION TESTS PASSED (9/9)!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_api_tests()

