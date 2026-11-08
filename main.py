"""
Automated Attendance System Using Face Recognition
Main Terminal Menu and Entrypoint.
Provides a clean, interactive command-line interface.
"""

import os
import sys
import datetime
from pathlib import Path
from typing import List, Optional

# Ensure project root is in Python path
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


def print_header(title: str = "AUTOMATED ATTENDANCE SYSTEM\n          USING FACE RECOGNITION") -> None:
    """Print standard formatted system header."""
    print("\n" + "=" * 50)
    print(f"       {title}")
    print("=" * 50)


def display_menu() -> None:
    """Display the main terminal menu options."""
    print("1. Register New Student")
    print("2. Capture Student Face Images")
    print("3. View Registered Students")
    print("4. Take Attendance Using Classroom Image")
    print("5. Take Attendance Using Webcam")
    print("6. View Today's Attendance")
    print("7. View Attendance History")
    print("8. Generate Attendance Report")
    print("9. View Attendance Statistics")
    print("10. Delete Student")
    print("11. Exit")
    print()


class AttendanceApp:
    """Main CLI Application Controller."""

    def __init__(self):
        print("\n[System Initializing] Loading database and neural network models...")
        self.db = DatabaseManager()
        self.detector = FaceDetector()
        self.extractor = FaceEmbeddingExtractor()
        self.matcher = FaceMatcher()

        self.registration_mgr = StudentRegistrationManager(
            db_manager=self.db, detector=self.detector, extractor=self.extractor
        )
        self.attendance_mgr = AttendanceManager(
            db_manager=self.db,
            detector=self.detector,
            extractor=self.extractor,
            matcher=self.matcher,
        )
        self.webcam_mgr = WebcamAttendanceManager(
            db_manager=self.db,
            detector=self.detector,
            extractor=self.extractor,
            matcher=self.matcher,
        )
        self.reporter = AttendanceReporter(db_manager=self.db)
        print("[System Ready] All components loaded successfully.\n")

    def run(self) -> None:
        """Main execution loop for terminal menu."""
        while True:
            try:
                print_header()
                display_menu()
                choice = input("Enter your choice (1-11): ").strip()

                if choice == "1":
                    self.handle_register_student()
                elif choice == "2":
                    self.handle_capture_additional_images()
                elif choice == "3":
                    self.handle_view_students()
                elif choice == "4":
                    self.handle_classroom_attendance()
                elif choice == "5":
                    self.handle_webcam_attendance()
                elif choice == "6":
                    self.handle_view_today_attendance()
                elif choice == "7":
                    self.handle_view_attendance_history()
                elif choice == "8":
                    self.handle_generate_report()
                elif choice == "9":
                    self.handle_view_statistics()
                elif choice == "10":
                    self.handle_delete_student()
                elif choice == "11":
                    print("\n" + "=" * 50)
                    print("Thank you for using the Automated Attendance System.")
                    print("Exiting application. Goodbye!")
                    print("=" * 50 + "\n")
                    break
                else:
                    print("\n[Invalid Selection] Please enter a valid number between 1 and 11.")
            except KeyboardInterrupt:
                print("\n\n[Interrupted] Returning to main menu...")
            except Exception as e:
                print(f"\n[Unexpected Error] An unexpected error occurred: {e}")

            input("\nPress ENTER to continue to the main menu...")

    # =========================================================================
    # Menu Action Handlers
    # =========================================================================

    def handle_register_student(self) -> None:
        """Menu 1: Register a new student."""
        print_header("STUDENT REGISTRATION")
        student_id = input("Enter Student ID: ").strip()
        if not student_id:
            print("[Error] Student ID cannot be empty.")
            return

        if self.db.student_exists(student_id):
            print(f"[Error] A student with ID '{student_id}' is already registered.")
            return

        student_name = input("Enter Student Name: ").strip()
        if not student_name:
            print("[Error] Student Name cannot be empty.")
            return

        department = input("Enter Department (Optional, e.g., Computer Science): ").strip() or None
        year = input("Enter Academic Year (Optional, e.g., 3rd Year): ").strip() or None

        print("\nSelect Face Enrollment Method:")
        print("  1. Capture Face Images via Live Webcam")
        print("  2. Provide Existing Image File Path(s)")
        print("  3. Cancel Registration")
        method_choice = input("Enter choice (1-3): ").strip()

        if method_choice == "1":
            samples_input = input("Enter number of face samples to capture (default 3): ").strip()
            target_samples = int(samples_input) if samples_input.isdigit() else 3
            success, msg = self.registration_mgr.register_new_student(
                student_id=student_id,
                student_name=student_name,
                department=department,
                year=year,
                use_webcam=True,
                target_samples=target_samples,
            )
            print(f"\n{msg}")

        elif method_choice == "2":
            print("\nEnter one or more image file paths.")
            print("(Separate multiple paths with commas, or enter a folder path)")
            path_input = input("Image path(s): ").strip()
            if not path_input:
                print("[Error] No path provided. Registration canceled.")
                return

            image_paths = []
            raw_paths = [p.strip() for p in path_input.split(",") if p.strip()]
            for p_str in raw_paths:
                p_obj = Path(p_str.strip('"').strip("'"))
                if p_obj.is_dir():
                    # Collect all image files inside folder
                    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
                    for f in p_obj.iterdir():
                        if f.suffix.lower() in valid_exts:
                            image_paths.append(str(f))
                elif p_obj.is_file():
                    image_paths.append(str(p_obj))
                else:
                    print(f"[Notice] File/Directory does not exist: {p_str}")

            if not image_paths:
                print("[Error] No valid image files found. Registration canceled.")
                return

            success, msg = self.registration_mgr.register_new_student(
                student_id=student_id,
                student_name=student_name,
                department=department,
                year=year,
                image_paths=image_paths,
                use_webcam=False,
            )
            print(f"\n{msg}")

        elif method_choice == "3":
            print("[Notice] Student registration canceled.")
        else:
            print("[Error] Invalid selection.")

    def handle_capture_additional_images(self) -> None:
        """Menu 2: Capture/Add more face samples for an existing student."""
        print_header("CAPTURE STUDENT FACE IMAGES")
        student_id = input("Enter Student ID: ").strip()
        if not student_id:
            print("[Error] Student ID cannot be empty.")
            return

        student = self.db.get_student(student_id)
        if not student:
            print(f"[Error] Student ID '{student_id}' is not registered.")
            print("Please register the student first using Option 1.")
            return

        existing_samples = self.db.get_embedding_count(student_id)
        print(f"\nStudent: {student['student_name']} (ID: {student_id})")
        print(f"Current enrolled face samples: {existing_samples}")

        print("\nSelect Image Source:")
        print("  1. Capture Additional Samples via Webcam")
        print("  2. Provide Image File Path(s)")
        print("  3. Cancel")
        choice = input("Enter choice (1-3): ").strip()

        student_dir = config.STUDENT_IMAGES_DIR / student_id
        student_dir.mkdir(parents=True, exist_ok=True)

        if choice == "1":
            samples_input = input("Enter number of additional samples to capture (default 2): ").strip()
            target_samples = int(samples_input) if samples_input.isdigit() else 2
            faces = self.registration_mgr.capture_faces_from_webcam(
                student_id=student_id,
                target_samples=target_samples,
                save_dir=student_dir,
            )
            added = 0
            for face in faces:
                emb = self.extractor.extract_embedding(face)
                if self.db.add_embedding(student_id, emb):
                    added += 1
            print(f"\n[Success] Added {added} new face embedding sample(s) for {student['student_name']}.")

        elif choice == "2":
            path_input = input("Enter image file path(s) (comma separated): ").strip()
            raw_paths = [p.strip().strip('"').strip("'") for p in path_input.split(",") if p.strip()]
            faces = self.registration_mgr.process_image_files(raw_paths, save_dir=student_dir)
            added = 0
            for face in faces:
                emb = self.extractor.extract_embedding(face)
                if self.db.add_embedding(student_id, emb):
                    added += 1
            print(f"\n[Success] Added {added} new face embedding sample(s) for {student['student_name']}.")

        elif choice == "3":
            print("[Notice] Operation canceled.")
        else:
            print("[Error] Invalid selection.")

    def handle_view_students(self) -> None:
        """Menu 3: View all registered students."""
        print_header("REGISTERED STUDENTS DIRECTORY")
        students = self.db.get_all_students()

        if not students:
            print("\n[Notice] No students are currently registered in the database.")
            print("Use Option 1 from the main menu to enroll students.")
            return

        print(f"{'Student ID':<12} {'Name':<22} {'Department':<18} {'Year':<10} {'Enrolled Date':<14} {'Samples':<8}")
        print("-" * 88)

        for s in students:
            sid = s["student_id"]
            name = s["student_name"]
            dept = s.get("department") or "-"
            yr = s.get("year") or "-"
            date_reg = s.get("registration_date") or "-"
            sample_count = self.db.get_embedding_count(sid)

            print(f"{sid:<12} {name:<22} {dept:<18} {yr:<10} {date_reg:<14} {sample_count:<8}")

        print("-" * 88)
        print(f"Total Enrolled Students: {len(students)}")

    def handle_classroom_attendance(self) -> None:
        """Menu 4: Take attendance using classroom photograph."""
        print_header("CLASSROOM IMAGE ATTENDANCE")

        # Check registered students
        if not self.db.get_all_students():
            print("[Warning] No registered students found. Please register students first.")
            return

        print("Example classroom paths:")
        print("  dataset/classroom_images/classroom.jpg")
        print("  dataset/classroom_images/group_photo.jpg\n")

        image_path = input("Enter classroom image path: ").strip()
        if not image_path:
            # Check default classroom image if exists
            default_test_path = config.CLASSROOM_IMAGES_DIR / "classroom.jpg"
            if default_test_path.exists():
                print(f"[Using default sample]: {default_test_path}")
                image_path = str(default_test_path)
            else:
                print("[Error] Image path cannot be empty.")
                return

        # Optional date override
        date_input = input("Enter attendance date (YYYY-MM-DD) or press ENTER for today: ").strip()
        attendance_date = date_input if date_input else None

        # Optional metric selection
        print("\nSelect Matching Metric:")
        print(f"  1. Euclidean Distance (Default, threshold: {config.EUCLIDEAN_THRESHOLD})")
        print(f"  2. Cosine Similarity (threshold: {config.COSINE_THRESHOLD})")
        metric_choice = input("Enter choice (1 or 2, default 1): ").strip()
        metric = "cosine" if metric_choice == "2" else "euclidean"
        self.matcher.metric = metric

        # Ask whether to display GUI window
        gui_choice = input("Display annotated image window? (Y/n): ").strip().lower()
        show_gui = gui_choice != "n"

        # Process image attendance
        self.attendance_mgr.process_classroom_image(
            image_path=image_path,
            attendance_date=attendance_date,
            display_image=show_gui,
        )

    def handle_webcam_attendance(self) -> None:
        """Menu 5: Live webcam attendance stream."""
        print_header("LIVE WEBCAM ATTENDANCE")
        if not self.db.get_all_students():
            print("[Warning] No registered students found. Please register students first.")
            return

        self.webcam_mgr.run_live_attendance()

    def handle_view_today_attendance(self) -> None:
        """Menu 6: View attendance for today."""
        print_header("TODAY'S ATTENDANCE")
        self.reporter.view_today_attendance()

    def handle_view_attendance_history(self) -> None:
        """Menu 7: View attendance history."""
        print_header("ATTENDANCE HISTORY")
        print("1. View Complete Attendance Log")
        print("2. Filter Attendance by Specific Date")
        print("3. Filter Attendance by Student ID")
        print("4. Return to Main Menu")
        sub_choice = input("Enter choice (1-4): ").strip()

        if sub_choice == "1":
            self.reporter.view_attendance_history()
        elif sub_choice == "2":
            target_date = input("Enter date (YYYY-MM-DD): ").strip()
            if target_date:
                self.reporter.view_attendance_by_date(target_date)
            else:
                print("[Error] Date cannot be empty.")
        elif sub_choice == "3":
            student_id = input("Enter Student ID: ").strip()
            if student_id:
                self.reporter.view_attendance_by_student(student_id)
            else:
                print("[Error] Student ID cannot be empty.")
        elif sub_choice == "4":
            return
        else:
            print("[Error] Invalid selection.")

    def handle_generate_report(self) -> None:
        """Menu 8: Generate CSV attendance report using Pandas."""
        print_header("GENERATE ATTENDANCE REPORT")
        print("1. Export Today's Attendance (with Present and Absent breakdown)")
        print("2. Export Attendance for a Specific Date")
        print("3. Export Complete Historical Attendance Log")
        print("4. Cancel")
        rep_choice = input("Enter choice (1-4): ").strip()

        if rep_choice == "1":
            today = datetime.date.today().isoformat()
            self.reporter.export_attendance_report(target_date=today)
        elif rep_choice == "2":
            target_date = input("Enter target date (YYYY-MM-DD): ").strip()
            if target_date:
                self.reporter.export_attendance_report(target_date=target_date)
            else:
                print("[Error] Date cannot be empty.")
        elif rep_choice == "3":
            self.reporter.export_attendance_report(target_date=None)
        elif rep_choice == "4":
            print("[Notice] Report generation canceled.")
        else:
            print("[Error] Invalid selection.")

    def handle_view_statistics(self) -> None:
        """Menu 9: View attendance statistics and generate charts."""
        print_header("ATTENDANCE STATISTICS & ANALYTICS")
        self.reporter.generate_attendance_statistics(save_chart=True)

    def handle_delete_student(self) -> None:
        """Menu 10: Delete a registered student and their biometric embeddings."""
        print_header("DELETE STUDENT RECORD")
        student_id = input("Enter Student ID to delete: ").strip()
        if not student_id:
            print("[Error] Student ID cannot be empty.")
            return

        student = self.db.get_student(student_id)
        if not student:
            print(f"[Error] Student ID '{student_id}' does not exist.")
            return

        embedding_count = self.db.get_embedding_count(student_id)
        print("\nStudent Details Found:")
        print(f"  ID:          {student['student_id']}")
        print(f"  Name:        {student['student_name']}")
        print(f"  Department:  {student.get('department') or 'N/A'}")
        print(f"  Year:        {student.get('year') or 'N/A'}")
        print(f"  Face Samples:{embedding_count}")

        confirm = input(
            f"\n[CONFIRMATION] Are you sure you want to permanently delete {student['student_name']} "
            f"and ALL associated facial embeddings and attendance records? (y/N): "
        ).strip().lower()

        if confirm in ("y", "yes"):
            # Delete from database (cascades to embeddings and attendance)
            success = self.db.delete_student(student_id)
            if success:
                # Clean up stored face images on disk
                student_dir = config.STUDENT_IMAGES_DIR / student_id
                if student_dir.exists():
                    try:
                        for file in student_dir.iterdir():
                            file.unlink()
                        student_dir.rmdir()
                    except Exception as e:
                        print(f"[Notice] Could not clean up image directory: {e}")

                print(f"\n[Success] Student '{student['student_name']}' (ID: {student_id}) has been deleted successfully.")
            else:
                print(f"\n[Error] Failed to delete student from database.")
        else:
            print("\n[Notice] Deletion aborted by user.")


def main():
    """Application entrypoint."""
    try:
        app = AttendanceApp()
        app.run()
    except Exception as e:
        print(f"\n[Fatal Error] System failed to initialize: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

