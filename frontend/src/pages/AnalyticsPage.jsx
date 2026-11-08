import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  BarChart3,
  TrendingUp,
  Percent,
  CheckCircle,
  AlertCircle,
  Users,
  Award,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const AnalyticsPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [studentPercentages, setStudentPercentages] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [dashRes, stuRes] = await Promise.all([
        api.get('/api/analytics/dashboard'),
        api.get('/api/analytics/student-percentages'),
      ]);
      setDashboardData(dashRes.data);
      setStudentPercentages(stuRes.data.students || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading || !dashboardData) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-400">Loading comprehensive analytics...</p>
      </div>
    );
  }

  // Format student percentage chart data
  const studentChartData = studentPercentages.map((s) => ({
    name: s.student_name,
    rate: s.percentage,
    isAbove75: s.percentage >= 75,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Attendance Analytics
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Visual insights, trend analysis, and individual compliance percentages
        </p>
      </div>

      {/* Top 3 High-Level KPI Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase">Total Sessions Held</span>
            <Users className="w-4 h-4 text-brand-500" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900 dark:text-white mt-3">
            {studentPercentages[0]?.total_sessions || 1}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Classroom attendance sessions recorded</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase">Overall System Rate</span>
            <Percent className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-3">
            {dashboardData.today_percentage}%
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Average turnout across all departments</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase">Total Attendance Events</span>
            <Award className="w-4 h-4 text-violet-500" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900 dark:text-white mt-3">
            {dashboardData.total_attendance_records}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Cumulative verified presence events</p>
        </div>
      </div>

      {/* Main Student-wise Compliance Bar Chart with 75% Reference Line */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-brand-500" /> Student Attendance Compliance
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Dashed orange line indicates minimum 75% institutional requirement
          </p>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={studentChartData} margin={{ top: 15, right: 10, left: -20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} />
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} interval={0} angle={-15} textAnchor="end" />
              <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
              <Tooltip
                formatter={(val) => [`${val}%`, 'Attendance Rate']}
                contentStyle={{
                  backgroundColor: '#0f172a',
                  border: '1px solid #1e293b',
                  borderRadius: '12px',
                  fontSize: '12px',
                  color: '#fff',
                }}
              />
              <ReferenceLine y={75} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: '75% Threshold', fill: '#f59e0b', fontSize: 11, position: 'right' }} />
              <Bar dataKey="rate" radius={[6, 6, 0, 0]}>
                {studentChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.isAbove75 ? '#10b981' : '#f43f5e'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Department Breakdown & Individual Roster */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Stats */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Department Performance
          </h3>
          <div className="space-y-3 pt-2">
            {dashboardData.department_stats.map((dept, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{dept.department}</span>
                  <span className="font-bold text-brand-600 dark:text-brand-400">{dept.rate}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                  <div
                    className="h-full bg-brand-500 rounded-full"
                    style={{ width: `${Math.min(100, dept.rate)}%` }}
                  ></div>
                </div>
                <p className="text-[10px] text-slate-400">
                  {dept.present} present out of {dept.total} enrolled students
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Individual Student Table */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Individual Attendance Compliance
          </h3>
          <div className="overflow-x-auto max-h-64">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Student Name</th>
                  <th className="py-2.5 px-3">Attended</th>
                  <th className="py-2.5 px-3">Turnout</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-200">
                {studentPercentages.map((s, idx) => (
                  <tr key={idx}>
                    <td className="py-2.5 px-3 font-semibold">{s.student_name}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-500">
                      {s.attended}/{s.total_sessions}
                    </td>
                    <td className="py-2.5 px-3 font-bold">{s.percentage}%</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          s.percentage >= 75
                            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600'
                            : 'bg-rose-50 dark:bg-rose-950/40 text-rose-600'
                        }`}
                      >
                        {s.percentage >= 75 ? 'ELIGIBLE' : 'SHORTAGE'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;

