"""
Student Registration Module for Automated Attendance System.
Handles new student onboarding:
- Demographic metadata collection (ID, Name, Department, Year).
- Face image collection via local image paths or live webcam capture.
- Face presence validation and quality checks.
- Extraction and persistent storage of multiple face embeddings.
"""

import os
import cv2
import datetime
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
import config
from database.db_manager import DatabaseManager
from modules.face_detection import FaceDetector
from modules.face_embedding import FaceEmbeddingExtractor


class StudentRegistrationManager:
    """Manages student enrollment, face validation, and embedding generation."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        detector: Optional[FaceDetector] = None,
        extractor: Optional[FaceEmbeddingExtractor] = None,
    ):
        self.db = db_manager or DatabaseManager()
        self.detector = detector or FaceDetector()
        self.extractor = extractor or FaceEmbeddingExtractor()

    def register_new_student(
        self,
        student_id: str,
        student_name: str,
        department: Optional[str] = None,
        year: Optional[str] = None,
        image_paths: Optional[List[str]] = None,
        use_webcam: bool = False,
        target_samples: int = 3,
    ) -> Tuple[bool, str]:
        """
        Complete enrollment pipeline for a new student.

        Returns:
            (success: bool, message: str)
        """
        student_id = str(student_id).strip()
        student_name = str(student_name).strip()

        if not student_id:
            return False, "Error: Student ID cannot be empty."
        if not student_name:
            return False, "Error: Student Name cannot be empty."

        # Check for duplicate ID
        if self.db.student_exists(student_id):
            return False, f"Error: Student with ID '{student_id}' is already registered."

        # Collect face images
        collected_faces: List[np.ndarray] = []
        student_dir = config.STUDENT_IMAGES_DIR / student_id
        student_dir.mkdir(parents=True, exist_ok=True)

        if use_webcam:
            print(f"\n[Webcam Mode] Starting face capture for {student_name} ({student_id})...")
            collected_faces = self.capture_faces_from_webcam(
                student_id=student_id,
                target_samples=target_samples,
                save_dir=student_dir,
            )
        elif image_paths:
            print(f"\n[File Mode] Processing {len(image_paths)} image(s) for {student_name}...")
            collected_faces = self.process_image_files(
                image_paths=image_paths,
                save_dir=student_dir,
            )
        else:
            return False, "Error: No face images provided (neither file paths nor webcam capture selected)."

        if not collected_faces:
            # Clean up directory if no valid faces were saved
            if student_dir.exists() and not any(student_dir.iterdir()):
                try:
                    student_dir.rmdir()
                except OSError:
                    pass
            return False, "Registration aborted: No valid faces detected in the provided images."

        # 1. Save student record in SQLite
        success = self.db.register_student(
            student_id=student_id,
            student_name=student_name,
            department=department,
            year=year,
        )
        if not success:
            return False, "Database error: Could not insert student record."

        # 2. Extract and save facial embeddings
        saved_embeddings_count = 0
        for face_rgb in collected_faces:
            try:
                embedding = self.extractor.extract_embedding(face_rgb)
                if self.db.add_embedding(student_id, embedding):
                    saved_embeddings_count += 1
            except Exception as e:
                print(f"[Warning] Failed to generate embedding for sample: {e}")

        if saved_embeddings_count == 0:
            # Rollback student record if no embeddings could be stored
            self.db.delete_student(student_id)
            return False, "Registration failed: Could not generate face embeddings."

        return (
            True,
            f"Successfully registered student '{student_name}' (ID: {student_id}) with {saved_embeddings_count} face embedding sample(s).",
        )

    def register_student_from_images(
        self,
        student_id: str,
        student_name: str,
        department: Optional[str] = None,
        year: Optional[str] = None,
        images_bgr: Optional[List[np.ndarray]] = None,
    ) -> Tuple[bool, str, int]:
        """
        Register a student directly from a list of in-memory BGR image arrays
        (e.g. from FastAPI file uploads or browser webcam snapshots).
        Returns: (success: bool, message: str, sample_count: int)
        """
        student_id = str(student_id).strip()
        student_name = str(student_name).strip()

        if not student_id:
            return False, "Student ID cannot be empty.", 0
        if not student_name:
            return False, "Student Name cannot be empty.", 0

        if self.db.student_exists(student_id):
            return False, f"Student ID '{student_id}' is already registered.", 0

        if not images_bgr:
            return False, "No face photographs provided for enrollment.", 0

        student_dir = config.STUDENT_IMAGES_DIR / student_id
        student_dir.mkdir(parents=True, exist_ok=True)

        valid_faces: List[np.ndarray] = []
        sample_idx = 1

        for idx, img in enumerate(images_bgr):
            if img is None or img.size == 0:
                continue

            detections = self.detector.detect_faces(img)
            if len(detections) == 0:
                continue
            elif len(detections) > 1:
                # Pick largest face
                detections.sort(key=lambda d: d["box"][2] * d["box"][3], reverse=True)

            face_rgb = detections[0]["cropped_face"]
            valid_faces.append(face_rgb)

            # Save sample to student folder
            save_path = student_dir / f"sample_{sample_idx}.jpg"
            cv2.imwrite(str(save_path), cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR))
            sample_idx += 1

        if not valid_faces:
            if student_dir.exists() and not any(student_dir.iterdir()):
                try:
                    student_dir.rmdir()
                except OSError:
                    pass
            return False, "No valid faces detected in the uploaded photographs. Please ensure faces are clear and well-lit.", 0

        # Register in database
        success = self.db.register_student(
            student_id=student_id,
            student_name=student_name,
            department=department,
            year=year,
        )
        if not success:
            return False, "Database insertion failed.", 0

        saved_count = 0
        for face_rgb in valid_faces:
            try:
                emb = self.extractor.extract_embedding(face_rgb)
                if self.db.add_embedding(student_id, emb):
                    saved_count += 1
            except Exception as e:
                print(f"[Warning] Error extracting embedding: {e}")

        if saved_count == 0:
            self.db.delete_student(student_id)
            return False, "Failed to compute facial embeddings from face samples.", 0

        return True, f"Successfully enrolled student {student_name} with {saved_count} face sample(s).", saved_count

    def process_image_files(
        self,
        image_paths: List[str],
        save_dir: Path,
    ) -> List[np.ndarray]:
        """
        Process a list of image file paths:
        Validates presence of a face and crops/normalizes the face region.
        """
        valid_faces: List[np.ndarray] = []
        sample_idx = 1

        for raw_path in image_paths:
            img_path = Path(raw_path.strip().strip('"').strip("'"))
            if not img_path.exists():
                print(f"  [Skip] Image file not found: {img_path}")
                continue

            img = cv2.imread(str(img_path))
            if img is None:
                print(f"  [Skip] Invalid or unreadable image: {img_path}")
                continue

            detections = self.detector.detect_faces(img)
            if len(detections) == 0:
                print(f"  [Warning] No face detected in: {img_path.name}. Skipping.")
                continue
            elif len(detections) > 1:
                print(
                    f"  [Notice] Multiple faces ({len(detections)}) detected in {img_path.name}. "
                    "Using the largest face detected."
                )
                # Select the face with maximum bounding box area
                detections.sort(key=lambda d: d["box"][2] * d["box"][3], reverse=True)

            face_crop_rgb = detections[0]["cropped_face"]
            valid_faces.append(face_crop_rgb)

            # Save the cropped face image for inspection
            save_path = save_dir / f"sample_{sample_idx}.jpg"
            face_bgr = cv2.cvtColor(face_crop_rgb, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(save_path), face_bgr)
            sample_idx += 1
            print(f"  [Validated] Extracted face sample from {img_path.name} -> {save_path.name}")

        return valid_faces

    def capture_faces_from_webcam(
        self,
        student_id: str,
        target_samples: int = 3,
        save_dir: Optional[Path] = None,
    ) -> List[np.ndarray]:
        """
        Interactively capture face samples using webcam.
        Press 'c' or SPACE to capture a sample when a face is highlighted in green.
        Press 'q' or ESC to stop capture early.
        """
        cap = cv2.VideoCapture(config.DEFAULT_WEBCAM_INDEX)
        if not cap.isOpened():
            print(f"[Error] Could not open webcam (index {config.DEFAULT_WEBCAM_INDEX}).")
            return []

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_FRAME_HEIGHT)

        captured_faces: List[np.ndarray] = []
        sample_num = 1

        print("\n" + "=" * 50)
        print(f"  WEBCAM ENROLLMENT: Capturing {target_samples} face samples")
        print("  Controls:")
        print("    [SPACE] or [C]: Capture face when bounding box is GREEN")
        print("    [ESC] or [Q]  : Exit capture")
        print("=" * 50 + "\n")

        try:
            while len(captured_faces) < target_samples:
                ret, frame = cap.read()
                if not ret or frame is None:
                    print("[Warning] Failed to grab frame from webcam.")
                    break

                # Detect faces in real-time
                detections = self.detector.detect_faces(frame)
                display_frame = frame.copy()

                if len(detections) == 1:
                    box = detections[0]["box"]
                    x, y, w, h = box
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(
                        display_frame,
                        f"Ready to capture ({len(captured_faces)}/{target_samples})",
                        (x, max(20, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )
                elif len(detections) > 1:
                    for det in detections:
                        x, y, w, h = det["box"]
                        cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 165, 255), 2)
                    cv2.putText(
                        display_frame,
                        "Warning: Multiple faces detected! Only 1 face allowed",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 165, 255),
                        2,
                    )
                else:
                    cv2.putText(
                        display_frame,
                        "Position face inside frame...",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )

                # Show instructions at bottom
                cv2.putText(
                    display_frame,
                    f"Samples captured: {len(captured_faces)} / {target_samples} | [SPACE] Capture | [ESC] Exit",
                    (15, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )

                cv2.imshow("Student Face Registration - Webcam", display_frame)
                key = cv2.waitKey(1) & 0xFF

                # Capture key: Space (32) or 'c' / 'C'
                if key in (32, ord("c"), ord("C")):
                    if len(detections) == 1:
                        face_rgb = detections[0]["cropped_face"]
                        captured_faces.append(face_rgb)
                        print(f"  [Captured] Sample {sample_num}/{target_samples} successfully recorded.")

                        if save_dir:
                            save_path = save_dir / f"sample_{sample_num}.jpg"
                            cv2.imwrite(str(save_path), cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR))

                        sample_num += 1

                        # Flash effect
                        white_frame = np.full_like(frame, 255)
                        cv2.imshow("Student Face Registration - Webcam", white_frame)
                        cv2.waitKey(80)
                    elif len(detections) == 0:
                        print("  [Warning] No face detected. Please face the camera and try again.")
                    else:
                        print("  [Warning] Multiple faces in view. Ensure only the enrolling student is visible.")

                # Exit key: ESC (27) or 'q' / 'Q'
                elif key in (27, ord("q"), ord("Q")):
                    print("[Info] Webcam registration canceled by user.")
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

        return captured_faces

