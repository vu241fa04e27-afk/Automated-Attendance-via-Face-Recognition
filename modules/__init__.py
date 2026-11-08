"""Modules package initialization."""
from .face_detection import FaceDetector
from .face_embedding import FaceEmbeddingExtractor
from .face_matching import FaceMatcher
from .student_registration import StudentRegistrationManager
from .attendance_manager import AttendanceManager
from .webcam_attendance import WebcamAttendanceManager
from .reports import AttendanceReporter

__all__ = [
    "FaceDetector",
    "FaceEmbeddingExtractor",
    "FaceMatcher",
    "StudentRegistrationManager",
    "AttendanceManager",
    "WebcamAttendanceManager",
    "AttendanceReporter",
]

