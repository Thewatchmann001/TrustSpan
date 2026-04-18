import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { LogIn, Mail, ArrowLeft, Wallet } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import Logo from '../components/Logo';
import PasswordInput from '../components/PasswordInput';
import BackgroundImage from '../components/BackgroundImage';
import { authAPI } from '../utils/api';

const PRIVY_ENABLED =
  typeof process.env.NEXT_PUBLIC_PRIVY_APP_ID === "string" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID.trim() !== "" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID !== "your-privy-app-id";

const PENDING_ROLE_STORAGE_KEY = "trustspan_pending_role";

export default function Login() {
  const { login, user, isAuthenticated, authError, syncFailed, clearAuthError } = useAuth();
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    role: 'student', // Role selection for role-based login
  });
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);
  const [privyLoading, setPrivyLoading] = useState(false);
  
  // Clear stale auth errors when component mounts and user is not authenticated
  useEffect(() => {
    if (!isAuthenticated && !user && (authError || syncFailed)) {
      console.log('🧹 Clearing stale auth errors on login page mount');
      if (clearAuthError) clearAuthError();
      // Note: syncFailed is managed by AuthContext and should be cleared on logout
      // But we can't directly clear it here, so we rely on the logout function
    }
  }, [isAuthenticated, user, authError, syncFailed, clearAuthError]);

  // Privy auth (optional)
  const getPrivyAuth = () => {
    try {
      // eslint-disable-next-line global-require
      const { usePrivyAuth } = require("../contexts/PrivyAuthContext");
      return usePrivyAuth();
    } catch (e) {
      return null;
    }
  };
  const privyAuth = getPrivyAuth();

  // Check for OAuth errors in URL
  useEffect(() => {
    const { error } = router.query;
    if (error) {
      toast.error(`OAuth sign-in failed: ${error}`);
      // Clear error from URL
      router.replace('/login', undefined, { shallow: true });
    }
  }, [router.query, router]);

  // Check for role mismatch message from sessionStorage (set during auto-logout)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedMessage = sessionStorage.getItem('trustspan_role_mismatch_message');
      if (storedMessage) {
        try {
          // Parse the stored message (it's now a JSON object)
          const messageData = JSON.parse(storedMessage);
          
          // Show a prominent toast with clear instructions
          const toastMessage = messageData.registeredRole
            ? `⚠️ This email is registered as ${messageData.registeredRole}. Please select "${messageData.registeredRole}" from the role dropdown below.`
            : (messageData.message || 'Role mismatch detected. Please select the correct role.');
          
          toast.error(toastMessage, {
            duration: 8000, // Show for 8 seconds (longer for important messages)
            icon: '⚠️',
            style: {
              background: '#FEF2F2',
              color: '#991B1B',
              border: '1px solid #FCA5A5',
              padding: '16px',
              fontSize: '14px',
              maxWidth: '500px',
              fontWeight: '500',
            },
          });
          
          // Auto-focus on role dropdown after a short delay
          if (messageData.registeredRole) {
            setTimeout(() => {
              const roleSelect = document.querySelector('select[name="role"], #role-select, select[value]');
              if (roleSelect) {
                roleSelect.focus();
                roleSelect.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }
            }, 500);
          }
          
          // Auto-select the correct role in the dropdown if available
          if (messageData.correctRole && formData.role !== messageData.correctRole) {
            setTimeout(() => {
              setFormData(prev => ({ ...prev, role: messageData.correctRole }));
              console.log(`✅ Auto-selected correct role: ${messageData.correctRole}`);
            }, 100);
          }
          
          // Clear the message after displaying once
          sessionStorage.removeItem('trustspan_role_mismatch_message');
          console.log('📢 Displayed role mismatch toast and cleared from sessionStorage');
        } catch (e) {
          // Fallback for old string format (backward compatibility)
          toast.error(storedMessage, {
            duration: 6000,
            icon: '⚠️',
          });
          sessionStorage.removeItem('trustspan_role_mismatch_message');
        }
      }
    }
  }, []); // Run once on mount

  // Redirect if already authenticated - BUT ONLY if no auth error exists
  useEffect(() => {
    // GUARD: Do not redirect if there's an auth error (role mismatch)
    if (authError || syncFailed) {
      console.log('⏸️ Auth error exists, preventing redirect');
      return;
    }
    
    if (isAuthenticated && user) {
      console.log('✅ User authenticated, redirecting...', { role: user.role, userId: user.id });
      const role = user.role || 'student';
      let redirectPath = '/cv-builder';
      
      if (role === 'founder' || role === 'startup') {
        redirectPath = '/cv-builder';
      } else if (role === 'investor') {
        redirectPath = '/cv-builder';
      }
      
      console.log('🚀 Redirecting to:', redirectPath);
      router.push(redirectPath);
    }
  }, [isAuthenticated, user, router, authError, syncFailed]);

  // No polling needed - AuthContext handles sync automatically


  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Role-based login: pass role to backend
    const result = await login(formData.email, formData.password, formData.role);
    
    if (result.success) {
      toast.success('Login successful!');
      // Redirect based on user role
      const role = result.user?.role || 'student';
      if (role === 'founder' || role === 'startup') {
        router.push('/cv-builder');
      } else if (role === 'investor') {
        router.push('/cv-builder');
      } else {
        router.push('/cv-builder');
      }
    } else {
      toast.error(result.error || 'Login failed');
    }
    
    setLoading(false);
  };

  const handlePrivyLogin = async () => {
    try {
      setPrivyLoading(true);
      
      // GUARD 1: Check for fatal auth error - but only if user is still authenticated
      // If user is not authenticated, clear the error and allow login
      if ((syncFailed || authError) && privyAuth?.authenticated) {
        toast.error("Authentication failed. Please logout and try again with the correct role.");
        setPrivyLoading(false);
        return;
      }
      
      // If user is not authenticated, clear any stale error flags
      if (!privyAuth?.authenticated && (syncFailed || authError)) {
        console.log('🧹 Clearing stale auth error flags - user is not authenticated');
        if (clearAuthError) clearAuthError();
        // Note: syncFailed is managed by AuthContext, it should be cleared on logout
      }
      
      // GUARD 2: Never call login() if already authenticated
      if (privyAuth?.authenticated && privyAuth?.user && isAuthenticated) {
        // User is authenticated but trying to switch roles - force logout first
        toast.error("You are already signed in. Please logout first to switch roles.");
        setPrivyLoading(false);
        return;
      }
      
      // GUARD 3: Ensure Privy is ready before attempting login
      if (!privyAuth?.ready) {
        toast.error("Privy is not ready yet. Please wait a moment and try again.");
        setPrivyLoading(false);
        return;
      }
      
      // GUARD 4: Ensure login function exists
      if (!privyAuth?.login) {
        throw new Error("Privy login is not available. Check NEXT_PUBLIC_PRIVY_APP_ID / CLIENT_ID.");
      }
      
      // Clear any previous errors
      clearAuthError();
      
      // Store selected role so Privy sync can apply it
      // Note: Backend will enforce role matching - existing user's role is authoritative
      if (typeof window !== "undefined") {
        window.localStorage.setItem(PENDING_ROLE_STORAGE_KEY, formData.role);
        console.log('💾 Stored pending role:', formData.role);
      }
      
      console.log('🔐 Calling Privy login...');
      await privyAuth.login();
      toast.success("Privy login opened. Complete the flow to continue.");
      // Backend sync happens inside AuthContext once Privy authenticates.
    } catch (err) {
      console.error('❌ Privy login error:', err);
      // If error is "already logged in", that's actually fine - sync will happen automatically
      if (err?.message?.includes('already logged in') || err?.message?.includes('already authenticated')) {
        console.log('ℹ️ User already logged in with Privy, sync will happen automatically');
        toast.success("Already signed in! Syncing account...");
      } else {
        toast.error(err?.message || "Privy login failed");
      }
    } finally {
      setPrivyLoading(false);
    }
  };

  return (
    <BackgroundImage
      src="/images/backgrounds/hero/auth-background.jpg"
      alt="Professional team - TrustSpan"
      overlay="auth"
      className="min-h-screen flex items-center justify-center p-6"
    >

      <div className="max-w-md w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="card-premium"
        >
          {/* Back Button */}
          <button
            onClick={() => router.back()}
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-4 -mt-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back</span>
          </button>
          {/* Logo */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="flex justify-center mb-6"
            >
              <Logo size="large" />
            </motion.div>
            
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="text-4xl font-bold text-slate-900 mb-3"
            >
              Welcome Back to TrustSpan
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="text-slate-600 font-medium"
            >
              Sign in to continue your journey
            </motion.p>
          </div>

          {/* Backend Role Error Display */}
          {authError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-4 bg-red-50 border-2 border-red-200 rounded-lg"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-red-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-bold text-red-900 mb-1">Role Mismatch</h4>
                  <p className="text-sm text-red-800">{authError}</p>
                  <p className="text-xs text-red-700 mt-2">
                    You have been automatically logged out. Please select the correct role above and try again.
                  </p>
                </div>
                <button
                  onClick={clearAuthError}
                  className="flex-shrink-0 text-red-600 hover:text-red-800"
                  aria-label="Dismiss error"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </motion.div>
          )}

          {/* Role selection - HIDDEN: Only Job Seeker allowed for now */}
          <input type="hidden" name="role" value="student" />

          {/* Email/password login – only visible when Privy is NOT enabled */}
          {!PRIVY_ENABLED && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5 z-10" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="input-field pl-10"
                    placeholder="your@email.com"
                    required
                  />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
              >
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Password
                </label>
                <PasswordInput
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Enter your password"
                  showStrengthMeter={false}
                />
              </motion.div>

              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.7 }}
                type="submit"
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2 group"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <LogIn className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    <span>Sign In</span>
                  </>
                )}
              </motion.button>
            </form>
          )}

          {/* Privy login (canonical when enabled) */}
          {PRIVY_ENABLED && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.73 }}
              type="button"
              onClick={handlePrivyLogin}
              disabled={privyLoading}
              className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-3 border-2 border-slate-300 rounded-lg hover:border-slate-400 hover:bg-slate-50 transition-all duration-200 font-semibold text-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {privyLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-slate-800"></div>
                  <span>Opening Privy...</span>
                </>
              ) : (
                <>
                  <Wallet className="w-5 h-5" />
                  <span>Continue with Privy</span>
                </>
              )}
            </motion.button>
          )}

          {/* Divider */}
          {/* Legacy OAuth (only when Privy is not enabled) */}
          {!PRIVY_ENABLED && (
            <>
            </>
          )}

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.85 }}
            className="mt-8 text-center"
          >
            <p className="text-slate-600">
              Don't have an account?{' '}
              <Link href="/register" className="text-amber-600 hover:text-amber-700 font-bold underline underline-offset-2 transition-colors">
                Sign up
              </Link>
            </p>
          </motion.div>
        </motion.div>
      </div>
    </BackgroundImage>
  );
}
