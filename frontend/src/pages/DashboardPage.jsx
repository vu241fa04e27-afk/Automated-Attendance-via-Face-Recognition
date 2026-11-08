import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  Users,
  UserCheck,
  UserX,
  Percent,
  Database,
  Camera,
  Video,
  FileSpreadsheet,
  UserPlus,
  ArrowUpRight,
  TrendingUp,
  Clock,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Legend,
} from 'recharts';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/analytics/dashboard');
      setData(res.data);
    } catch (err) {
      setError('Failed to fetch dashboard metrics from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Loading attendance intelligence...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 rounded-2xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-sm">
        {error || 'Unable to retrieve dashboard information.'}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Enrolled',
      value: data.total_students,
      subtitle: 'Registered students in database',
      icon: Users,
      color: 'from-blue-600 to-cyan-500',
      badge: 'Database',
    },
    {
      title: 'Present Today',
      value: data.present_today,
      subtitle: `${data.today_date}`,
      icon: UserCheck,
      color: 'from-emerald-600 to-teal-500',
      badge: 'Today',
    },
    {
      title: 'Absent Today',
      value: data.absent_today,
      subtitle: 'Students not yet detected',
      icon: UserX,
      color: 'from-rose-600 to-orange-500',
      badge: 'Alert',
    },
    {
      title: 'Attendance Rate',
      value: `${data.today_percentage}%`,
      subtitle: 'Today overall turnout',
      icon: Percent,
      color: 'from-violet-600 to-indigo-500',
      badge: 'Rate',
    },
  ];

  const pieData = [
    { name: 'Present', value: data.present_today, color: '#10b981' },
    { name: 'Absent', value: data.absent_today, color: '#f43f5e' },
  ];

  return (
    <div className="space-y-8">
      {/* Top Welcome & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-500/10 border border-brand-200 dark:border-brand-500/20 text-brand-700 dark:text-brand-300 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" /> AI Attendance Intelligence Active
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Attendance Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time biometric attendance metrics powered by FaceNet InceptionResnetV1 & MTCNN
          </p>
        </div>

        {/* Quick action buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => navigate('/classroom-attendance')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-500/20 transition-all"
          >
            <Camera className="w-4 h-4" /> Take Attendance
          </button>
          <button
            onClick={() => navigate('/webcam-attendance')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 text-white text-xs font-semibold transition-all"
          >
            <Video className="w-4 h-4" /> Live Webcam
          </button>
          <button
            onClick={() => navigate('/register-student')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold transition-all"
          >
            <UserPlus className="w-4 h-4 text-brand-500" /> New Student
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  {card.title}
                </span>
                <div
                  className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${card.color} text-white flex items-center justify-center shadow-md`}
                >
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                  {card.value}
                </div>
                <div className="text-xs text-slate-400 dark:text-slate-500 mt-1 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600"></span>
                  {card.subtitle}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily 7-day Turnout Bar Chart */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-brand-500" /> Recent 7-Day Attendance Trend
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Daily present student count across sessions
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.daily_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} />
                <XAxis dataKey="day_name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #1e293b',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#fff',
                  }}
                />
                <Bar dataKey="present" fill="#3b82f6" radius={[6, 6, 0, 0]} name="Present" />
                <Bar dataKey="absent" fill="#cbd5e1" radius={[6, 6, 0, 0]} name="Absent" opacity={0.6} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Present vs Absent Ratio Donut Chart */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Today's Distribution
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Present vs absent attendance ratio
            </p>
          </div>

          <div className="h-52 w-full flex items-center justify-center my-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #1e293b',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#fff',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              <div>
                <p className="text-[11px] text-slate-400">Present</p>
                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  {data.present_today}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500"></span>
              <div>
                <p className="text-[11px] text-slate-400">Absent</p>
                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  {data.absent_today}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Records & Quick Details Table */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-500" /> Recent Attendance Logs
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live biometric records logged into SQLite
            </p>
          </div>
          <button
            onClick={() => navigate('/attendance-records')}
            className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
          >
            View Complete Log <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {data.recent_records.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            No attendance records logged yet. Use Option A or Option B above to take attendance.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4 rounded-l-xl">Student ID</th>
                  <th className="py-3 px-4">Student Name</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Match Distance</th>
                  <th className="py-3 px-4 rounded-r-xl">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-200">
                {data.recent_records.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium">{r.student_id}</td>
                    <td className="py-3 px-4 font-semibold">{r.student_name}</td>
                    <td className="py-3 px-4 text-slate-500">{r.department || 'N/A'}</td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {r.attendance_date} {r.attendance_time}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500">
                      {r.matching_distance !== null ? Number(r.matching_distance).toFixed(3) : '-'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900">
                        {r.status}
                      </span>
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

export default DashboardPage;

