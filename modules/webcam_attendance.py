"""
Webcam Attendance Module for Automated Attendance System.
Provides continuous real-time video stream face recognition:
- Identifies enrolled students frame-by-frame.
- Automatically logs attendance in SQLite once per student per day.
- Visual overlays for student names, confidence metrics, and attendance confirmations.
- Safe resource release on ESC or 'q' key press.
"""

import cv2
import datetime
import time
import numpy as np
from typing import Optional, Dict, Any, List
import config
from database.db_manager import DatabaseManager
from modules.face_detection import FaceDetector
from modules.face_embedding import FaceEmbeddingExtractor
from modules.face_matching import FaceMatcher


class WebcamAttendanceManager:
    """Manages real-time video stream face recognition and automated attendance logging."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        detector: Optional[FaceDetector] = None,
        extractor: Optional[FaceEmbeddingExtractor] = None,
        matcher: Optional[FaceMatcher] = None,
        camera_index: int = config.DEFAULT_WEBCAM_INDEX,
    ):
        self.db = db_manager or DatabaseManager()
        self.detector = detector or FaceDetector()
        self.extractor = extractor or FaceEmbeddingExtractor()
        self.matcher = matcher or FaceMatcher()
        self.camera_index = camera_index

    def run_live_attendance(self) -> None:
        """
        Open webcam and perform continuous face recognition and attendance marking.
        Press ESC (27) or 'q' to stop.
        """
        print(f"\n[Webcam] Connecting to camera (Index: {self.camera_index})...")
        cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            print(f"[Error] Could not open webcam at index {self.camera_index}.")
            print("Please check your camera connection or try another device index.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_FRAME_HEIGHT)

        # Load enrolled database embeddings
        enrolled_embeddings = self.db.get_all_embeddings()
        if not enrolled_embeddings:
            print("[Warning] No enrolled student embeddings found in database.")
            print("Please register students first before starting webcam attendance.")
            cap.release()
            return

        today_date = datetime.date.today().isoformat()
        marked_session_students = set()

        # Cache existing attendees for today to avoid repeated queries
        today_records = self.db.get_today_attendance()
        for rec in today_records:
            marked_session_students.add(rec["student_id"])

        print("\n" + "=" * 55)
        print("           LIVE WEBCAM ATTENDANCE MODE")
        print("=" * 55)
        print("  Controls:")
        print("    [ESC] or [Q] : Exit webcam attendance mode")
        print(f"  Enrolled Students in Database: {len(self.db.get_all_students())}")
        print(f"  Already Marked Today: {len(marked_session_students)}")
        print("=" * 55 + "\n")

        # For performance, process recognition every N frames
        frame_count = 0
        recognition_interval = 3  # Detect and recognize every 3 frames, hold bounding boxes between
        last_detections: List[Dict[str, Any]] = []
        last_labels: List[str] = []
        last_colors: List[tuple] = []
        last_notification = ""
        notification_time = 0.0

        fps_start_time = time.time()
        fps_frame_count = 0
        current_fps = 0.0

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    print("[Warning] Failed to read frame from webcam.")
                    break

                frame_count += 1
                fps_frame_count += 1

                # Calculate FPS every second
                if time.time() - fps_start_time >= 1.0:
                    current_fps = fps_frame_count / (time.time() - fps_start_time)
                    fps_frame_count = 0
                    fps_start_time = time.time()

                if frame_count % recognition_interval == 0:
                    detections = self.detector.detect_faces(frame)
                    labels = []
                    colors = []

                    for det in detections:
                        face_crop = det["cropped_face"]
                        embedding = self.extractor.extract_embedding(face_crop)
                        match_res = self.matcher.match_face(embedding, enrolled_embeddings)

                        if match_res["is_recognized"]:
                            sid = match_res["student_id"]
                            sname = match_res["student_name"]
                            dist = match_res["distance"]

                            if sid not in marked_session_students:
                                now_time = datetime.datetime.now().strftime("%H:%M:%S")
                                success, msg = self.db.mark_attendance(
                                    student_id=sid,
                                    attendance_date=today_date,
                                    attendance_time=now_time,
                                    status="PRESENT",
                                    matching_distance=dist,
                                )
                                if success:
                                    marked_session_students.add(sid)
                                    last_notification = f"Attendance Marked: {sname} ({sid})"
                                    notification_time = time.time()
                                    print(f"  >>> [ATTENDANCE MARKED] {sname} ({sid}) at {now_time}")
                                else:
                                    marked_session_students.add(sid)
                                    last_notification = f"Already marked: {sname}"
                                    notification_time = time.time()

                            labels.append(f"{sname} [d={dist:.2f}]")
                            colors.append((0, 255, 0))  # Green
                        else:
                            dist = match_res.get("distance", 999.0)
                            labels.append(f"UNKNOWN [d={dist:.2f}]")
                            colors.append((0, 0, 255))  # Red

                    last_detections = detections
                    last_labels = labels
                    last_colors = colors

                # Draw persistent bounding boxes
                display_frame = self.detector.draw_detections(
                    image=frame,
                    detections=last_detections,
                    labels=last_labels,
                    colors=last_colors,
                )

                # Top info bar
                h, w = display_frame.shape[:2]
                cv2.rectangle(display_frame, (0, 0), (w, 35), (30, 30, 30), cv2.FILLED)
                cv2.putText(
                    display_frame,
                    f"Date: {today_date} | Present Today: {len(marked_session_students)} | FPS: {current_fps:.1f} | [ESC] Exit",
                    (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

                # Show attendance toast notification
                if last_notification and (time.time() - notification_time < 3.0):
                    cv2.rectangle(display_frame, (0, h - 45), (w, h), (0, 180, 0), cv2.FILLED)
                    cv2.putText(
                        display_frame,
                        last_notification,
                        (20, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )

                cv2.imshow("Automated Attendance System - Live Webcam", display_frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q"), ord("Q")):
                    print("\n[Webcam] Exiting live attendance stream.")
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[Webcam] Hardware released and display windows closed.")

