import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { ArrowLeft, Wallet } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import Logo from '../components/Logo';
import BackgroundImage from '../components/BackgroundImage';

const PENDING_ROLE_STORAGE_KEY = "trustspan_pending_role";

export default function Login() {
  const { user, isAuthenticated, authError, syncFailed, clearAuthError } = useAuth();
  const router = useRouter();
  const [formData, setFormData] = useState({ role: 'student' });
  const [privyLoading, setPrivyLoading] = useState(false);
  
  const getPrivyAuth = () => {
    try {
      const { usePrivyAuth } = require("../contexts/PrivyAuthContext");
      return usePrivyAuth();
    } catch (e) {
      return null;
    }
  };

  const privyAuth = getPrivyAuth();

  useEffect(() => {
    if (isAuthenticated && user) {
      const path = user.role === 'admin' ? '/admin-dashboard' :
                   user.active_role === 'employer' ? '/employer-dashboard' : '/cv-builder';
      router.push(path);
    }
  }, [isAuthenticated, user]);

  const handlePrivyLogin = async () => {
    setPrivyLoading(true);
    try {
      if (!privyAuth?.ready) {
        toast.error("Privy is not ready yet.");
        return;
      }
      clearAuthError();
      if (typeof window !== "undefined") {
        window.localStorage.setItem(PENDING_ROLE_STORAGE_KEY, formData.role);
      }
      await privyAuth.login();
    } catch (err) {
      toast.error(err?.message || "Login failed");
    } finally {
      setPrivyLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md w-full bg-white p-8 rounded-3xl shadow-xl">
        <div className="text-center mb-8">
          <Logo size="large" className="mx-auto mb-6" />
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Welcome Back</h1>
          <p className="text-slate-600">Sign in with Privy to continue</p>
        </div>

        {authError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {authError}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Select your role</label>
            <select
              value={formData.role}
              onChange={e => setFormData({role: e.target.value})}
              className="w-full p-3 border rounded-xl bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="student">Job Seeker</option>
              <option value="employer">Employer</option>
              <option value="investor">Investor</option>
            </select>
          </div>

          <button
            onClick={handlePrivyLogin}
            disabled={privyLoading}
            className="w-full flex items-center justify-center gap-3 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-all disabled:opacity-50"
          >
            <Wallet size={20} />
            {privyLoading ? "Opening Privy..." : "Continue with Privy"}
          </button>
        </div>

        <p className="mt-8 text-center text-slate-500 text-sm">
          Don't have an account? <Link href="/register" className="text-blue-600 font-bold hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
