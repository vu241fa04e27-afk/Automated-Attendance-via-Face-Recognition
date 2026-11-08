"""
Attendance Manager Module for Automated Attendance System.
Handles batch classroom image attendance processing:
- Detects all visible student faces.
- Extracts embeddings and matches identities.
- Marks recognized students as PRESENT in SQLite.
- Identifies UNKNOWN faces and lists undetected students as ABSENT.
- Annotates and saves visual results.
- Generates a structured terminal summary report.
"""

import os
import cv2
import datetime
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import config
from database.db_manager import DatabaseManager
from modules.face_detection import FaceDetector
from modules.face_embedding import FaceEmbeddingExtractor
from modules.face_matching import FaceMatcher


class AttendanceManager:
    """Orchestrates face identification and attendance recording from static images."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        detector: Optional[FaceDetector] = None,
        extractor: Optional[FaceEmbeddingExtractor] = None,
        matcher: Optional[FaceMatcher] = None,
    ):
        self.db = db_manager or DatabaseManager()
        self.detector = detector or FaceDetector()
        self.extractor = extractor or FaceEmbeddingExtractor()
        self.matcher = matcher or FaceMatcher()

    def process_classroom_image(
        self,
        image_path: UnionPath,
        attendance_date: Optional[str] = None,
        display_image: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Process a classroom photograph, recognize enrolled students, and mark attendance.

        Args:
            image_path: Path to classroom image file.
            attendance_date: Date string (YYYY-MM-DD), defaults to today.
            display_image: Whether to open an OpenCV window showing annotated detections.

        Returns:
            Dictionary containing attendance summary statistics and student statuses.
        """
        path_obj = Path(str(image_path).strip().strip('"').strip("'"))
        if not path_obj.exists():
            print(f"[Error] Image file not found: {path_obj}")
            return None

        img = cv2.imread(str(path_obj))
        if img is None:
            print(f"[Error] Failed to read or decode image file: {path_obj}")
            return None

        now = datetime.datetime.now()
        date_str = attendance_date or now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # Fetch enrolled records from database
        all_students = self.db.get_all_students()
        if not all_students:
            print("[Warning] No students are currently registered in the system.")
            print("Please register students first before taking attendance.")
            return None

        enrolled_embeddings = self.db.get_all_embeddings()
        if not enrolled_embeddings:
            print("[Warning] No face embeddings found in database. Please enroll students with face samples.")
            return None

        print(f"\n[Processing] Analyzing classroom image: {path_obj.name}")
        print(f"[Detector] Running face detection ({self.detector.method.upper()})...")

        # 1. Detect all faces in the classroom photograph
        detections = self.detector.detect_faces(img)
        print(f"[Detector] Found {len(detections)} face(s) in image.")

        recognized_students: Dict[str, Dict[str, Any]] = {}
        unknown_faces_count = 0
        detection_labels: List[str] = []
        detection_colors: List[Tuple[int, int, int]] = []

        # 2. Extract embeddings and match each face
        for idx, det in enumerate(detections):
            face_crop_rgb = det["cropped_face"]
            embedding = self.extractor.extract_embedding(face_crop_rgb)
            match_res = self.matcher.match_face(embedding, enrolled_embeddings)

            if match_res["is_recognized"]:
                sid = match_res["student_id"]
                sname = match_res["student_name"]
                dist = match_res["distance"]

                label = f"{sname} ({sid}) [d={dist:.2f}]"
                color = (0, 255, 0)  # Green for recognized

                # Mark attendance in database
                marked, msg = self.db.mark_attendance(
                    student_id=sid,
                    attendance_date=date_str,
                    attendance_time=time_str,
                    status="PRESENT",
                    matching_distance=dist,
                )

                recognized_students[sid] = {
                    "name": sname,
                    "distance": dist,
                    "marked_new": marked,
                    "message": msg,
                }
            else:
                unknown_faces_count += 1
                dist = match_res.get("distance", 999.0)
                label = f"UNKNOWN [d={dist:.2f}]"
                color = (0, 0, 255)  # Red for unknown face

            detection_labels.append(label)
            detection_colors.append(color)

        # 3. Annotate image with bounding boxes & student names
        annotated_img = self.detector.draw_detections(
            image=img,
            detections=detections,
            labels=detection_labels,
            colors=detection_colors,
        )

        # Save annotated image into output/ directory
        timestamp_slug = now.strftime("%Y%m%d_%H%M%S")
        output_filename = f"attendance_result_{timestamp_slug}.jpg"
        saved_output_path = config.OUTPUT_DIR / output_filename
        cv2.imwrite(str(saved_output_path), annotated_img)
        print(f"[Output] Annotated result saved to: {saved_output_path}")

        # Optionally display image with OpenCV
        if display_image:
            self.detector.display_or_save(
                annotated_img,
                window_title=f"Classroom Attendance - {date_str}",
                save_filename=None,
            )

        # 4. Construct complete student attendance list (All registered students)
        total_students = len(all_students)
        present_count = 0
        absent_count = 0
        student_statuses: List[Dict[str, Any]] = []

        for student in all_students:
            sid = student["student_id"]
            sname = student["student_name"]

            if sid in recognized_students:
                status = "PRESENT"
                present_count += 1
            elif self.db.is_attendance_marked(sid, date_str):
                # Marked present earlier on the same date
                status = "PRESENT"
                present_count += 1
            else:
                # Student was not detected in this classroom photo
                status = "ABSENT"
                absent_count += 1

            student_statuses.append(
                {
                    "student_id": sid,
                    "student_name": sname,
                    "department": student.get("department", "N/A"),
                    "year": student.get("year", "N/A"),
                    "status": status,
                }
            )

        attendance_percentage = (
            (present_count / total_students) * 100.0 if total_students > 0 else 0.0
        )

        summary = {
            "date": date_str,
            "total_students": total_students,
            "present_count": present_count,
            "absent_count": absent_count,
            "unknown_faces": unknown_faces_count,
            "attendance_percentage": attendance_percentage,
            "student_statuses": student_statuses,
            "annotated_image_path": str(saved_output_path),
        }

        # 5. Display formatted summary table
        self.print_attendance_summary(summary)

        return summary

    def process_image_array(
        self,
        img: np.ndarray,
        attendance_date: Optional[str] = None,
        save_output: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Process an in-memory BGR image array (e.g. from FastAPI file upload).
        Performs detection, recognition, marks attendance, and returns base64 annotated image.
        """
        import base64

        if img is None or img.size == 0:
            return None

        now = datetime.datetime.now()
        date_str = attendance_date or now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        all_students = self.db.get_all_students()
        if not all_students:
            return {
                "error": "No students are currently registered in the database.",
                "total_students": 0,
                "present_count": 0,
                "absent_count": 0,
                "unknown_faces": 0,
                "attendance_percentage": 0.0,
                "student_statuses": [],
                "detections": [],
                "annotated_image_base64": None,
            }

        enrolled_embeddings = self.db.get_all_embeddings()
        detections = self.detector.detect_faces(img)

        recognized_students: Dict[str, Dict[str, Any]] = {}
        unknown_faces_count = 0
        detection_labels: List[str] = []
        detection_colors: List[Tuple[int, int, int]] = []
        detections_info: List[Dict[str, Any]] = []

        for det in detections:
            face_crop_rgb = det["cropped_face"]
            embedding = self.extractor.extract_embedding(face_crop_rgb)
            match_res = self.matcher.match_face(embedding, enrolled_embeddings)

            box = det["box"]
            x, y, w, h = box

            if match_res["is_recognized"]:
                sid = match_res["student_id"]
                sname = match_res["student_name"]
                dist = match_res["distance"]

                label = f"{sname} ({sid})"
                color = (0, 255, 0)  # Green

                marked, msg = self.db.mark_attendance(
                    student_id=sid,
                    attendance_date=date_str,
                    attendance_time=time_str,
                    status="PRESENT",
                    matching_distance=dist,
                )

                recognized_students[sid] = {
                    "name": sname,
                    "distance": dist,
                    "marked_new": marked,
                    "message": msg,
                    "time": time_str,
                }

                detections_info.append(
                    {
                        "box": [int(x), int(y), int(w), int(h)],
                        "student_id": sid,
                        "student_name": sname,
                        "distance": dist,
                        "status": "RECOGNIZED",
                        "is_recognized": True,
                    }
                )
            else:
                unknown_faces_count += 1
                dist = match_res.get("distance", 999.0)
                label = f"UNKNOWN ({dist:.2f})"
                color = (0, 0, 255)  # Red

                detections_info.append(
                    {
                        "box": [int(x), int(y), int(w), int(h)],
                        "student_id": "UNKNOWN",
                        "student_name": "UNKNOWN",
                        "distance": dist,
                        "status": match_res.get("status", "UNKNOWN"),
                        "is_recognized": False,
                    }
                )

            detection_labels.append(label)
            detection_colors.append(color)

        annotated_img = self.detector.draw_detections(
            image=img,
            detections=detections,
            labels=detection_labels,
            colors=detection_colors,
        )

        saved_path = None
        if save_output:
            timestamp_slug = now.strftime("%Y%m%d_%H%M%S")
            output_filename = f"web_attendance_{timestamp_slug}.jpg"
            saved_output_path = config.OUTPUT_DIR / output_filename
            cv2.imwrite(str(saved_output_path), annotated_img)
            saved_path = str(saved_output_path)

        # Convert annotated image to base64 JPEG
        ret, buffer = cv2.imencode(".jpg", annotated_img)
        base64_str = base64.b64encode(buffer).decode("utf-8") if ret else None
        base64_uri = f"data:image/jpeg;base64,{base64_str}" if base64_str else None

        # Build full roster status list
        total_students = len(all_students)
        present_count = 0
        absent_count = 0
        student_statuses = []

        for student in all_students:
            sid = student["student_id"]
            sname = student["student_name"]

            if sid in recognized_students:
                status = "PRESENT"
                present_count += 1
                rec_info = recognized_students[sid]
                time_val = rec_info.get("time", time_str)
                dist_val = rec_info.get("distance", 0.0)
            elif self.db.is_attendance_marked(sid, date_str):
                status = "PRESENT"
                present_count += 1
                time_val = time_str
                dist_val = None
            else:
                status = "ABSENT"
                absent_count += 1
                time_val = None
                dist_val = None

            student_statuses.append(
                {
                    "student_id": sid,
                    "student_name": sname,
                    "department": student.get("department") or "General",
                    "year": student.get("year") or "-",
                    "status": status,
                    "attendance_time": time_val,
                    "matching_distance": dist_val,
                }
            )

        pct = round((present_count / total_students) * 100, 1) if total_students > 0 else 0.0

        return {
            "date": date_str,
            "total_students": total_students,
            "present_count": present_count,
            "absent_count": absent_count,
            "unknown_faces": unknown_faces_count,
            "attendance_percentage": pct,
            "student_statuses": student_statuses,
            "detections": detections_info,
            "annotated_image_base64": base64_uri,
            "saved_image_path": saved_path,
        }

    def process_webcam_frame(
        self,
        frame_bgr: np.ndarray,
        attendance_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a single webcam video frame from frontend.
        Returns recognized bounding boxes and marks attendance automatically once per day.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        now = datetime.datetime.now()
        date_str = attendance_date or now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        enrolled_embeddings = self.db.get_all_embeddings()
        if not enrolled_embeddings:
            return []

        detections = self.detector.detect_faces(frame_bgr)
        results = []

        for det in detections:
            face_crop_rgb = det["cropped_face"]
            embedding = self.extractor.extract_embedding(face_crop_rgb)
            match_res = self.matcher.match_face(embedding, enrolled_embeddings)

            x, y, w, h = det["box"]
            is_rec = match_res["is_recognized"]
            sid = match_res["student_id"]
            sname = match_res["student_name"]
            dist = match_res["distance"]

            marked_now = False
            if is_rec:
                if not self.db.is_attendance_marked(sid, date_str):
                    success, msg = self.db.mark_attendance(
                        student_id=sid,
                        attendance_date=date_str,
                        attendance_time=time_str,
                        status="PRESENT",
                        matching_distance=dist,
                    )
                    marked_now = success

            results.append(
                {
                    "box": [int(x), int(y), int(w), int(h)],
                    "student_id": sid,
                    "student_name": sname,
                    "distance": dist,
                    "status": match_res.get("status", "UNKNOWN"),
                    "is_recognized": is_rec,
                    "marked_now": marked_now,
                    "timestamp": time_str,
                }
            )

        return results

    @staticmethod
    def print_attendance_summary(summary: Dict[str, Any]) -> None:
        """Format and print the terminal attendance summary table."""
        print("\n" + "=" * 50)
        print("              ATTENDANCE SUMMARY")
        print("=" * 50)
        print(f"Date: {summary['date']}\n")
        print(f"{'Student ID':<14} {'Name':<20} {'Status':<10}")
        print("-" * 50)

        for s in summary["student_statuses"]:
            sid = str(s["student_id"])
            name = str(s["student_name"])
            status = str(s["status"])
            print(f"{sid:<14} {name:<20} {status:<10}")

        print("\n" + "-" * 50)
        print(f"Total Students:        {summary['total_students']}")
        print(f"Present:               {summary['present_count']}")
        print(f"Absent:                {summary['absent_count']}")
        print(f"Unknown Faces:         {summary['unknown_faces']}")
        print(f"\nAttendance Percentage: {summary['attendance_percentage']:.1f}%")
        print("=" * 50 + "\n")


# Type alias for paths
UnionPath = Union = Any

