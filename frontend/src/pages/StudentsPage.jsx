import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  Users,
  Search,
  Filter,
  UserPlus,
  Trash2,
  Edit2,
  Eye,
  ScanFace,
  X,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

const StudentsPage = () => {
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');

  // Modals state
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [viewDetailsModal, setViewDetailsModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [deleteModal, setDeleteModal] = useState(false);
  const [editFormData, setEditFormData] = useState({ student_name: '', department: '', year: '' });
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState('');

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const params = {};
      if (search) params.search = search;
      if (deptFilter) params.department = deptFilter;
      if (yearFilter) params.year = yearFilter;

      const res = await api.get('/api/students', { params });
      setStudents(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [deptFilter, yearFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchStudents();
  };

  const openViewModal = async (student) => {
    try {
      const res = await api.get(`/api/students/${student.student_id}`);
      setSelectedStudent(res.data);
      setViewDetailsModal(true);
    } catch (err) {
      alert('Could not fetch student details.');
    }
  };

  const openEditModal = (student) => {
    setSelectedStudent(student);
    setEditFormData({
      student_name: student.student_name,
      department: student.department || '',
      year: student.year || '',
    });
    setEditModal(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await api.put(`/api/students/${selectedStudent.student_id}`, editFormData);
      setMessage(`Student ${editFormData.student_name} updated successfully.`);
      setEditModal(false);
      fetchStudents();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update student.');
    } finally {
      setActionLoading(false);
    }
  };

  const openDeleteModal = (student) => {
    setSelectedStudent(student);
    setDeleteModal(true);
  };

  const handleDeleteSubmit = async () => {
    setActionLoading(true);
    try {
      await api.delete(`/api/students/${selectedStudent.student_id}`);
      setMessage(`Student ${selectedStudent.student_name} and associated facial data permanently deleted.`);
      setDeleteModal(false);
      fetchStudents();
    } catch (err) {
      alert('Failed to delete student.');
    } finally {
      setActionLoading(false);
    }
  };

  // Distinct departments & years for filter dropdowns
  const departments = Array.from(new Set(students.map((s) => s.department).filter(Boolean)));
  const years = Array.from(new Set(students.map((s) => s.year).filter(Boolean)));

  return (
    <div className="space-y-6">
      {/* Header & New Student Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Student Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Directory of registered students and their biometric face embeddings
          </p>
        </div>

        <button
          onClick={() => navigate('/register-student')}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-500/20 transition-all"
        >
          <UserPlus className="w-4 h-4" /> Enroll New Student
        </button>
      </div>

      {/* Success Notification Banner */}
      {message && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>{message}</span>
          </div>
          <button onClick={() => setMessage('')} className="text-emerald-500 hover:text-emerald-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search student by Name or ID..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </form>

        <div className="flex items-center gap-2">
          <select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-200 focus:outline-none"
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-200 focus:outline-none"
          >
            <option value="">All Years</option>
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>

          {(search || deptFilter || yearFilter) && (
            <button
              onClick={() => {
                setSearch('');
                setDeptFilter('');
                setYearFilter('');
              }}
              className="px-3 py-2 rounded-xl text-xs font-semibold text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Students Data Table */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-slate-400">Loading student directory...</p>
          </div>
        ) : students.length === 0 ? (
          <div className="py-16 text-center">
            <Users className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-700 mb-3" />
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">No Students Found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              No registered student matched your query. Use the enroll button to add students.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-100 dark:border-slate-800">
                <tr>
                  <th className="py-3.5 px-5">Student ID</th>
                  <th className="py-3.5 px-5">Student Name</th>
                  <th className="py-3.5 px-5">Department</th>
                  <th className="py-3.5 px-5">Academic Year</th>
                  <th className="py-3.5 px-5">Registration Date</th>
                  <th className="py-3.5 px-5">Face Samples</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-slate-700 dark:text-slate-200">
                {students.map((student) => (
                  <tr key={student.student_id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-5 font-mono font-semibold text-brand-600 dark:text-brand-400">
                      {student.student_id}
                    </td>
                    <td className="py-3.5 px-5 font-semibold text-slate-900 dark:text-white">
                      {student.student_name}
                    </td>
                    <td className="py-3.5 px-5 text-slate-500 dark:text-slate-400">
                      {student.department || 'N/A'}
                    </td>
                    <td className="py-3.5 px-5 text-slate-500 dark:text-slate-400">
                      {student.year || 'N/A'}
                    </td>
                    <td className="py-3.5 px-5 font-mono text-[11px] text-slate-400">
                      {student.registration_date}
                    </td>
                    <td className="py-3.5 px-5">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900">
                        <ScanFace className="w-3.5 h-3.5 text-blue-500" />
                        {student.face_samples_count} sample{student.face_samples_count !== 1 ? 's' : ''}
                      </span>
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => openViewModal(student)}
                          title="View Profile Details"
                          className="p-1.5 rounded-lg text-slate-500 hover:text-brand-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openEditModal(student)}
                          title="Edit Student Info"
                          className="p-1.5 rounded-lg text-slate-500 hover:text-amber-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openDeleteModal(student)}
                          title="Delete Student"
                          className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Student Modal */}
      {editModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Edit Student Details
              </h3>
              <button onClick={() => setEditModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-4 mt-5">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                  Student ID (Read-only)
                </label>
                <input
                  type="text"
                  value={selectedStudent?.student_id || ''}
                  disabled
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 font-mono text-xs text-slate-500 cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Student Name
                </label>
                <input
                  type="text"
                  value={editFormData.student_name}
                  onChange={(e) => setEditFormData({ ...editFormData, student_name: e.target.value })}
                  required
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Department
                </label>
                <input
                  type="text"
                  value={editFormData.department}
                  onChange={(e) => setEditFormData({ ...editFormData, department: e.target.value })}
                  placeholder="e.g. Computer Science"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Academic Year
                </label>
                <input
                  type="text"
                  value={editFormData.year}
                  onChange={(e) => setEditFormData({ ...editFormData, year: e.target.value })}
                  placeholder="e.g. 3rd Year"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3">
                <button
                  type="button"
                  onClick={() => setEditModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-sm"
                >
                  {actionLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-2xl">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 flex items-center justify-center mb-4">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Permanently Delete Student?
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">
              This action will completely remove <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedStudent?.student_name}</span> (ID: {selectedStudent?.student_id}) along with all associated facial embeddings, disk images, and attendance history. This action cannot be undone.
            </p>

            <div className="flex items-center justify-end gap-2.5 mt-6">
              <button
                type="button"
                onClick={() => setDeleteModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteSubmit}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-sm"
              >
                {actionLoading ? 'Deleting...' : 'Confirm Deletion'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Profile Details Modal */}
      {viewDetailsModal && selectedStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 flex items-center justify-center font-bold text-sm">
                  {selectedStudent.student.student_name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    {selectedStudent.student.student_name}
                  </h3>
                  <p className="text-xs font-mono text-slate-400">ID: {selectedStudent.student.student_id}</p>
                </div>
              </div>
              <button onClick={() => setViewDetailsModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 my-5 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50">
              <div>
                <p className="text-[11px] text-slate-400 uppercase font-medium">Department</p>
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                  {selectedStudent.student.department || 'Not specified'}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-400 uppercase font-medium">Academic Year</p>
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                  {selectedStudent.student.year || 'Not specified'}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-400 uppercase font-medium">Enrolled Face Vectors</p>
                <p className="text-xs font-semibold text-brand-600 dark:text-brand-400 mt-0.5">
                  {selectedStudent.face_samples_count} embeddings
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-400 uppercase font-medium">Attendance Rate</p>
                <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5">
                  {selectedStudent.attendance_percentage}% ({selectedStudent.attended_sessions}/{selectedStudent.total_sessions} sessions)
                </p>
              </div>
            </div>

            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Recent Attendance History
            </h4>
            {selectedStudent.recent_history.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No attendance records yet for this student.</p>
            ) : (
              <div className="space-y-1.5 max-h-40 overflow-y-auto">
                {selectedStudent.recent_history.map((h, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-xs">
                    <span className="font-mono text-slate-500">{h.attendance_date} at {h.attendance_time}</span>
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400">{h.status}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end mt-6">
              <button
                onClick={() => setViewDetailsModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900 dark:bg-slate-800 text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentsPage;

