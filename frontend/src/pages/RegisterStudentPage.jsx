import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  UserPlus,
  Upload,
  Camera,
  Trash2,
  CheckCircle,
  AlertCircle,
  ScanFace,
  X,
  RefreshCw,
} from 'lucide-react';

const RegisterStudentPage = () => {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [formData, setFormData] = useState({
    student_id: '',
    student_name: '',
    department: '',
    year: '',
  });

  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'webcam'
  const [selectedFiles, setSelectedFiles] = useState([]); // array of File objects or dataURLs
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [mediaStream, setMediaStream] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Start browser webcam
  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setMediaStream(stream);
      setIsWebcamActive(true);
      setError('');
    } catch (err) {
      setError('Could not access your webcam. Please allow camera permissions in your browser.');
    }
  };

  // Stop browser webcam
  const stopWebcam = () => {
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
      setMediaStream(null);
    }
    setIsWebcamActive(false);
  };

  // Capture frame from webcam canvas
  const captureWebcamSnapshot = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      const file = new File([blob], `webcam_sample_${Date.now()}.jpg`, { type: 'image/jpeg' });
      const previewUrl = URL.createObjectURL(blob);
      setSelectedFiles((prev) => [...prev, { file, previewUrl }]);
    }, 'image/jpeg', 0.95);
  };

  // Handle local file selection
  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    const newItems = files.map((file) => ({
      file,
      previewUrl: URL.createObjectURL(file),
    }));
    setSelectedFiles((prev) => [...prev, ...newItems]);
  };

  // Remove selected image
  const removeImage = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Submit enrollment form
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.student_id.trim() || !formData.student_name.trim()) {
      setError('Student ID and Student Name are required.');
      return;
    }

    if (selectedFiles.length === 0) {
      setError('Please provide at least 1 face photograph for facial embedding extraction.');
      return;
    }

    setSubmitting(true);
    setError('');
    setSuccessMsg('');

    try {
      const formPayload = new FormData();
      formPayload.append('student_id', formData.student_id.trim());
      formPayload.append('student_name', formData.student_name.trim());
      if (formData.department) formPayload.append('department', formData.department.trim());
      if (formData.year) formPayload.append('year', formData.year.trim());

      selectedFiles.forEach((item) => {
        formPayload.append('images', item.file);
      });

      const res = await api.post('/api/students', formPayload, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setSuccessMsg(res.data.message || 'Student enrolled successfully!');
      stopWebcam();
      // Reset form
      setFormData({ student_id: '', student_name: '', department: '', year: '' });
      setSelectedFiles([]);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed. Ensure face images are clear.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Register New Student
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Capture student metadata and extract FaceNet deep feature embeddings
        </p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError('')} className="text-rose-400 hover:text-rose-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button
            onClick={() => navigate('/students')}
            className="text-xs font-bold text-emerald-600 hover:underline"
          >
            View Directory →
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Metadata Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider text-brand-600 dark:text-brand-400">
            1. Student Information
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Student ID <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={formData.student_id}
                onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                placeholder="e.g. 104 or CS-2024-001"
                required
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Student Full Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={formData.student_name}
                onChange={(e) => setFormData({ ...formData, student_name: e.target.value })}
                placeholder="e.g. Ananya Sen"
                required
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Department (Optional)
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                placeholder="e.g. Computer Science & Engineering"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Academic Year (Optional)
              </label>
              <input
                type="text"
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                placeholder="e.g. 3rd Year"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>
        </div>

        {/* Biometric Face Samples Enrollment Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider text-brand-600 dark:text-brand-400">
                2. Face Biometric Samples
              </h2>
              <p className="text-xs text-slate-400">
                Multiple samples from different angles improve recognition robustness
              </p>
            </div>

            {/* Tab switch */}
            <div className="flex rounded-xl bg-slate-100 dark:bg-slate-800 p-1">
              <button
                type="button"
                onClick={() => {
                  setActiveTab('upload');
                  stopWebcam();
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'upload'
                    ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Upload className="w-3.5 h-3.5" /> File Upload
              </button>
              <button
                type="button"
                onClick={() => {
                  setActiveTab('webcam');
                  startWebcam();
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'webcam'
                    ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Camera className="w-3.5 h-3.5" /> Browser Webcam
              </button>
            </div>
          </div>

          {/* Tab 1: File Upload */}
          {activeTab === 'upload' && (
            <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl p-6 text-center hover:border-brand-500 transition-colors">
              <Upload className="w-10 h-10 mx-auto text-slate-400 mb-2" />
              <p className="text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-200">
                Drag and drop face photographs here, or click to browse
              </p>
              <p className="text-[11px] text-slate-400 mt-1">Supports JPG, PNG, WEBP (multiple files allowed)</p>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
                id="face-file-upload"
              />
              <label
                htmlFor="face-file-upload"
                className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-semibold text-slate-800 dark:text-slate-200 cursor-pointer transition-colors"
              >
                Select Face Photos
              </label>
            </div>
          )}

          {/* Tab 2: Browser Live Webcam Capture */}
          {activeTab === 'webcam' && (
            <div className="space-y-4">
              <div className="relative rounded-2xl overflow-hidden bg-slate-950 aspect-video max-w-lg mx-auto border border-slate-800 flex items-center justify-center">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                {!isWebcamActive && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 p-4">
                    <Camera className="w-10 h-10 mb-2" />
                    <p className="text-xs">Webcam feed inactive</p>
                    <button
                      type="button"
                      onClick={startWebcam}
                      className="mt-3 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-medium"
                    >
                      Start Camera
                    </button>
                  </div>
                )}
              </div>

              {isWebcamActive && (
                <div className="flex justify-center gap-3">
                  <button
                    type="button"
                    onClick={captureWebcamSnapshot}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-500/20"
                  >
                    <Camera className="w-4 h-4" /> Capture Snapshot
                  </button>
                  <button
                    type="button"
                    onClick={stopWebcam}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold"
                  >
                    Stop Camera
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Selected Face Gallery Preview */}
          {selectedFiles.length > 0 && (
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  Ready to enroll ({selectedFiles.length} sample{selectedFiles.length !== 1 ? 's' : ''}):
                </p>
                <button
                  type="button"
                  onClick={() => setSelectedFiles([])}
                  className="text-xs text-rose-500 hover:underline"
                >
                  Clear all
                </button>
              </div>

              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
                {selectedFiles.map((item, idx) => (
                  <div
                    key={idx}
                    className="relative group rounded-xl overflow-hidden aspect-square border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 shadow-sm"
                  >
                    <img
                      src={item.previewUrl}
                      alt={`sample-${idx}`}
                      className="w-full h-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage(idx)}
                      className="absolute top-1 right-1 p-1 rounded-full bg-rose-600 text-white opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                    <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-slate-900/70 text-[9px] font-mono text-white">
                      #{idx + 1}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/students')}
            className="px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md shadow-brand-500/25 disabled:opacity-50 transition-all"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Extracting FaceNet Embeddings...</span>
              </>
            ) : (
              <>
                <ScanFace className="w-4 h-4" />
                <span>Complete Student Enrollment</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RegisterStudentPage;

