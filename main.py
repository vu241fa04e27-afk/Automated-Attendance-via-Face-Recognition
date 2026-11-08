"""
SafeSite: Real-Time PPE Detection & Safety Compliance Monitoring
Main Interactive Application & Terminal Runner.

Provides options for:
  1. Live Webcam PPE Detection & Compliance Tracking
  2. Video File / RTSP Stream Safety Monitoring
  3. Batch Testing on Sample Images
  4. Viewing Compliance Benchmarks (mAP@50, Latency, Class APs)
  5. Exporting Violation Audit Logs to CSV
  6. Starting the FastAPI Backend Server
  7. Running Full Automated Verification Suite
"""

import sys
import os
import time
from pathlib import Path
import cv2

import config
from modules.pipeline import SafeSitePipeline
from modules.dataset_generator import generate_yolo_dataset
from modules.evaluator import get_benchmark_report
from database.violations_db import get_compliance_stats, export_violations_csv, get_violations

def print_banner():
    banner = r"""
========================================================================
   ____             ____       _       ____  ____  _____ 
  / ___|  __ _ / _| ___|  __ _(_) |_ __ _ / ___||  _ \| ____|
  \___ \ / _` | |_|  _| / _` | | __/ _` |\___ \| |_) |  _|  
   ___) | (_| |  _| |__| (_| | | || (_| | ___) |  __/| |___ 
  |____/ \__,_|_| |_____\__,_|_|\__\__,_||____/|_|   |_____|
  Real-Time PPE Detection & Safety Compliance Monitoring
========================================================================
Architecture: YOLOv8-nano (Anchor-Free) | Resolution: 640x640
Classes: hard_hat, safety_vest, goggles, person, no_helmet, no_vest
Spatial Rules: Head (Hat), Torso (Vest), Eye (Goggles in Hazard Zones)
========================================================================
"""
    print(banner)

def run_webcam_monitor(camera_index: int = 0, hazard_zone: str = "General Site"):
    """Runs real-time PPE monitoring on live webcam feed."""
    print(f"\n[SafeSite] Connecting to Webcam index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"[Error] Could not open camera {camera_index}. Please verify device connection.")
        return

    pipeline = SafeSitePipeline()
    print("[SafeSite] Monitor running. Press 'q' or ESC in the OpenCV window to exit.")
    print(f"[SafeSite] Active Zone: {hazard_zone}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Warning] Failed to grab frame from camera.")
            break

        result = pipeline.process_frame(frame, hazard_zone=hazard_zone, record_violations=True)
        cv2.imshow("SafeSite PPE Live Safety Monitor", result["annotated_frame"])

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[SafeSite] Webcam monitoring stopped.")

def run_sample_batch_test():
    """Runs detection pipeline across all generated sample images and prints results."""
    print("\n[SafeSite] Generating / Loading YOLO Dataset samples...")
    dataset_info = generate_yolo_dataset()
    print(f"[SafeSite] Dataset configured with {len(dataset_info['samples_generated'])} test cases.")

    pipeline = SafeSitePipeline()
    samples = [
        ("compliant_worker_01.jpg", "General Site", "Compliant Worker"),
        ("violation_missing_hat_02.jpg", "General Site", "Missing Hard Hat"),
        ("violation_missing_vest_03.jpg", "General Site", "Missing Safety Vest"),
        ("violation_no_ppe_04.jpg", "General Site", "No PPE Violation"),
        ("compliant_worker_01.jpg", "Welding & Grinding Zone", "Hazard Zone Goggles Check"),
    ]

    print("\n" + "=" * 76)
    print(f"{'Sample Image':<30} | {'Zone':<18} | {'Status':<10} | {'Missing Items'}")
    print("=" * 76)

    for fname, zone, desc in samples:
        img_path = config.DATASET_DIR / "images" / "train" / fname
        if not img_path.exists():
            continue

        img = cv2.imread(str(img_path))
        res = pipeline.process_frame(img, hazard_zone=zone, record_violations=True, is_static_image=True)
        worker = res["workers"][0] if res["workers"] else {"compliance_status": "NONE", "missing_items": []}
        status = worker["compliance_status"]
        missing = ", ".join(worker["missing_items"]) if worker["missing_items"] else "None"

        print(f"{fname:<30} | {zone:<18} | {status:<10} | {missing}")

        # Save annotated result
        out_path = config.OUTPUT_DIR / f"test_result_{fname}"
        cv2.imwrite(str(out_path), res["annotated_frame"])

    print("=" * 76)
    print(f"[SafeSite] Annotated test images saved in: {config.OUTPUT_DIR}\n")

def display_benchmarks():
    """Prints project technical report benchmarks."""
    report = get_benchmark_report()
    print("\n" + "=" * 65)
    print("      SAFESITE PPE DETECTION - TECHNICAL BENCHMARK REPORT      ")
    print("=" * 65)
    print(f"Model Architecture : {report['model_architecture']}")
    print(f"Input Resolution   : {report['input_resolution']}")
    print(f"Parameters         : {report['parameters']} | GFLOPs: {report['gflops']}")
    print(f"mAP @ 0.50         : {report['mAP_50']}%")
    print(f"mAP @ 0.50:0.95    : {report['mAP_50_95']}%")
    print(f"Overall Precision  : {report['precision']}% | Recall: {report['recall']}%")
    print(f"CPU Latency        : {report['latency_metrics']['total_latency_ms']} ms ({report['latency_metrics']['fps_cpu']} FPS)")
    print("-" * 65)
    print(f"{'Class Name':<25} | {'AP@50 (%)':<10} | {'Precision (%)':<14} | {'Recall (%)'}")
    print("-" * 65)
    for c in report["class_metrics"]:
        print(f"{c['display']:<25} | {c['ap_50']:<10.1f} | {c['precision']:<14.1f} | {c['recall']:<10.1f}")
    print("=" * 65 + "\n")

def export_audit_log():
    """Exports SQLite violations to CSV."""
    csv_path = export_violations_csv()
    print(f"\n[SafeSite] Violations audit log successfully exported to:")
    print(f"  👉 {csv_path}\n")

def start_backend_server():
    """Starts Uvicorn FastAPI backend server."""
    print("\n[SafeSite] Starting FastAPI backend on http://localhost:8000 ...")
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)

def main():
    print_banner()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "test":
            run_sample_batch_test()
            return
        elif cmd == "server":
            start_backend_server()
            return
        elif cmd == "benchmark":
            display_benchmarks()
            return
        elif cmd == "webcam":
            run_webcam_monitor()
            return

    while True:
        print("\n--- SafeSite Main Menu ---")
        print("1. Run Sample Batch Test on All PPE Scenarios")
        print("2. Launch Live Webcam PPE Monitor (with visual alerts & sound)")
        print("3. View Technical Evaluation & mAP Benchmarks")
        print("4. Export Safety Violations Audit Log (CSV)")
        print("5. Start FastAPI Backend Server (Port 8000)")
        print("6. Exit")

        choice = input("\nEnter choice [1-6]: ").strip()
        if choice == "1":
            run_sample_batch_test()
        elif choice == "2":
            run_webcam_monitor()
        elif choice == "3":
            display_benchmarks()
        elif choice == "4":
            export_audit_log()
        elif choice == "5":
            start_backend_server()
        elif choice == "6":
            print("\nExiting SafeSite PPE Monitoring System. Stay safe!\n")
            break
        else:
            print("[Warning] Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()
