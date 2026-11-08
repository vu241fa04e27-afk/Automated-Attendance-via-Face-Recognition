"""
Direct route function integration test.
Tests backend business logic without needing httpx.
"""

import sys
import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.routes import auth, students, recognition, attendance, analytics, reports, settings
from backend.app.schemas.schemas import LoginRequest
import cv2

def run_direct_tests():
    print("\n" + "=" * 60)
    print("      FASTAPI ROUTE LOGIC INTEGRATION TEST SUITE")
    print("=" * 60)

    # 1. Login
    print("\n[TEST 1] Testing Admin Login logic...")
    login_res = auth.login(LoginRequest(username="admin", password="admin123"))
    assert "access_token" in login_res
    admin = login_res["admin"]
    print(f"  -> PASS: Logged in as: {admin['username']}")

    # 2. List students
    print("\n[TEST 2] Testing List Students route...")
    student_list = students.list_students(admin=admin)
    assert len(student_list) >= 1
    print(f"  -> PASS: Found {len(student_list)} students. First: {student_list[0].student_name}")

    # 3. Dashboard Analytics
    print("\n[TEST 3] Testing Dashboard Analytics route...")
    dash_data = analytics.get_dashboard_data(admin=admin)
    assert dash_data["total_students"] >= 1
    print(f"  -> PASS: Enrolled: {dash_data['total_students']}, Daily trends: {len(dash_data['daily_trends'])} days")

    # 4. Today Attendance
    print("\n[TEST 4] Testing Today's Attendance route...")
    today_data = attendance.get_today_attendance(admin=admin)
    assert "records" in today_data
    print(f"  -> PASS: Attendance roster has {len(today_data['records'])} entries.")

    # 5. Image Recognition
    print("\n[TEST 5] Testing Classroom Image Recognition logic...")
    img_path = PROJECT_ROOT / "dataset" / "classroom_images" / "classroom.jpg"
    img = cv2.imread(str(img_path))
    res = recognition.attendance_mgr.process_image_array(img, save_output=False)
    assert res is not None
    assert len(res["detections"]) > 0
    print(f"  -> PASS: Detected {len(res['detections'])} faces in image. Present: {res['present_count']}, Absent: {res['absent_count']}")

    # 6. Settings
    print("\n[TEST 6] Testing System Settings route...")
    s_data = settings.get_system_settings(admin=admin)
    assert "euclidean_threshold" in s_data
    print(f"  -> PASS: Model: {s_data['embedding_model']}, Euclidean Threshold: {s_data['euclidean_threshold']}")

    print("\n" + "=" * 60)
    print("  ALL DIRECT BACKEND ROUTE TESTS PASSED (6/6)!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_direct_tests()

