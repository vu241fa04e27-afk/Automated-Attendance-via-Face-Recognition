import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';

import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import StudentsPage from './pages/StudentsPage';
import RegisterStudentPage from './pages/RegisterStudentPage';
import ClassroomAttendancePage from './pages/ClassroomAttendancePage';
import WebcamAttendancePage from './pages/WebcamAttendancePage';
import AttendanceRecordsPage from './pages/AttendanceRecordsPage';
import AttendanceReportsPage from './pages/AttendanceReportsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AboutPage from './pages/AboutPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected dashboard routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/students" element={<StudentsPage />} />
                <Route path="/register-student" element={<RegisterStudentPage />} />
                <Route path="/classroom-attendance" element={<ClassroomAttendancePage />} />
                <Route path="/webcam-attendance" element={<WebcamAttendancePage />} />
                <Route path="/attendance-records" element={<AttendanceRecordsPage />} />
                <Route path="/reports" element={<AttendanceReportsPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/about" element={<AboutPage />} />
              </Route>
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

