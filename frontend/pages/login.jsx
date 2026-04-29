import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import Link from "next/link";
import { Wallet } from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import Logo from "../components/Logo";
import BackgroundImage from "../components/BackgroundImage";

export default function Login() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
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
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isAuthenticated && user) {
      router.push("/cv-builder");
    }
  }, [isAuthenticated, user, router]);

  const handlePrivyLogin = async () => {
    try {
      setPrivyLoading(true);
      if (privyAuth?.authenticated && privyAuth?.user) {
        toast.error("You are already signed in.");
        setPrivyLoading(false);
        return;
      }
      if (!privyAuth?.ready || !privyAuth?.login) {
        toast.error("Privy is not ready yet. Please wait a moment and try again.");
        setPrivyLoading(false);
        return;
      }
      await privyAuth.login();
    } catch (err) {
      if (err?.message?.includes('already logged in') || err?.message?.includes('already authenticated')) {
        toast.error("You are already signed in.");
      } else {
        toast.error(err?.message || "Privy login failed");
      }
    } finally {
      setPrivyLoading(false);
    }
  };

  if (!mounted) return null;

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
              Welcome Back
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="text-slate-600 font-medium"
            >
              Sign in to your TrustSpan account
            </motion.p>
          </div>

          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            type="button"
            onClick={handlePrivyLogin}
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
                <span>Sign in with Privy</span>
              </>
            )}
          </motion.button>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.9 }}
            className="mt-8 text-center"
          >
            <p className="text-blue-600">
              Don't have an account?{" "}
              <Link href="/register" className="text-blue-700 hover:text-blue-800 font-bold underline underline-offset-2 transition-colors">
                Register here
              </Link>
            </p>
          </motion.div>
        </motion.div>
      </div>
    </BackgroundImage>
  );
}
