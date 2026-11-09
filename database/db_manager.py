"""
Database Manager for Automated Attendance System.
Handles SQLite operations for students, face embeddings, and attendance records.
Enforces foreign key relationships and unique constraints.
"""

import sqlite3
import datetime
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import config


class DatabaseManager:
    """Manages all interactions with the SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path if db_path else getattr(config, "ATTENDANCE_DB_PATH", config.DB_PATH))
        self.initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_database(self) -> None:
        """Create the necessary database tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Students Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS STUDENTS (
                    student_id TEXT PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    department TEXT,
                    year TEXT,
                    registration_date TEXT NOT NULL
                );
                """
            )

            # 2. Face Embeddings Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS FACE_EMBEDDINGS (
                    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    embedding_data BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES STUDENTS(student_id) ON DELETE CASCADE
                );
                """
            )

            # 3. Attendance Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ATTENDANCE (
                    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    attendance_date TEXT NOT NULL,
                    attendance_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    matching_distance REAL,
                    FOREIGN KEY (student_id) REFERENCES STUDENTS(student_id) ON DELETE CASCADE,
                    UNIQUE (student_id, attendance_date)
                );
                """
            )

            # 4. Admins Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ADMINS (
                    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

            # 5. System Settings Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS SYSTEM_SETTINGS (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

            # Indexes for faster lookup
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_embeddings_student_id ON FACE_EMBEDDINGS(student_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_attendance_date ON ATTENDANCE(attendance_date);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON ATTENDANCE(student_id);"
            )

            # Initialize default admin if no admin exists
            cursor.execute("SELECT COUNT(*) FROM ADMINS;")
            if cursor.fetchone()[0] == 0:
                import hashlib
                import secrets

                default_user = "admin"
                default_pass = "admin123"
                salt = secrets.token_hex(16)
                p_hash = hashlib.pbkdf2_hmac(
                    "sha256", default_pass.encode("utf-8"), salt.encode("utf-8"), 100000
                ).hex()
                created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute(
                    """
                    INSERT INTO ADMINS (username, password_hash, salt, full_name, created_at)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (default_user, p_hash, salt, "System Administrator", created),
                )

            # Initialize default system settings if not present
            default_settings = [
                ("euclidean_threshold", str(config.EUCLIDEAN_THRESHOLD)),
                ("cosine_threshold", str(config.COSINE_THRESHOLD)),
                ("ambiguity_margin", str(config.AMBIGUITY_MARGIN)),
                ("default_detector", str(config.DEFAULT_DETECTOR)),
                ("matching_metric", str(config.DEFAULT_MATCHING_METRIC)),
            ]
            for key, val in default_settings:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO SYSTEM_SETTINGS (setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?);
                    """,
                    (key, val, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )

            conn.commit()

    # ==========================================
    # Student Operations
    # ==========================================

    def register_student(
        self,
        student_id: str,
        student_name: str,
        department: Optional[str] = None,
        year: Optional[str] = None,
        registration_date: Optional[str] = None,
    ) -> bool:
        """
        Register a new student in the database.
        Returns True if successful, False if student_id already exists.
        """
        if not registration_date:
            registration_date = datetime.date.today().isoformat()

        query = """
            INSERT INTO STUDENTS (student_id, student_name, department, year, registration_date)
            VALUES (?, ?, ?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        str(student_id).strip(),
                        str(student_name).strip(),
                        str(department).strip() if department else None,
                        str(year).strip() if year else None,
                        registration_date,
                    ),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def student_exists(self, student_id: str) -> bool:
        """Check if a student with the given ID already exists."""
        query = "SELECT 1 FROM STUDENTS WHERE student_id = ? LIMIT 1;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (str(student_id).strip(),))
            return cursor.fetchone() is not None

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve student record by student_id."""
        query = "SELECT * FROM STUDENTS WHERE student_id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (str(student_id).strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Retrieve all enrolled students sorted by student_id."""
        query = "SELECT * FROM STUDENTS ORDER BY student_id ASC;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def update_student(
        self,
        student_id: str,
        student_name: str,
        department: Optional[str] = None,
        year: Optional[str] = None,
    ) -> bool:
        """Update existing student details."""
        query = """
            UPDATE STUDENTS
            SET student_name = ?, department = ?, year = ?
            WHERE student_id = ?;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    str(student_name).strip(),
                    str(department).strip() if department else None,
                    str(year).strip() if year else None,
                    str(student_id).strip(),
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_student(self, student_id: str) -> bool:
        """
        Delete a student and cascadingly delete their face embeddings and attendance records.
        Returns True if a student was deleted, False if student was not found.
        """
        query = "DELETE FROM STUDENTS WHERE student_id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (str(student_id).strip(),))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================
    # Face Embedding Operations
    # ==========================================

    def add_embedding(self, student_id: str, embedding: np.ndarray) -> bool:
        """
        Save a face embedding vector for a student.
        Embedding is serialized as float32 bytes for precision and compactness.
        """
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding, dtype=np.float32)
        else:
            embedding = embedding.astype(np.float32)

        raw_bytes = embedding.tobytes()
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
            INSERT INTO FACE_EMBEDDINGS (student_id, embedding_data, created_at)
            VALUES (?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(student_id).strip(), raw_bytes, created_at))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"[Error saving embedding]: {e}")
            return False

    def get_embeddings_for_student(self, student_id: str) -> List[np.ndarray]:
        """Retrieve all embedding vectors associated with a specific student ID."""
        query = "SELECT embedding_data FROM FACE_EMBEDDINGS WHERE student_id = ?;"
        embeddings = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (str(student_id).strip(),))
            rows = cursor.fetchall()
            for row in rows:
                arr = np.frombuffer(row["embedding_data"], dtype=np.float32)
                embeddings.append(arr)
        return embeddings

    def get_all_embeddings(self) -> List[Dict[str, Any]]:
        """
        Retrieve all enrolled face embeddings joined with student details.
        Returns list of dicts with student_id, student_name, and numpy embedding vector.
        """
        query = """
            SELECT e.embedding_id, e.student_id, s.student_name, e.embedding_data
            FROM FACE_EMBEDDINGS e
            JOIN STUDENTS s ON e.student_id = s.student_id
            ORDER BY e.student_id ASC;
        """
        records = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                arr = np.frombuffer(row["embedding_data"], dtype=np.float32)
                records.append(
                    {
                        "embedding_id": row["embedding_id"],
                        "student_id": row["student_id"],
                        "student_name": row["student_name"],
                        "embedding": arr,
                    }
                )
        return records

    def get_embedding_count(self, student_id: Optional[str] = None) -> int:
        """Return total number of embeddings for a student or across all students."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if student_id:
                cursor.execute(
                    "SELECT COUNT(*) FROM FACE_EMBEDDINGS WHERE student_id = ?;",
                    (str(student_id).strip(),),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM FACE_EMBEDDINGS;")
            return cursor.fetchone()[0]

    # ==========================================
    # Attendance Operations
    # ==========================================

    def mark_attendance(
        self,
        student_id: str,
        attendance_date: Optional[str] = None,
        attendance_time: Optional[str] = None,
        status: str = "PRESENT",
        matching_distance: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Record attendance for a student on a specific date.
        Returns:
            (True, "Marked successfully") if recorded.
            (False, "Already marked for today") if duplicate.
            (False, error_msg) if an error occurs.
        """
        now = datetime.datetime.now()
        if not attendance_date:
            attendance_date = now.strftime("%Y-%m-%d")
        if not attendance_time:
            attendance_time = now.strftime("%H:%M:%S")

        query = """
            INSERT INTO ATTENDANCE (student_id, attendance_date, attendance_time, status, matching_distance)
            VALUES (?, ?, ?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        str(student_id).strip(),
                        attendance_date,
                        attendance_time,
                        status,
                        matching_distance,
                    ),
                )
                conn.commit()
                return True, "Attendance marked successfully."
        except sqlite3.IntegrityError:
            return False, f"Attendance already marked for student {student_id} on {attendance_date}."
        except sqlite3.Error as e:
            return False, f"Database error while marking attendance: {e}"

    def is_attendance_marked(self, student_id: str, attendance_date: Optional[str] = None) -> bool:
        """Check if attendance has already been recorded for a student on a specific date."""
        if not attendance_date:
            attendance_date = datetime.date.today().isoformat()
        query = """
            SELECT 1 FROM ATTENDANCE
            WHERE student_id = ? AND attendance_date = ?
            LIMIT 1;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (str(student_id).strip(), attendance_date))
            return cursor.fetchone() is not None

    def get_attendance_by_date(self, attendance_date: str) -> List[Dict[str, Any]]:
        """Retrieve attendance records for a given date along with student info."""
        query = """
            SELECT a.attendance_id, a.student_id, s.student_name, s.department, s.year,
                   a.attendance_date, a.attendance_time, a.status, a.matching_distance
            FROM ATTENDANCE a
            JOIN STUDENTS s ON a.student_id = s.student_id
            WHERE a.attendance_date = ?
            ORDER BY a.attendance_time ASC;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (attendance_date,))
            return [dict(row) for row in cursor.fetchall()]

    def get_attendance_by_student(self, student_id: str) -> List[Dict[str, Any]]:
        """Retrieve all attendance entries for a specific student."""
        query = """
            SELECT a.attendance_id, a.student_id, s.student_name, s.department, s.year,
                   a.attendance_date, a.attendance_time, a.status, a.matching_distance
            FROM ATTENDANCE a
            JOIN STUDENTS s ON a.student_id = s.student_id
            WHERE a.student_id = ?
            ORDER BY a.attendance_date DESC, a.attendance_time DESC;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (str(student_id).strip(),))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_attendance(self) -> List[Dict[str, Any]]:
        """Retrieve entire attendance log."""
        query = """
            SELECT a.attendance_id, a.student_id, s.student_name, s.department, s.year,
                   a.attendance_date, a.attendance_time, a.status, a.matching_distance
            FROM ATTENDANCE a
            JOIN STUDENTS s ON a.student_id = s.student_id
            ORDER BY a.attendance_date DESC, a.attendance_time DESC;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_today_attendance(self) -> List[Dict[str, Any]]:
        """Retrieve attendance records for today's date."""
        today = datetime.date.today().isoformat()
        return self.get_attendance_by_date(today)

    def get_distinct_attendance_dates(self) -> List[str]:
        """Retrieve list of distinct dates when attendance was recorded."""
        query = "SELECT DISTINCT attendance_date FROM ATTENDANCE ORDER BY attendance_date DESC;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [row["attendance_date"] for row in cursor.fetchall()]

    # ==========================================
    # Authentication & Admin Operations
    # ==========================================

    def verify_admin_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify admin credentials and return admin dict if valid, None otherwise."""
        import hashlib

        query = "SELECT * FROM ADMINS WHERE username = ? LIMIT 1;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (str(username).strip(),))
            row = cursor.fetchone()
            if not row:
                return None

            stored_hash = row["password_hash"]
            salt = row["salt"]
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            ).hex()

            if hmac_compare(stored_hash, computed_hash):
                return {
                    "admin_id": row["admin_id"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "created_at": row["created_at"],
                }
            return None

    def change_admin_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change admin password securely."""
        import hashlib
        import secrets

        admin = self.verify_admin_password(username, old_password)
        if not admin:
            return False, "Invalid current password."

        new_salt = secrets.token_hex(16)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", new_password.encode("utf-8"), new_salt.encode("utf-8"), 100000
        ).hex()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ADMINS SET password_hash = ?, salt = ? WHERE username = ?;",
                (new_hash, new_salt, username),
            )
            conn.commit()
            return True, "Password updated successfully."

    # ==========================================
    # System Settings Operations
    # ==========================================

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a system setting value."""
        query = "SELECT setting_value FROM SYSTEM_SETTINGS WHERE setting_key = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (key,))
            row = cursor.fetchone()
            return row["setting_value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Update or insert a system setting value."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO SYSTEM_SETTINGS (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value, updated_at = excluded.updated_at;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (key, str(value), now))
            conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        """Retrieve all system settings as a dictionary."""
        query = "SELECT setting_key, setting_value FROM SYSTEM_SETTINGS;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return {row["setting_key"]: row["setting_value"] for row in cursor.fetchall()}

    # ==========================================
    # Filtered Attendance & Analytics Operations
    # ==========================================

    def get_filtered_attendance(
        self,
        target_date: Optional[str] = None,
        student_id: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter attendance records with dynamic conditions."""
        query = """
            SELECT a.attendance_id, a.student_id, s.student_name, s.department, s.year,
                   a.attendance_date, a.attendance_time, a.status, a.matching_distance
            FROM ATTENDANCE a
            JOIN STUDENTS s ON a.student_id = s.student_id
            WHERE 1=1
        """
        params: List[Any] = []

        if target_date:
            query += " AND a.attendance_date = ?"
            params.append(target_date)
        if student_id:
            query += " AND a.student_id = ?"
            params.append(student_id)
        if department:
            query += " AND s.department = ?"
            params.append(department)
        if status:
            query += " AND a.status = ?"
            params.append(status)
        if search:
            query += " AND (s.student_name LIKE ? OR a.student_id LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY a.attendance_date DESC, a.attendance_time DESC;"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """Compute real-time dashboard analytics, trends, and charts data."""
        today = datetime.date.today().isoformat()
        all_students = self.get_all_students()
        total_students = len(all_students)

        today_records = self.get_attendance_by_date(today)
        present_sids = {r["student_id"] for r in today_records}
        present_count = len(present_sids)
        absent_count = max(0, total_students - present_count)
        today_percentage = (
            round((present_count / total_students) * 100, 1) if total_students > 0 else 0.0
        )

        all_records = self.get_all_attendance()
        total_attendance_records = len(all_records)

        # Recent 7 days trend
        daily_trends = []
        for i in range(6, -1, -1):
            day_d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
            day_records = self.get_attendance_by_date(day_d)
            day_present = len({r["student_id"] for r in day_records})
            day_absent = max(0, total_students - day_present)
            day_pct = round((day_present / total_students * 100), 1) if total_students > 0 else 0.0
            daily_trends.append(
                {
                    "date": day_d,
                    "day_name": datetime.date.fromisoformat(day_d).strftime("%a"),
                    "present": day_present,
                    "absent": day_absent,
                    "percentage": day_pct,
                }
            )

        # Department breakdown
        dept_map: Dict[str, Dict[str, int]] = {}
        for s in all_students:
            dept = s.get("department") or "General"
            if dept not in dept_map:
                dept_map[dept] = {"total": 0, "present": 0}
            dept_map[dept]["total"] += 1
            if s["student_id"] in present_sids:
                dept_map[dept]["present"] += 1

        department_stats = [
            {
                "department": dept,
                "total": info["total"],
                "present": info["present"],
                "absent": info["total"] - info["present"],
                "rate": round((info["present"] / info["total"]) * 100, 1) if info["total"] > 0 else 0.0,
            }
            for dept, info in dept_map.items()
        ]

        # Recent 8 attendance entries
        recent_records = all_records[:8]

        return {
            "total_students": total_students,
            "present_today": present_count,
            "absent_today": absent_count,
            "today_percentage": today_percentage,
            "total_attendance_records": total_attendance_records,
            "today_date": today,
            "daily_trends": daily_trends,
            "department_stats": department_stats,
            "recent_records": recent_records,
        }


def hmac_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    import hmac
    return hmac.compare_digest(a, b)


