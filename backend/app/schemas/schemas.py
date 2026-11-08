"""
Pydantic Schemas for Request & Response Data Validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class LoginRequest(BaseModel):
    username: str = Field(..., description="Administrator username")
    password: str = Field(..., description="Administrator password")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: Dict[str, Any]


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class StudentCreate(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=50)
    student_name: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = None
    year: Optional[str] = None


class StudentUpdate(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = None
    year: Optional[str] = None


class StudentResponse(BaseModel):
    student_id: str
    student_name: str
    department: Optional[str] = None
    year: Optional[str] = None
    registration_date: str
    face_samples_count: int = 0


class AttendanceMarkRequest(BaseModel):
    student_id: str
    attendance_date: Optional[str] = None
    attendance_time: Optional[str] = None
    status: str = "PRESENT"
    matching_distance: Optional[float] = None


class AttendanceRecord(BaseModel):
    attendance_id: int
    student_id: str
    student_name: str
    department: Optional[str] = None
    year: Optional[str] = None
    attendance_date: str
    attendance_time: str
    status: str
    matching_distance: Optional[float] = None


class WebcamFrameRequest(BaseModel):
    image_base64: str
    attendance_date: Optional[str] = None


class SettingsUpdate(BaseModel):
    euclidean_threshold: Optional[float] = None
    cosine_threshold: Optional[float] = None
    ambiguity_margin: Optional[float] = None
    default_detector: Optional[str] = None
    matching_metric: Optional[str] = None

