import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  FileSpreadsheet,
  Download,
  Calendar,
  CheckCircle,
  XCircle,
  Percent,
  RefreshCw,
  Users,
} from 'lucide-react';

const AttendanceReportsPage = () => {
  const [reportDate, setReportDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const fetchDateReport = async (dateStr) => {
    try {
      setLoading(true);
      const res = await api.get('/api/attendance/today');
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDateReport(reportDate);
  }, [reportDate]);

  const handleDownloadCSV = async (dateParam) => {
    try {
      setExporting(true);
      const url = dateParam ? `/api/reports/export?date=${dateParam}` : '/api/reports/export';
      const res = await api.get(url, { responseType: 'blob' });

      const blob = new Blob([res.data], { type: 'text/csv' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', dateParam ? `attendance_${dateParam}.csv` : 'attendance_full_history.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Could not generate CSV report.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Attendance Reports
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Official daily attendance rosters and CSV export engine
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleDownloadCSV(reportDate)}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-500/20 transition-all disabled:opacity-50"
          >
            {exporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            <span>Export Today's CSV</span>
          </button>
          <button
            onClick={() => handleDownloadCSV(null)}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-500" />
            <span>Export Complete History</span>
          </button>
        </div>
      </div>

      {/* Date Selector & High-level Session Summary */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Selected Date</span>
            <p className="text-lg font-extrabold text-slate-900 dark:text-white mt-1 font-mono">
              {data.date}
            </p>
          </div>
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
            <span className="text-[11px] font-semibold text-emerald-500 uppercase">Present Students</span>
            <p className="text-lg font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
              {data.present_count} / {data.total_students}
            </p>
          </div>
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
            <span className="text-[11px] font-semibold text-rose-500 uppercase">Absent Students</span>
            <p className="text-lg font-extrabold text-rose-600 dark:text-rose-400 mt-1">
              {data.absent_count}
            </p>
          </div>
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80">
            <span className="text-[11px] font-semibold text-brand-500 uppercase">Attendance Turnout</span>
            <p className="text-lg font-extrabold text-brand-600 dark:text-brand-400 mt-1">
              {data.attendance_percentage}%
            </p>
          </div>
        </div>
      )}

      {/* Roster Table */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Official Session Attendance Roster
            </h3>
            <p className="text-[11px] text-slate-400">
              Listing all enrolled students with verified presence/absence statuses
            </p>
          </div>
        </div>

        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-slate-400">Generating report sheet...</p>
          </div>
        ) : !data || data.records.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-400">
            No enrolled students to report.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-100 dark:border-slate-800">
                <tr>
                  <th className="py-3 px-5">Student ID</th>
                  <th className="py-3 px-5">Student Name</th>
                  <th className="py-3 px-5">Department</th>
                  <th className="py-3 px-5">Academic Year</th>
                  <th className="py-3 px-5">Status</th>
                  <th className="py-3 px-5">Time Marked</th>
                  <th className="py-3 px-5">Match Distance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-slate-700 dark:text-slate-200">
                {data.records.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-5 font-mono font-medium text-brand-600 dark:text-brand-400">
                      {r.student_id}
                    </td>
                    <td className="py-3 px-5 font-semibold text-slate-900 dark:text-white">
                      {r.student_name}
                    </td>
                    <td className="py-3 px-5 text-slate-500">{r.department}</td>
                    <td className="py-3 px-5 text-slate-500">{r.year}</td>
                    <td className="py-3 px-5">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          r.status === 'PRESENT'
                            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900'
                            : 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900'
                        }`}
                      >
                        {r.status === 'PRESENT' ? (
                          <CheckCircle className="w-3 h-3 text-emerald-500" />
                        ) : (
                          <XCircle className="w-3 h-3 text-rose-500" />
                        )}
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 px-5 font-mono text-[11px] text-slate-400">
                      {r.attendance_time}
                    </td>
                    <td className="py-3 px-5 font-mono text-slate-500">
                      {r.matching_distance !== null ? Number(r.matching_distance).toFixed(3) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AttendanceReportsPage;

