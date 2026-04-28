import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import Link from "next/link";
import {
  UserPlus,
  Mail,
  User,
  Wallet,
  Building2,
  GraduationCap,
} from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import Logo from "../components/Logo";
import PasswordInput from "../components/PasswordInput";
import BackgroundImage from "../components/BackgroundImage";
import { Keypair } from "@solana/web3.js";
import { authAPI } from "../utils/api";

const PRIVY_ENABLED =
  typeof process.env.NEXT_PUBLIC_PRIVY_APP_ID === "string" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID.trim() !== "" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID !== "your-privy-app-id";

const PENDING_ROLE_STORAGE_KEY = "trustspan_pending_role";

export default function Register() {
  const { register, user, isAuthenticated, authError, syncFailed, clearAuthError } = useAuth();
  const router = useRouter();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "student",
    wallet_address: "",
    university: "",
    company_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [privyLoading, setPrivyLoading] = useState(false);
  
  // Clear stale auth errors when component mounts and user is not authenticated
  useEffect(() => {
    if (!isAuthenticated && !user && (authError || syncFailed)) {
      console.log('🧹 Clearing stale auth errors on register page mount');
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
  
  // Only auto-generate wallet for investors and startups (not for job seekers/students)
  useEffect(() => {
    // If Privy is enabled, DO NOT generate random wallets (keys would be lost).
    if (PRIVY_ENABLED) return;

    if (!formData.wallet_address && mounted && (formData.role === 'investor' || formData.role === 'startup' || formData.role === 'founder')) {
      try {
        const keypair = Keypair.generate();
        const walletAddress = keypair.publicKey.toBase58();
        setFormData(prev => ({ ...prev, wallet_address: walletAddress }));
        console.log("✅ Auto-generated Solana wallet:", walletAddress);
      } catch (error) {
        console.error("Failed to generate wallet:", error);
      }
    }
  }, [mounted, formData.role]);

  // Fix hydration mismatch - only show dynamic content after mount
  useEffect(() => {
    setMounted(true);
  }, []);

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
      router.push("/cv-builder");
    }
  }, [isAuthenticated, user, router, authError, syncFailed]);


  const handlePrivyRegister = async () => {
    try {
      setPrivyLoading(true);
      
      // GUARD 1: Check for fatal auth error - but only if user is still authenticated
      // If user is not authenticated, clear the error and allow registration
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
      if (privyAuth?.authenticated && privyAuth?.user) {
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
      
      if (typeof window !== "undefined") {
        window.localStorage.setItem(PENDING_ROLE_STORAGE_KEY, formData.role);
      }
      await privyAuth.login();
      toast.success("Privy sign-up/login started. Complete the Privy flow.");
    } catch (err) {
      console.error('❌ Privy registration error:', err);
      // If error is "already logged in", that's actually fine
      if (err?.message?.includes('already logged in') || err?.message?.includes('already authenticated')) {
        toast.error("You are already signed in. Please logout first.");
      } else {
        toast.error(err?.message || "Privy registration failed");
      }
    } finally {
      setPrivyLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Convert empty wallet_address to null to avoid unique constraint violations
      const submitData = {
        ...formData,
        wallet_address: formData.wallet_address?.trim() || null,
      };

      console.log('📝 Submitting registration...', { email: submitData.email, role: submitData.role });
      const result = await register(submitData);
      
      console.log('📬 Registration result:', result);
      
      if (result.success) {
        toast.success("Registration successful!");
        router.push("/cv-builder");
      } else {
        const errorMsg = result.error || "Registration failed";
        console.error('❌ Registration failed:', errorMsg);
        toast.error(errorMsg);
        setLoading(false);
      }
    } catch (error) {
      console.error('❌ Unexpected error during registration:', error);
      toast.error(`Registration failed: ${error.message || 'Unknown error'}`);
      setLoading(false);
    }
  };

  return (
    <BackgroundImage
      src="/images/backgrounds/hero/auth-background.jpg"
      alt="Professional team - TrustSpan"
      overlay="auth"
      className="min-h-screen flex items-center justify-center p-6"
    >
      <div className="max-w-2xl w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="card-premium"
        >
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
              Join TrustSpan
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="text-slate-600 font-medium"
            >
              Build Your Career, Build Your Future
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

          {/* Traditional registration form – only when Privy is NOT enabled */}
          {!PRIVY_ENABLED && (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5 z-10" />
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) =>
                      setFormData({ ...formData, full_name: e.target.value })
                    }
                    className="input-field pl-10"
                    placeholder="John Doe"
                    required
                  />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
              >
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5 z-10" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => {
                      const email = e.target.value;
                      setFormData({ ...formData, email });
                      // Real-time email validation
                      if (email) {
                        const { validateEmail } = require('../lib/validation');
                        const validation = validateEmail(email, true);
                        if (!validation.isValid) {
                          // Show inline error (you can enhance this with state)
                          console.log('Email validation:', validation.error);
                        }
                      }
                    }}
                    className="input-field pl-10"
                    placeholder="your@email.com"
                    required
                    pattern="[^\s@]+@[^\s@]+\.[^\s@]+"
                    title="Enter a valid email address"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  We'll never share your email with anyone
                </p>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
            >
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Password
                <span className="text-xs font-normal text-gray-600 ml-2">
                  (Min 8 chars, uppercase, lowercase, number, special char)
                </span>
              </label>
              <PasswordInput
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                placeholder="Create a strong password"
                required
                minLength={8}
                showStrengthMeter={true}
              />
            </motion.div>

            {formData.role === "student" && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  University <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <GraduationCap className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5 z-10" />
                  <select
                    value={formData.university}
                    onChange={(e) =>
                      setFormData({ ...formData, university: e.target.value })
                    }
                    className="input-field pl-10"
                    required
                  >
                    <option value="">Select your university</option>
                    <option value="Fourah Bay College, University of Sierra Leone">
                      Fourah Bay College, University of Sierra Leone
                    </option>
                    <option value="Njala University">Njala University</option>
                    <option value="College of Medicine and Allied Health Sciences">
                      College of Medicine and Allied Health Sciences
                    </option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </motion.div>
            )}

            {formData.role === "founder" && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Company Name <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 w-5 h-5 z-10" />
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) =>
                      setFormData({ ...formData, company_name: e.target.value })
                    }
                    className="input-field pl-10"
                    placeholder={
                      formData.role === "founder"
                        ? "Your startup name"
                        : "Your company name"
                    }
                    required
                  />
                </div>
                <p className="text-xs text-blue-600 mt-1 font-medium">
                  {formData.role === "founder"
                    ? "This will be your startup name on the platform"
                    : "This will be your company name on the platform"}
                </p>
              </motion.div>
            )}

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.9 }}
            >
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Solana Wallet Address{" "}
                {formData.role !== "student" && (
                  <span className="text-xs font-normal text-green-600">
                    (Auto-generated)
                  </span>
                )}
              </label>
              <div className="relative">
                <Wallet className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 w-5 h-5 z-10" />
                <input
                  type="text"
                  value={formData.wallet_address}
                  readOnly={formData.role !== "student"}
                  onChange={(e) => {
                    if (formData.role === "student") {
                      setFormData({ ...formData, wallet_address: e.target.value });
                    }
                  }}
                  className={`input-field pl-10 ${
                    formData.role !== "student" 
                      ? "bg-gray-50 text-gray-700 cursor-not-allowed" 
                      : ""
                  }`}
                  placeholder={
                    formData.role === "student"
                      ? "Optional: Enter wallet address or leave empty"
                      : formData.wallet_address
                      ? ""
                      : "Generating wallet..."
                  }
                />
              </div>
              {formData.role !== "student" && formData.wallet_address && (
                <div className="mt-2">
                  <p className="text-xs text-gray-500 mb-1">
                    A Solana wallet has been automatically created for you.
                  </p>
                  <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded p-2">
                    ℹ️ <strong>Note:</strong> This is a valid Solana wallet address. The account will appear on Solana Explorer after it receives its first transaction. You can use this address to receive USDC investments.
                  </p>
                </div>
              )}
              <p className="text-xs text-blue-600 mt-1 font-medium">
                {formData.role === "founder" || formData.role === "investor"
                  ? "Required for founders and investors"
                  : "Optional for job seekers - you can leave this empty"}
              </p>
            </motion.div>

            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 1.0 }}
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 group mt-6"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Creating account...</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span>Create Account</span>
                </>
              )}
            </motion.button>
          </form>
          )}

          {/* Privy-only registration when enabled */}
          {PRIVY_ENABLED && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
              type="button"
              onClick={handlePrivyRegister}
              disabled={privyLoading}
              className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 border-2 border-slate-300 rounded-lg hover:border-slate-400 hover:bg-slate-50 transition-all duration-200 font-semibold text-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
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

          {/* Google OAuth Button - REMOVED: Privy handles Google authentication internally */}
          {/* 
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 1.1 }}
            type="button"
            onClick={() => {
              setOauthLoading(true);
              // Redirect to Google OAuth with selected role
              const oauthUrl = authAPI.initiateGoogleOAuth(formData.role);
              window.location.href = oauthUrl;
            }}
            disabled={oauthLoading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 border-2 border-gray-300 rounded-lg hover:border-gray-400 hover:bg-gray-50 transition-all duration-200 font-medium text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {oauthLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600"></div>
                <span>Redirecting to Google...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                <span>Continue with Google</span>
              </>
            )}
          </motion.button>
          */}

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 1.15 }}
            className="mt-8 text-center"
          >
            <p className="text-blue-600">
              Already have an account?{" "}
              <Link
                href="/login"
                className="text-blue-700 hover:text-blue-800 font-bold underline underline-offset-2 transition-colors"
              >
                Sign in
              </Link>
            </p>
          </motion.div>
        </motion.div>
      </div>
    </BackgroundImage>
  );
}
