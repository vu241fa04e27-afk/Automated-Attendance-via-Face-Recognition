import React from 'react';
import {
  ScanFace,
  Brain,
  Cpu,
  Database,
  Layers,
  ShieldCheck,
  CheckCircle,
  FileCode,
  Network,
  Scale,
} from 'lucide-react';

const AboutPage = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero Banner */}
      <div className="p-8 rounded-3xl bg-gradient-to-br from-slate-900 via-brand-950 to-slate-900 text-white border border-brand-500/20 shadow-xl relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/20 border border-brand-400/30 text-brand-300 text-xs font-semibold">
            <ScanFace className="w-3.5 h-3.5" /> Computer Vision & Deep Learning
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Automated Attendance System Using Face Recognition
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm leading-relaxed max-w-2xl">
            A production-ready full-stack educational biometric attendance platform engineered using deep convolutional neural networks (FaceNet / MTCNN), FastAPI, and React.
          </p>
        </div>
      </div>

      {/* Problem Statement & Objectives */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Problem Statement
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            Conventional manual roll-call attendance consumes significant lecture time, introduces human recording errors, and is susceptible to proxy attendance. This project solves these challenges by automating instantaneous, contactless biometric identity verification from group photographs or video feeds.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Key Objectives
          </h2>
          <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-2">
            <li className="flex items-center gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              Automate multi-face recognition in crowded classroom photographs
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              Extract 512-dimensional normalized embeddings via FaceNet InceptionResnetV1
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              Perform high-precision identity matching via Euclidean distance and Cosine similarity
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              Enforce relational constraints preventing duplicate attendance records
            </li>
          </ul>
        </div>
      </div>

      {/* Core Scientific Concepts */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-6">
        <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Brain className="w-5 h-5 text-brand-500" /> Core Computer Vision Concepts & Pipeline
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white">
              <Layers className="w-4 h-4 text-brand-500" /> MTCNN (Multi-task Cascaded CNN)
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Employs a 3-stage cascaded architecture (Proposal Network P-Net, Refine Network R-Net, and Output Network O-Net) to achieve robust face localization, bounding box regression, and facial landmark alignment under variable lighting.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white">
              <Network className="w-4 h-4 text-cyan-500" /> FaceNet InceptionResnetV1
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Trained on VGGFace2 using triplet loss function. Maps cropped 160×160 RGB face patches directly to a compact 512-dimensional Euclidean space where squared distances directly correspond to facial similarity.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white">
              <Scale className="w-4 h-4 text-emerald-500" /> Euclidean Distance ($L_2$ Norm)
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed font-mono">
              d(u, v) = sqrt( sum( (u_i - v_i)^2 ) )
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Because vectors are normalized to unit length, identity match is affirmed when d &lt; 0.85.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white">
              <Scale className="w-4 h-4 text-violet-500" /> Cosine Similarity
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed font-mono">
              cos(θ) = (u · v) / (||u|| ||v||)
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Measures the angular alignment between facial vectors in 512-d hyperspace, with threshold &gt; 0.68.
            </p>
          </div>
        </div>
      </div>

      {/* Technology Stack Badges */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
          Technology Stack
        </h3>
        <div className="flex flex-wrap gap-2 text-xs font-semibold">
          <span className="px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            Python 3.11/3.14
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            FastAPI + Uvicorn
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-cyan-50 dark:bg-cyan-950/40 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800">
            React 18 + Vite
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
            Tailwind CSS
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-violet-50 dark:bg-violet-950/40 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800">
            PyTorch + facenet-pytorch
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
            OpenCV (cv2)
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200">
            SQLite3 Database
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            Recharts & Pandas
          </span>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;

