import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  Settings,
  Sliders,
  Shield,
  Save,
  CheckCircle,
  AlertCircle,
  Info,
  KeyRound,
  RefreshCw,
} from 'lucide-react';

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    euclidean_threshold: 0.85,
    cosine_threshold: 0.68,
    ambiguity_margin: 0.08,
    default_detector: 'mtcnn',
    matching_metric: 'euclidean',
    embedding_model: 'FaceNet InceptionResnetV1 (vggface2)',
    embedding_dimension: 512,
  });

  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [loading, setLoading] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [settingsMsg, setSettingsMsg] = useState('');
  const [passwordMsg, setPasswordMsg] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/settings');
      setSettings(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSettingsSubmit = async (e) => {
    e.preventDefault();
    setSavingSettings(true);
    setSettingsMsg('');
    try {
      await api.put('/api/settings', {
        euclidean_threshold: Number(settings.euclidean_threshold),
        cosine_threshold: Number(settings.cosine_threshold),
        ambiguity_margin: Number(settings.ambiguity_margin),
        default_detector: settings.default_detector,
        matching_metric: settings.matching_metric,
      });
      setSettingsMsg('Recognition settings and thresholds updated successfully.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update settings.');
    } finally {
      setSavingSettings(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordMsg('');
    setPasswordError('');

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('New passwords do not match.');
      return;
    }
    if (passwordForm.new_password.length < 6) {
      setPasswordError('Password must be at least 6 characters long.');
      return;
    }

    setChangingPassword(true);
    try {
      const res = await api.post('/api/auth/change-password', {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      });
      setPasswordMsg(res.data.message);
      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setPasswordError(err.response?.data?.detail || 'Failed to change password.');
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-400">Loading system configuration...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          System Settings & Configuration
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Tune Computer Vision recognition hyperparameters and administrator security
        </p>
      </div>

      {/* Model & System Info Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-900 to-slate-900 text-white border border-brand-700/40 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-brand-300">
            Active Pretrained Inference Engine
          </span>
          <h2 className="text-lg font-bold mt-1 text-white">{settings.embedding_model}</h2>
          <p className="text-xs text-slate-300 mt-0.5">
            512-dimensional $L_2$-normalized hypersphere embedding vectors
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-xl bg-white/10 text-xs font-mono border border-white/15">
            Input: 160×160 RGB
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
            Local Execution
          </span>
        </div>
      </div>

      {/* Card 1: Face Matching Hyperparameters Form */}
      <form onSubmit={handleSettingsSubmit} className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Recognition Thresholds & Calibration
            </h3>
          </div>
        </div>

        {settingsMsg && (
          <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>{settingsMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Euclidean Threshold */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Euclidean Distance Threshold
              </label>
              <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400">
                {settings.euclidean_threshold}
              </span>
            </div>
            <input
              type="range"
              min="0.40"
              max="1.20"
              step="0.01"
              value={settings.euclidean_threshold}
              onChange={(e) => setSettings({ ...settings, euclidean_threshold: e.target.value })}
              className="w-full accent-brand-600 cursor-pointer"
            />
            <p className="text-[10px] text-slate-400 mt-1">
              Lower distance = stricter match. Recommended: 0.80 - 0.90 (Default: 0.85).
            </p>
          </div>

          {/* Cosine Threshold */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Cosine Similarity Threshold
              </label>
              <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400">
                {settings.cosine_threshold}
              </span>
            </div>
            <input
              type="range"
              min="0.50"
              max="0.95"
              step="0.01"
              value={settings.cosine_threshold}
              onChange={(e) => setSettings({ ...settings, cosine_threshold: e.target.value })}
              className="w-full accent-brand-600 cursor-pointer"
            />
            <p className="text-[10px] text-slate-400 mt-1">
              Higher similarity = stricter match. Recommended: 0.65 - 0.75 (Default: 0.68).
            </p>
          </div>

          {/* Ambiguity Margin */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Ambiguity Margin
              </label>
              <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400">
                {settings.ambiguity_margin}
              </span>
            </div>
            <input
              type="range"
              min="0.02"
              max="0.20"
              step="0.01"
              value={settings.ambiguity_margin}
              onChange={(e) => setSettings({ ...settings, ambiguity_margin: e.target.value })}
              className="w-full accent-brand-600 cursor-pointer"
            />
            <p className="text-[10px] text-slate-400 mt-1">
              Rejects matches if top 2 candidates are within margin to prevent guessing.
            </p>
          </div>

          {/* Matching Metric Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Default Matching Metric
            </label>
            <select
              value={settings.matching_metric}
              onChange={(e) => setSettings({ ...settings, matching_metric: e.target.value })}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 focus:outline-none"
            >
              <option value="euclidean">Euclidean Distance (L2 norm)</option>
              <option value="cosine">Cosine Similarity</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={savingSettings}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-sm disabled:opacity-50 transition-all"
          >
            {savingSettings ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>Save Thresholds</span>
          </button>
        </div>
      </form>

      {/* Card 2: Administrator Password Change */}
      <form onSubmit={handlePasswordSubmit} className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-emerald-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Administrator Password & Authentication
            </h3>
          </div>
        </div>

        {passwordMsg && (
          <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>{passwordMsg}</span>
          </div>
        )}

        {passwordError && (
          <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{passwordError}</span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Current Password
            </label>
            <input
              type="password"
              value={passwordForm.old_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
              required
              className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              New Password
            </label>
            <input
              type="password"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
              required
              className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
              required
              className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={changingPassword}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 text-white text-xs font-bold shadow-sm disabled:opacity-50 transition-all"
          >
            {changingPassword ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Shield className="w-3.5 h-3.5" />}
            <span>Update Password</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default SettingsPage;

