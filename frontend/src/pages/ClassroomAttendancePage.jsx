import React, { useState } from 'react';
import api from '../services/api';
import {
  Camera,
  Upload,
  CheckCircle,
  AlertCircle,
  Sparkles,
  Users,
  Eye,
  FileSpreadsheet,
  RefreshCw,
  Maximize2,
  Scan,
} from 'lucide-react';

const ClassroomAttendancePage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [showFullImageModal, setShowFullImageModal] = useState(false);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError('');
    }
  };

  const handleProcessImage = async () => {
    if (!selectedFile) {
      setError('Please select or upload a classroom image first.');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await api.post('/api/recognition/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setResult(res.data);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Recognition failed. Please try again.';
      setError(msg);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-blue-700 dark:text-blue-300 text-xs font-semibold mb-2">
          <Scan className="w-3.5 h-3.5" /> Option A: Group Photograph Attendance
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Classroom Image Attendance
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Detect and recognize multiple student faces simultaneously using deep MTCNN and FaceNet inference
        </p>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Upload & Preview on Left, Results on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Selection & Recognition Trigger */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              1. Select Classroom Photo
            </h2>

            {!previewUrl ? (
              <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl p-8 text-center hover:border-brand-500 transition-colors">
                <Upload className="w-10 h-10 mx-auto text-slate-400 mb-2" />
                <p className="text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-200">
                  Upload classroom or group photo
                </p>
                <p className="text-[11px] text-slate-400 mt-1">Supports high-resolution JPG or PNG</p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="classroom-upload"
                />
                <label
                  htmlFor="classroom-upload"
                  className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold cursor-pointer transition-colors shadow-sm"
                >
                  Browse Classroom Photo
                </label>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="relative rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-950 aspect-[4/3] flex items-center justify-center">
                  <img
                    src={result?.annotated_image_base64 || previewUrl}
                    alt="Classroom input"
                    className="w-full h-full object-contain"
                  />
                  {result?.annotated_image_base64 && (
                    <button
                      onClick={() => setShowFullImageModal(true)}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-slate-900/80 text-white hover:bg-slate-900 text-xs flex items-center gap-1 shadow-md"
                    >
                      <Maximize2 className="w-3.5 h-3.5" /> Full View
                    </button>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="change-classroom-upload"
                  />
                  <label
                    htmlFor="change-classroom-upload"
                    className="text-xs font-medium text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 cursor-pointer underline"
                  >
                    Change photo
                  </label>

                  <button
                    onClick={handleProcessImage}
                    disabled={processing}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-blue-500 hover:from-brand-500 hover:to-blue-400 text-white text-xs font-bold shadow-md shadow-brand-500/25 disabled:opacity-50 transition-all"
                  >
                    {processing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Detecting Faces & Matching...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>Start Face Recognition</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Attendance Recognition Results */}
        <div className="lg:col-span-7 space-y-4">
          {!result ? (
            <div className="h-full min-h-[300px] p-8 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex flex-col items-center justify-center text-center">
              <Camera className="w-12 h-12 text-slate-300 dark:text-slate-700 mb-3" />
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200">
                Awaiting Classroom Photo
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Upload a classroom photograph on the left and click "Start Face Recognition" to view detected faces and marked attendance.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Summary Stats Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
                  <p className="text-[10px] text-slate-400 font-medium uppercase">Faces Located</p>
                  <p className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">
                    {result.detections.length}
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
                  <p className="text-[10px] text-emerald-500 font-medium uppercase">Present</p>
                  <p className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {result.present_count}
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
                  <p className="text-[10px] text-rose-500 font-medium uppercase">Absent</p>
                  <p className="text-xl font-extrabold text-rose-600 dark:text-rose-400 mt-0.5">
                    {result.absent_count}
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
                  <p className="text-[10px] text-amber-500 font-medium uppercase">Unknown Faces</p>
                  <p className="text-xl font-extrabold text-amber-600 dark:text-amber-400 mt-0.5">
                    {result.unknown_faces}
                  </p>
                </div>
              </div>

              {/* Roster & Matching Table */}
              <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                      Attendance Session Roster
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Overall Session Attendance: <span className="font-bold text-emerald-500">{result.attendance_percentage}%</span>
                    </p>
                  </div>
                  <span className="text-xs font-mono px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {result.date}
                  </span>
                </div>

                <div className="overflow-x-auto max-h-80">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 uppercase font-semibold sticky top-0">
                      <tr>
                        <th className="py-2.5 px-4">Student ID</th>
                        <th className="py-2.5 px-4">Student Name</th>
                        <th className="py-2.5 px-4">Department</th>
                        <th className="py-2.5 px-4">Match Distance</th>
                        <th className="py-2.5 px-4">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-slate-700 dark:text-slate-200">
                      {result.student_statuses.map((s, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                          <td className="py-2.5 px-4 font-mono font-medium">{s.student_id}</td>
                          <td className="py-2.5 px-4 font-semibold">{s.student_name}</td>
                          <td className="py-2.5 px-4 text-slate-500">{s.department}</td>
                          <td className="py-2.5 px-4 font-mono text-slate-500">
                            {s.matching_distance !== null ? Number(s.matching_distance).toFixed(3) : '-'}
                          </td>
                          <td className="py-2.5 px-4">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                s.status === 'PRESENT'
                                  ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900'
                                  : 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900'
                              }`}
                            >
                              {s.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Full Image Modal */}
      {showFullImageModal && result?.annotated_image_base64 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-4xl bg-slate-900 rounded-3xl p-4 border border-slate-800 shadow-2xl space-y-3">
            <div className="flex items-center justify-between px-2">
              <h3 className="text-sm font-bold text-white">Annotated Face Recognition Output</h3>
              <button
                onClick={() => setShowFullImageModal(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                Close ✕
              </button>
            </div>
            <div className="rounded-2xl overflow-hidden bg-black max-h-[75vh] flex items-center justify-center">
              <img
                src={result.annotated_image_base64}
                alt="Full annotated result"
                className="max-h-[75vh] object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClassroomAttendancePage;

