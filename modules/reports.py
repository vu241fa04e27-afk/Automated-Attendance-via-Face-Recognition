"""
Reports and Statistics Module for Automated Attendance System.
Handles CSV export using Pandas, attendance history review, percentage calculation,
and graphical visualization using Matplotlib.
"""

import os
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List
import config
from database.db_manager import DatabaseManager


class AttendanceReporter:
    """Generates attendance analytics, exports CSV reports, and creates visual charts."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def view_today_attendance(self) -> None:
        """Display attendance for the current calendar date."""
        today = datetime.date.today().isoformat()
        self.view_attendance_by_date(today)

    def view_attendance_by_date(self, target_date: str) -> None:
        """
        Display comprehensive attendance for a specific date,
        including all registered students (marked as PRESENT or ABSENT).
        """
        all_students = self.db.get_all_students()
        if not all_students:
            print("\n[Notice] No students registered in the database.")
            return

        date_records = self.db.get_attendance_by_date(target_date)
        present_sids = {r["student_id"]: r for r in date_records}

        print("\n" + "=" * 68)
        print(f"             ATTENDANCE REPORT FOR: {target_date}")
        print("=" * 68)
        print(f"{'Student ID':<12} {'Student Name':<20} {'Status':<10} {'Time':<10} {'Distance':<10}")
        print("-" * 68)

        present_count = 0
        absent_count = 0

        for s in all_students:
            sid = s["student_id"]
            name = s["student_name"]
            if sid in present_sids:
                rec = present_sids[sid]
                time_str = rec.get("attendance_time", "-")
                dist = rec.get("matching_distance")
                dist_str = f"{dist:.2f}" if dist is not None else "-"
                status_str = "PRESENT"
                present_count += 1
            else:
                time_str = "-"
                dist_str = "-"
                status_str = "ABSENT"
                absent_count += 1

            print(f"{sid:<12} {name:<20} {status_str:<10} {time_str:<10} {dist_str:<10}")

        total_students = len(all_students)
        pct = (present_count / total_students) * 100.0 if total_students > 0 else 0.0

        print("-" * 68)
        print(f"Total Enrolled: {total_students} | Present: {present_count} | Absent: {absent_count}")
        print(f"Daily Attendance Rate: {pct:.1f}%")
        print("=" * 68 + "\n")

    def view_attendance_by_student(self, student_id: str) -> None:
        """Display attendance log and percentage for an individual student."""
        student = self.db.get_student(student_id)
        if not student:
            print(f"\n[Error] Student ID '{student_id}' does not exist.")
            return

        records = self.db.get_attendance_by_student(student_id)
        distinct_dates = self.db.get_distinct_attendance_dates()
        total_sessions = len(distinct_dates)
        attended_sessions = len(records)
        pct = (attended_sessions / total_sessions * 100.0) if total_sessions > 0 else 0.0

        print("\n" + "=" * 65)
        print(f"  ATTENDANCE LOG: {student['student_name']} (ID: {student['student_id']})")
        print(f"  Department: {student.get('department') or 'N/A'} | Year: {student.get('year') or 'N/A'}")
        print("=" * 65)
        print(f"{'Date':<15} {'Time':<12} {'Status':<12} {'Match Distance':<15}")
        print("-" * 65)

        if not records:
            print("  No attendance records found for this student.")
        else:
            for r in records:
                dist = r.get("matching_distance")
                dist_str = f"{dist:.3f}" if dist is not None else "-"
                print(f"{r['attendance_date']:<15} {r['attendance_time']:<12} {r['status']:<12} {dist_str:<15}")

        print("-" * 65)
        print(f"Total College Sessions: {total_sessions}")
        print(f"Attended Sessions:     {attended_sessions}")
        print(f"Attendance Percentage: {pct:.1f}%")
        print("=" * 65 + "\n")

    def view_attendance_history(self) -> None:
        """Display overall chronological attendance history."""
        records = self.db.get_all_attendance()
        if not records:
            print("\n[Notice] No attendance history recorded yet.")
            return

        print("\n" + "=" * 75)
        print("                     COMPLETE ATTENDANCE HISTORY")
        print("=" * 75)
        print(f"{'ID':<6} {'Date':<12} {'Time':<10} {'Student ID':<12} {'Student Name':<20} {'Status':<8}")
        print("-" * 75)

        for r in records:
            print(
                f"{r['attendance_id']:<6} {r['attendance_date']:<12} {r['attendance_time']:<10} "
                f"{r['student_id']:<12} {r['student_name']:<20} {r['status']:<8}"
            )

        print("-" * 75)
        print(f"Total attendance entries recorded: {len(records)}")
        print("=" * 75 + "\n")

    def export_attendance_report(self, target_date: Optional[str] = None) -> Optional[str]:
        """
        Export attendance records to a CSV file inside the reports/ folder using Pandas.
        If target_date is provided, exports that day's complete report (including absent students).
        Otherwise exports complete historical log.
        """
        all_students = self.db.get_all_students()
        if not all_students:
            print("\n[Notice] No student records available to export.")
            return None

        if target_date:
            date_records = self.db.get_attendance_by_date(target_date)
            present_map = {r["student_id"]: r for r in date_records}
            rows = []
            for s in all_students:
                sid = s["student_id"]
                if sid in present_map:
                    rec = present_map[sid]
                    rows.append(
                        {
                            "Student_ID": sid,
                            "Student_Name": s["student_name"],
                            "Department": s.get("department") or "",
                            "Year": s.get("year") or "",
                            "Attendance_Date": target_date,
                            "Attendance_Time": rec.get("attendance_time", ""),
                            "Status": "PRESENT",
                            "Matching_Distance": rec.get("matching_distance", ""),
                        }
                    )
                else:
                    rows.append(
                        {
                            "Student_ID": sid,
                            "Student_Name": s["student_name"],
                            "Department": s.get("department") or "",
                            "Year": s.get("year") or "",
                            "Attendance_Date": target_date,
                            "Attendance_Time": "",
                            "Status": "ABSENT",
                            "Matching_Distance": "",
                        }
                    )
            df = pd.DataFrame(rows)
            filename = f"attendance_{target_date}.csv"
        else:
            all_records = self.db.get_all_attendance()
            if not all_records:
                print("\n[Notice] No attendance entries to export.")
                return None
            df = pd.DataFrame(all_records)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendance_history_{timestamp}.csv"

        out_path = config.REPORTS_DIR / filename
        df.to_csv(out_path, index=False)
        print(f"\n[Success] Attendance report exported to CSV:")
        print(f"  >>> Path: {out_path}")
        return str(out_path)

    def generate_attendance_statistics(self, save_chart: bool = True) -> Dict[str, Any]:
        """
        Compute high-level attendance metrics and student-wise statistics.
        Optionally plots a bar chart with Matplotlib.
        """
        all_students = self.db.get_all_students()
        if not all_students:
            print("\n[Notice] No students enrolled.")
            return {}

        all_attendance = self.db.get_all_attendance()
        distinct_dates = self.db.get_distinct_attendance_dates()
        total_sessions = len(distinct_dates)
        total_students = len(all_students)

        # Count attendance per student
        student_counts: Dict[str, int] = {s["student_id"]: 0 for s in all_students}
        for rec in all_attendance:
            sid = rec["student_id"]
            if sid in student_counts:
                student_counts[sid] += 1

        stats_data = []
        for s in all_students:
            sid = s["student_id"]
            attended = student_counts[sid]
            pct = (attended / total_sessions * 100.0) if total_sessions > 0 else 0.0
            stats_data.append(
                {
                    "student_id": sid,
                    "student_name": s["student_name"],
                    "department": s.get("department") or "N/A",
                    "attended_sessions": attended,
                    "total_sessions": total_sessions,
                    "percentage": pct,
                }
            )

        print("\n" + "=" * 70)
        print("                  ATTENDANCE ANALYTICS & STATISTICS")
        print("=" * 70)
        print(f"Total Registered Students:  {total_students}")
        print(f"Total Recorded Sessions:    {total_sessions}")
        print(f"Total Attendance Marks:     {len(all_attendance)}")
        if total_sessions > 0 and total_students > 0:
            overall_pct = (len(all_attendance) / (total_sessions * total_students)) * 100.0
            print(f"Overall System Attendance:  {overall_pct:.1f}%")
        print("-" * 70)
        print(f"{'Student ID':<12} {'Name':<20} {'Attended':<10} {'Total':<8} {'Percentage':<10}")
        print("-" * 70)

        for row in stats_data:
            print(
                f"{row['student_id']:<12} {row['student_name']:<20} "
                f"{row['attended_sessions']:<10} {row['total_sessions']:<8} {row['percentage']:<9.1f}%"
            )
        print("=" * 70 + "\n")

        # Generate Matplotlib visualization
        chart_path = None
        if save_chart and total_sessions > 0:
            try:
                import matplotlib.pyplot as plt

                names = [r["student_name"] for r in stats_data]
                percentages = [r["percentage"] for r in stats_data]

                plt.figure(figsize=(9, 5))
                bar_colors = ["#2ecc71" if p >= 75.0 else "#e74c3c" for p in percentages]
                bars = plt.bar(names, percentages, color=bar_colors, width=0.55, edgecolor="#333333")

                plt.axhline(
                    y=75,
                    color="orange",
                    linestyle="--",
                    linewidth=1.5,
                    label="75% Requirement Threshold",
                )

                plt.title("Student-wise Attendance Statistics", fontsize=14, fontweight="bold", pad=12)
                plt.xlabel("Student Name", fontsize=11, labelpad=8)
                plt.ylabel("Attendance Percentage (%)", fontsize=11, labelpad=8)
                plt.ylim(0, 105)
                plt.grid(axis="y", linestyle=":", alpha=0.6)
                plt.legend(loc="lower right")

                for bar in bars:
                    h = bar.get_height()
                    plt.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        h + 1.5,
                        f"{h:.1f}%",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                        fontweight="bold",
                    )

                plt.tight_layout()
                chart_path = config.REPORTS_DIR / "attendance_stats.png"
                plt.savefig(chart_path, dpi=200)
                plt.close()
                print(f"[Chart Generated] Attendance statistics bar chart saved to: {chart_path}")
            except Exception as e:
                print(f"[Notice] Could not generate matplotlib chart: {e}")

        return {
            "total_students": total_students,
            "total_sessions": total_sessions,
            "total_marks": len(all_attendance),
            "student_stats": stats_data,
            "chart_path": str(chart_path) if chart_path else None,
        }

