import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Wallet } from 'lucide-react';
import Logo from '../components/Logo';
import toast from 'react-hot-toast';

const PENDING_ROLE_STORAGE_KEY = "trustspan_pending_role";

export default function Register() {
  const { isAuthenticated, user, authError, clearAuthError } = useAuth();
  const router = useRouter();
  const [role, setRole] = useState('student');
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
      router.push('/');
    }
  }, [isAuthenticated, user]);

  const handlePrivyRegister = async () => {
    setPrivyLoading(true);
    try {
      if (!privyAuth?.ready) return toast.error("Privy not ready");
      clearAuthError();
      if (typeof window !== "undefined") {
        window.localStorage.setItem(PENDING_ROLE_STORAGE_KEY, role);
      }
      await privyAuth.login();
    } catch (err) {
      toast.error(err?.message || "Registration failed");
    } finally {
      setPrivyLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md w-full bg-white p-8 rounded-3xl shadow-xl">
        <div className="text-center mb-8">
          <Logo size="large" className="mx-auto mb-6" />
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Create Account</h1>
          <p className="text-slate-600">Join TrustSpan with Privy</p>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">I want to join as a</label>
            <div className="grid grid-cols-3 gap-2">
              {['student', 'employer', 'investor'].map(r => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className={`py-2 rounded-lg text-xs font-bold border transition-all ${role === r ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 text-slate-600 border-slate-200'}`}
                >
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handlePrivyRegister}
            disabled={privyLoading}
            className="w-full flex items-center justify-center gap-3 py-4 bg-slate-900 hover:bg-black text-white rounded-xl font-bold transition-all disabled:opacity-50"
          >
            <Wallet size={20} />
            {privyLoading ? "Opening Privy..." : "Register with Privy"}
          </button>
        </div>

        <p className="mt-8 text-center text-slate-500 text-sm">
          Already have an account? <Link href="/login" className="text-blue-600 font-bold hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
