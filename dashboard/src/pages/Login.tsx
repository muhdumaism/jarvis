import React, { useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api, setAuthToken } from '../services/api';
import { ShieldAlert, KeyRound, User } from 'lucide-react';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const addToast = useJarvisStore((s) => s.addToast);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.auth.login(username, password);
      setAuthToken(res.token);
      addToast('Logged in successfully', 'success');
      window.location.hash = '/dashboard';
    } catch (err: any) {
      setError(err.message || 'Login failed');
      addToast(err.message || 'Incorrect username or password', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-bg-light dark:bg-bg-dark px-4">
      <div className="card-neo max-w-md w-full p-8 flex flex-col gap-6">
        <div className="text-center">
          <div className="inline-flex p-4 rounded-full bg-blue-500/10 dark:bg-blue-400/10 border border-blue-500/20 dark:border-blue-400/20 mb-3">
            <KeyRound className="w-8 h-8 text-blue-500" />
          </div>
          <h2 className="text-2xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
            JARVIS OS Login
          </h2>
          <p className="text-xs font-semibold text-slate-400 mt-1">
            AUTHENTICATION REQUIRED FOR SYSTEM ACCESS
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-100 rounded-lg dark:bg-red-950/40 dark:text-red-400 border border-red-200/50 dark:border-red-900/30">
            <ShieldAlert className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Username
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-400">
                <User className="w-5 h-5" />
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="input-neo pl-11"
                placeholder="admin"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-400">
                <KeyRound className="w-5 h-5" />
              </span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="input-neo pl-11"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-neo font-bold px-6 py-3.5 mt-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-xl shadow-neo-sm-light dark:shadow-neo-sm-dark hover:from-blue-600 hover:to-indigo-600 active:scale-95 transition-all text-sm uppercase tracking-wider disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Access Dashboard'}
          </button>
        </form>
      </div>
    </div>
  );
};
