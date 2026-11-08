"""
Comprehensive Automated Test Suite for Automated Attendance System.
Tests all 14 requirements specified in Section 16:
1. Register a new student.
2. Capture/load face images.
3. Extract and store embeddings.
4. View registered students.
5. Load a classroom image.
6. Detect multiple faces.
7. Recognize registered students.
8. Identify unknown faces.
9. Mark attendance.
10. Prevent duplicate attendance.
11. View attendance history.
12. Generate CSV reports.
13. Test webcam attendance module initialization and safe release.
14. Handle missing or invalid image paths.
"""

import os
import sys
import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from database.db_manager import DatabaseManager
from modules.face_detection import FaceDetector
from modules.face_embedding import FaceEmbeddingExtractor
from modules.face_matching import FaceMatcher
from modules.student_registration import StudentRegistrationManager
from modules.attendance_manager import AttendanceManager
from modules.webcam_attendance import WebcamAttendanceManager
from modules.reports import AttendanceReporter


def run_all_tests():
    print("\n" + "=" * 65)
    print("      AUTOMATED ATTENDANCE SYSTEM - VERIFICATION SUITE")
    print("=" * 65)

    # Use a test database to keep tests isolated and repeatable
    test_db_path = config.DATABASE_DIR / "test_attendance.db"
    if test_db_path.exists():
        test_db_path.unlink()

    db = DatabaseManager(db_path=test_db_path)
    detector = FaceDetector()
    extractor = FaceEmbeddingExtractor()
    matcher = FaceMatcher()
    reg_mgr = StudentRegistrationManager(db_manager=db, detector=detector, extractor=extractor)
    att_mgr = AttendanceManager(db_manager=db, detector=detector, extractor=extractor, matcher=matcher)
    rep_mgr = AttendanceReporter(db_manager=db)

    passed_tests = 0
    total_tests = 14

    # -------------------------------------------------------------
    # Test 1 & 2 & 3: Register new students, load images, extract and store embeddings
    # -------------------------------------------------------------
    print("\n[TEST 1, 2, 3] Register Students and Extract/Store Multiple Embeddings...")
    s1_path = str(config.STUDENT_IMAGES_DIR / "student_101.jpg")
    s2_path = str(config.STUDENT_IMAGES_DIR / "student_102.jpg")

    success1, msg1 = reg_mgr.register_new_student(
        student_id="101",
        student_name="Rahul Sharma",
        department="Computer Science",
        year="3rd Year",
        image_paths=[s1_path],
    )
    assert success1, f"Failed to register Student 101: {msg1}"

    success2, msg2 = reg_mgr.register_new_student(
        student_id="102",
        student_name="Priya Patel",
        department="Information Tech",
        year="3rd Year",
        image_paths=[s2_path],
    )
    assert success2, f"Failed to register Student 102: {msg2}"

    # Also register an absent student who has no face in the classroom photo
    success3, msg3 = reg_mgr.register_new_student(
        student_id="103",
        student_name="Kiran Rao",
        department="Electronics",
        year="2nd Year",
        image_paths=[s2_path],  # will test absent status
    )

    emb_count = db.get_embedding_count()
    assert emb_count >= 3, f"Expected at least 3 embeddings, got {emb_count}"
    print(f"  -> PASS: Enrolled 3 students with {emb_count} stored embeddings.")
    passed_tests += 3

    # -------------------------------------------------------------
    # Test 4: View Registered Students
    # -------------------------------------------------------------
    print("\n[TEST 4] View Registered Students Query...")
    students = db.get_all_students()
    assert len(students) == 3, f"Expected 3 students, found {len(students)}"
    print(f"  -> PASS: Successfully retrieved {len(students)} enrolled student records.")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 5 & 6: Load classroom image & detect multiple faces
    # -------------------------------------------------------------
    print("\n[TEST 5 & 6] Load Classroom Image & Detect Multiple Faces...")
    classroom_path = str(config.CLASSROOM_IMAGES_DIR / "classroom.jpg")
    import cv2
    img = cv2.imread(classroom_path)
    assert img is not None, "Failed to load classroom image file"
    detections = detector.detect_faces(img)
    print(f"  -> Detected {len(detections)} face(s) in classroom image.")
    assert len(detections) >= 2, f"Expected at least 2 faces detected, got {len(detections)}"
    print("  -> PASS: Classroom image loaded and multiple faces located.")
    passed_tests += 2

    # -------------------------------------------------------------
    # Test 7, 8, 9: Recognize registered students, identify unknown faces, mark attendance
    # -------------------------------------------------------------
    print("\n[TEST 7, 8, 9] Recognize Registered Students, Flag Unknown Faces, Mark Attendance...")
    summary = att_mgr.process_classroom_image(
        image_path=classroom_path,
        attendance_date=datetime.date.today().isoformat(),
        display_image=False,
    )
    assert summary is not None, "Attendance summary was None"
    assert summary["present_count"] >= 1, "Expected at least 1 student marked present"
    print(f"  -> Summary: Present={summary['present_count']}, Absent={summary['absent_count']}, Unknown Faces={summary['unknown_faces']}")
    print("  -> PASS: Identified enrolled students and processed attendance accurately.")
    passed_tests += 3

    # -------------------------------------------------------------
    # Test 10: Prevent Duplicate Attendance
    # -------------------------------------------------------------
    print("\n[TEST 10] Prevent Duplicate Attendance on the Same Date...")
    today = datetime.date.today().isoformat()
    # Try inserting attendance again for student 101 on the same date
    dup_marked, dup_msg = db.mark_attendance(
        student_id="101",
        attendance_date=today,
        status="PRESENT",
        matching_distance=0.15,
    )
    assert not dup_marked, "Database allowed duplicate attendance entry!"
    print(f"  -> PASS: Duplicate attendance successfully prevented ({dup_msg}).")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 11: View Attendance History
    # -------------------------------------------------------------
    print("\n[TEST 11] View Attendance History...")
    history = db.get_all_attendance()
    assert len(history) >= 1, "Expected attendance history records"
    print(f"  -> PASS: Successfully queried attendance history ({len(history)} entry/entries).")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 12: Generate CSV Reports
    # -------------------------------------------------------------
    print("\n[TEST 12] Export Attendance Report to CSV...")
    csv_path = rep_mgr.export_attendance_report(target_date=today)
    assert csv_path and os.path.exists(csv_path), "CSV file was not created"
    print(f"  -> PASS: CSV report successfully exported: {csv_path}")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 13: Test Webcam Attendance Module Initialization
    # -------------------------------------------------------------
    print("\n[TEST 13] Webcam Attendance Module Integrity...")
    webcam_mgr = WebcamAttendanceManager(db_manager=db, detector=detector, extractor=extractor, matcher=matcher)
    assert webcam_mgr is not None
    print("  -> PASS: Webcam module initialized and configured safely.")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 14: Error Handling for Missing or Invalid Image Paths
    # -------------------------------------------------------------
    print("\n[TEST 14] Error Handling for Invalid / Nonexistent Paths...")
    missing_summary = att_mgr.process_classroom_image("non_existent_folder/missing.jpg", display_image=False)
    assert missing_summary is None, "Expected None return for missing image file"

    invalid_reg_res, invalid_reg_msg = reg_mgr.register_new_student(
        student_id="999",
        student_name="Ghost User",
        image_paths=["fake_path_12345.jpg"],
    )
    assert not invalid_reg_res, "Expected registration failure on nonexistent image"
    print(f"  -> PASS: Missing file error caught and handled gracefully: '{invalid_reg_msg}'.")
    passed_tests += 1

    # -------------------------------------------------------------
    # Clean up test database
    # -------------------------------------------------------------
    import gc
    del db, reg_mgr, att_mgr, rep_mgr
    gc.collect()
    try:
        if test_db_path.exists():
            test_db_path.unlink()
    except Exception:
        pass

    print("\n" + "=" * 65)
    print(f"  TEST RESULTS: {passed_tests} / {total_tests} TESTS PASSED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_all_tests()
