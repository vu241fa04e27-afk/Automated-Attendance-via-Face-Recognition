# Automated Attendance System Using Face Recognition (Full-Stack Web Application)

A modern, production-grade Full-Stack Computer Vision Web Application built with **FastAPI**, **React (Vite + Tailwind CSS)**, **FaceNet (InceptionResnetV1)**, **MTCNN**, and **SQLite**.

Converts the deep learning facial recognition pipeline into an AI-powered student attendance management platform with live webcam recognition, group classroom photograph processing, and interactive analytics.

---

## 1. Project Architecture

```
Automated_Attendance_System/
│
├── frontend/                          # React + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── components/                # ProtectedRoute & reusable UI widgets
│   │   ├── context/                   # AuthContext & ThemeContext (Dark/Light)
│   │   ├── layouts/                   # DashboardLayout (Sidebar & Top Navbar)
│   │   ├── pages/                     # 11 Modern Application Pages
│   │   │   ├── LoginPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── StudentsPage.jsx
│   │   │   ├── RegisterStudentPage.jsx
│   │   │   ├── ClassroomAttendancePage.jsx
│   │   │   ├── WebcamAttendancePage.jsx
│   │   │   ├── AttendanceRecordsPage.jsx
│   │   │   ├── AttendanceReportsPage.jsx
│   │   │   ├── AnalyticsPage.jsx
│   │   │   ├── AboutPage.jsx
│   │   │   └── SettingsPage.jsx
│   │   ├── services/                  # Axios API client with Bearer interceptors
│   │   ├── App.jsx                    # React Router configuration
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── vercel.json                    # Vercel SPA deployment configuration
│
├── backend/                           # FastAPI RESTful API Backend
│   ├── app/
│   │   ├── auth/                      # PBKDF2 hashing & HMAC-SHA256 bearer tokens
│   │   ├── routes/                    # API Routers
│   │   │   ├── auth.py                # Admin authentication
│   │   │   ├── students.py            # Student CRUD & Face uploads
│   │   │   ├── recognition.py         # Classroom & Webcam frame inference
│   │   │   ├── attendance.py          # Daily attendance & history logs
│   │   │   ├── analytics.py           # Dashboard KPIs, trends & distributions
│   │   │   ├── reports.py             # CSV export streams
│   │   │   └── settings.py            # Runtime recognition threshold calibration
│   │   ├── schemas/                   # Pydantic request & response models
│   │   └── main.py                    # FastAPI server entrypoint
│   └── requirements.txt
│
├── modules/                           # Core Computer Vision Engine
│   ├── face_detection.py              # MTCNN & OpenCV Haar Cascade
│   ├── face_embedding.py              # FaceNet InceptionResnetV1 (512-d embeddings)
│   ├── face_matching.py               # Euclidean Distance & Cosine Similarity
│   ├── attendance_manager.py          # Frame & classroom image attendance engine
│   ├── student_registration.py        # Image decoding & biometric storage
│   ├── webcam_attendance.py           # Standalone webcam controller
│   └── reports.py                     # Pandas CSV generator & stats
│
├── database/
│   ├── attendance.db                  # SQLite database (STUDENTS, ATTENDANCE, EMBEDDINGS, ADMINS)
│   └── db_manager.py                  # Database operations & connection pooling
│
├── dataset/
│   ├── student_images/                # Student biometric face samples
│   └── classroom_images/              # Classroom & group test photographs
│
├── models/
│   └── haarcascade_frontalface_default.xml # Haar Cascade fallback classifier
│
├── run_server.py                      # One-command backend launcher
├── main.py                            # Terminal CLI version (preserved)
├── requirements.txt                   # Root dependencies
└── README.md
```

---

## 2. Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Frontend Framework** | React 18 + Vite | Single Page Application (SPA) with fast HMR |
| **Styling & Theme** | Tailwind CSS | Modern Navy & Blue AI palette with Dark/Light modes |
| **Icons & Charts** | Lucide React & Recharts | Interactive SVG icons and responsive analytics charts |
| **HTTP Client** | Axios | Automatic Bearer token injection and error interceptors |
| **Backend Framework** | FastAPI + Uvicorn | High-throughput asynchronous Python ASGI web framework |
| **Deep Learning Models** | FaceNet `InceptionResnetV1` | Pretrained on VGGFace2, 512-dimensional $L_2$-normalized embeddings |
| **Face Detectors** | MTCNN & Haar Cascade | Multi-scale face detection with landmark alignment |
| **Distance Metrics** | Euclidean Distance & Cosine Similarity | Real-time metric comparison with ambiguity margin checks |
| **Database** | SQLite3 | Relational schema with foreign keys and unique constraints |

---

## 3. Website Features & Pages

### 1. Login Page (`/login`)
- Secure administrator authentication portal.
- Default demonstration credentials:
  - **Username**: `admin`
  - **Password**: `admin123`
- Cryptographic PBKDF2-HMAC-SHA256 password verification with unique salting.
- Form validation and password visibility toggle.

### 2. Dashboard (`/`)
- Real-time KPI cards: **Total Enrolled**, **Present Today**, **Absent Today**, and **Turnout Rate**.
- Recharts visualizations: 7-day daily turnout trend and today's present-to-absent donut chart.
- Quick action buttons to start classroom attendance, launch live webcam, or enroll a student.
- Live recent attendance log stream from the database.

### 3. Student Management (`/students`)
- Directory of all enrolled students with stored face sample counts.
- Search by Student ID or Name; filter by department and academic year.
- **View Profile**: Inspect attendance percentages, session counts, and recent logs.
- **Edit Student**: Update student name, department, or academic year.
- **Delete Student**: Cascadingly purges student records, face embeddings, attendance entries, and stored photos.

### 4. Student Registration (`/register-student`)
- Complete student enrollment with demographic metadata.
- **Option A (File Upload)**: Upload multiple face photographs with drag-and-drop and image previews.
- **Option B (Browser Webcam)**: Request camera permissions in the browser, view live preview, and take snapshots directly into the enrollment gallery.
- Real-time face detection validation; extracts FaceNet embeddings on submit.

### 5. Classroom Photograph Attendance (`/classroom-attendance`)
- Upload a full classroom/group photo (or use sample `dataset/classroom_images/classroom.jpg`).
- Click **Start Face Recognition**:
  - Detects all visible faces via MTCNN.
  - Extracts 512-dimensional FaceNet embeddings.
  - Matches identities against enrolled database records.
  - Automatically marks recognized students as `PRESENT` in SQLite.
  - Flags undetected students as `ABSENT`.
  - Flags non-enrolled individuals as `UNKNOWN`.
- Displays side-by-side results: annotated image with green/red bounding boxes, distance scores, and session roster table.

### 6. Live Webcam Attendance (`/webcam-attendance`)
- Accesses browser webcam with user permission.
- Transmits video frames to FastAPI backend at controlled intervals.
- Overlays real-time green/red bounding boxes and student identification labels directly on the video feed.
- Automatically marks attendance **once per student per date** in the database.
- Displays toast notifications and a live list of attendees marked during the active session.

### 7. Attendance Records (`/attendance-records`)
- Complete historical attendance log.
- Filter by date (calendar picker), department, and attendance status (`PRESENT` or `ABSENT`).
- Real-time search by student name or ID.
- One-click CSV export button.

### 8. Attendance Reports (`/reports`)
- Official attendance roster breakdown for any date.
- Shows total enrolled, present count, absent count, and percentage.
- Direct downloads for **Daily Attendance CSV** and **Complete Historical Log CSV**.

### 9. Attendance Analytics (`/analytics`)
- Institutional compliance tracking.
- Student-wise attendance percentage bar chart with a **75% minimum institutional requirement threshold line**.
- Department performance comparison cards.
- Attendance eligibility status tags (`ELIGIBLE` vs `SHORTAGE`).

### 10. Settings & Configuration (`/settings`)
- Interactive sliders to calibrate Computer Vision hyperparameters:
  - **Euclidean Distance Threshold** (default: `0.85`)
  - **Cosine Similarity Threshold** (default: `0.68`)
  - **Ambiguity Margin** (default: `0.08`)
  - **Default Matching Metric** (Euclidean / Cosine)
- Administrator password update form.
- Deep learning inference details (model name, input dimensions, embedding size).

### 11. About Project (`/about`)
- Comprehensive overview of the Computer Vision pipeline: MTCNN (P-Net, R-Net, O-Net), FaceNet triplet loss, hypersphere embedding mechanics, and distance metric mathematics.

---

## 4. Execution & Setup Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.11 and 3.14)
- Node.js v18+ and npm

---

### Step 1: Start the FastAPI Backend

Open a terminal in the project root directory:

```powershell
# 1. Activate virtual environment (if using one)
venv\Scripts\activate

# 2. Install backend dependencies (if not already installed)
pip install -r backend/requirements.txt

# 3. Launch FastAPI server
python run_server.py
```
Backend will start on: **`http://127.0.0.1:8000`**  
Interactive API Docs (Swagger): **`http://127.0.0.1:8000/docs`**

---

### Step 2: Start the React Frontend

Open a second terminal window in the project directory:

```powershell
# 1. Navigate to frontend folder
cd frontend

# 2. Install dependencies (if not already installed)
npm install

# 3. Start development server
npm run dev
```
Frontend will be available at: **`http://localhost:5173`**

---

### Step 3: Log In to the Web Dashboard
1. Open your browser and navigate to **`http://localhost:5173`**.
2. Sign in with:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Explore the dashboard, enroll students, and test classroom or live webcam attendance!

---

## 5. Deployment Guide

### Frontend Deployment (Vercel)
The React frontend is pre-configured for Vercel deployment:
1. Push the project to GitHub.
2. Import the repository in [Vercel](https://vercel.com).
3. Set the **Root Directory** to `frontend`.
4. In **Environment Variables**, add:
   ```
   VITE_API_URL=https://<your-deployed-python-backend-domain>
   ```
5. Deploy! The included `vercel.json` ensures client-side routing works for all 11 pages.

### Backend Deployment (Render / Railway / VPS)
Deploy the Python FastAPI backend to any service supporting Python 3.10+ and PyTorch (e.g. Render, Railway, AWS EC2, or DigitalOcean droplet):
1. Build command:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Start command:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```
3. Set environment variable:
   ```
   ATTENDANCE_SECRET_KEY=<your-secure-random-secret-key>
   ```

---

## 6. Biometric Privacy & Security Compliance

- **Local Neural Inference**: Pretrained FaceNet model inference executes entirely on your backend server; no biometric images or vectors are shared with third-party cloud APIs.
- **Biometric Minimization**: Embeddings are stored as raw float32 numerical vectors rather than storing high-resolution face photographs in databases.
- **Cascading Deletion**: Option in Student Management completely purges a student's facial embeddings, disk photos, and attendance entries.
- **Repository Safety**: `.gitignore` ensures that database files (`.db`), student photographs, and pretrained weights are never committed to public version control.
