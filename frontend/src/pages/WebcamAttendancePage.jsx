import React, { useEffect, useRef, useState } from 'react';
import api from '../services/api';
import {
  Video,
  Play,
  Square,
  AlertCircle,
  CheckCircle,
  UserCheck,
  ScanFace,
  Clock,
  Sparkles,
} from 'lucide-react';

const WebcamAttendancePage = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState('');
  const [sessionAttendees, setSessionAttendees] = useState([]);
  const [lastNotification, setLastNotification] = useState(null);
  const [fps, setFps] = useState(0);

  // Start webcam stream
  const startCamera = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsStreaming(true);
    } catch (err) {
      setError('Could not access webcam. Please ensure camera permissions are granted.');
    }
  };

  // Stop webcam stream
  const stopCamera = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }

    // Clear overlay canvas
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }

    setIsStreaming(false);
  };

  // Continuous frame recognition loop
  useEffect(() => {
    if (!isStreaming) return;

    let isProcessingFrame = false;
    let frameCount = 0;
    const startTime = Date.now();

    intervalRef.current = setInterval(async () => {
      if (isProcessingFrame || !videoRef.current || !canvasRef.current) return;
      if (videoRef.current.readyState !== 4) return; // HAVE_ENOUGH_DATA

      isProcessingFrame = true;

      try {
        const offscreenCanvas = document.createElement('canvas');
        offscreenCanvas.width = 640;
        offscreenCanvas.height = 480;
        const offCtx = offscreenCanvas.getContext('2d');
        offCtx.drawImage(videoRef.current, 0, 0, 640, 480);

        const base64Data = offscreenCanvas.toDataURL('image/jpeg', 0.85);

        // Send frame to Python FastAPI backend
        const res = await api.post('/api/recognition/webcam', {
          image_base64: base64Data,
        });

        const detections = res.data.detections || [];
        drawBoundingBoxes(detections);

        // Check for new attendance marks
        detections.forEach((d) => {
          if (d.marked_now) {
            setLastNotification(`Attendance marked: ${d.student_name} (${d.student_id})`);
            setSessionAttendees((prev) => {
              if (!prev.some((item) => item.student_id === d.student_id)) {
                return [{ ...d, time: d.timestamp }, ...prev];
              }
              return prev;
            });
          }
        });

        frameCount++;
        const elapsedSec = (Date.now() - startTime) / 1000;
        if (elapsedSec > 0) {
          setFps(Math.round((frameCount / elapsedSec) * 10) / 10);
        }
      } catch (err) {
        console.error('Frame processing error:', err);
      } finally {
        isProcessingFrame = false;
      }
    }, 700); // Send frame every 700ms

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isStreaming]);

  // Draw bounding boxes on canvas over video
  const drawBoundingBoxes = (detections) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    detections.forEach((det) => {
      const [x, y, w, h] = det.box;
      const isRec = det.is_recognized;

      ctx.lineWidth = 3;
      ctx.strokeStyle = isRec ? '#10b981' : '#f43f5e'; // Green or Red
      ctx.strokeRect(x, y, w, h);

      // Label background
      const labelText = isRec ? `${det.student_name} (${Number(det.distance).toFixed(2)})` : `UNKNOWN (${Number(det.distance).toFixed(2)})`;
      ctx.font = 'bold 12px "Plus Jakarta Sans", sans-serif';
      const textWidth = ctx.measureText(labelText).width;

      ctx.fillStyle = isRec ? '#10b981' : '#f43f5e';
      ctx.fillRect(x, Math.max(0, y - 22), textWidth + 12, 22);

      // Label text
      ctx.fillStyle = '#ffffff';
      ctx.fillText(labelText, x + 6, Math.max(15, y - 6));
    });
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-xs font-semibold mb-2">
          <Sparkles className="w-3.5 h-3.5" /> Option B: Live Real-Time Video Stream
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Live Webcam Attendance
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Real-time browser camera stream processed frame-by-frame on Python FaceNet backend
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Live Video Canvas */}
        <div className="lg:col-span-8 space-y-4">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    isStreaming ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
                  }`}
                ></span>
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {isStreaming ? `Live Feed • FPS: ${fps}` : 'Camera Offline'}
                </span>
              </div>

              {!isStreaming ? (
                <button
                  onClick={startCamera}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-500/20 transition-all"
                >
                  <Play className="w-3.5 h-3.5" /> Start Live Stream
                </button>
              ) : (
                <button
                  onClick={stopCamera}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-md shadow-rose-500/20 transition-all"
                >
                  <Square className="w-3.5 h-3.5" /> Stop Stream
                </button>
              )}
            </div>

            {/* Video container with overlay canvas */}
            <div className="relative rounded-2xl overflow-hidden bg-slate-950 aspect-[4/3] border border-slate-800 flex items-center justify-center">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                width={640}
                height={480}
                className="w-full h-full object-cover"
              />
              <canvas
                ref={canvasRef}
                width={640}
                height={480}
                className="absolute inset-0 w-full h-full pointer-events-none"
              />

              {!isStreaming && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
                  <Video className="w-12 h-12 mb-3 text-slate-600" />
                  <p className="text-xs">Camera stream is stopped</p>
                  <button
                    onClick={startCamera}
                    className="mt-3 px-4 py-1.5 rounded-xl bg-brand-600 text-white text-xs font-semibold"
                  >
                    Click to Start Camera
                  </button>
                </div>
              )}

              {/* Toast Notification Banner */}
              {lastNotification && (
                <div className="absolute bottom-4 left-4 right-4 p-3 rounded-xl bg-emerald-600/90 backdrop-blur-md text-white text-xs font-bold flex items-center gap-2 shadow-xl animate-fade-in">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{lastNotification}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Attendees Logged in Current Session */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm h-full flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-emerald-500" /> Session Attendees
                </h3>
                <p className="text-[11px] text-slate-400">Marked in SQLite database</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 font-extrabold text-xs">
                {sessionAttendees.length}
              </span>
            </div>

            {sessionAttendees.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-400">
                <ScanFace className="w-10 h-10 text-slate-300 dark:text-slate-700 mb-2" />
                <p className="text-xs font-medium text-slate-600 dark:text-slate-300">
                  No Attendees Yet
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  When a registered student faces the camera, their attendance is instantly recorded once.
                </p>
              </div>
            ) : (
              <div className="flex-1 space-y-2 overflow-y-auto max-h-[420px]">
                {sessionAttendees.map((att, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex items-center justify-between"
                  >
                    <div>
                      <p className="text-xs font-bold text-slate-900 dark:text-white">
                        {att.student_name}
                      </p>
                      <p className="text-[10px] font-mono text-slate-400">ID: {att.student_id}</p>
                    </div>
                    <div className="text-right">
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                        <CheckCircle className="w-3 h-3" /> PRESENT
                      </span>
                      <p className="text-[9px] font-mono text-slate-400">{att.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebcamAttendancePage;

