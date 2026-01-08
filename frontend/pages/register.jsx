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
import { Keypair } from "@solana/web3.js";

export default function Register() {
  const { register, user, isAuthenticated } = useAuth();
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
  const [mounted, setMounted] = useState(false);
  
  // Only auto-generate wallet for investors and startups (not for job seekers/students)
  useEffect(() => {
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

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      const role = user.role || "student";
      if (role === "founder" || role === "startup") {
        router.push("/startup-dashboard");
      } else if (role === "investor") {
        router.push("/investor-platform");
      } else {
        router.push("/cv-builder");
      }
    }
  }, [isAuthenticated, user, router]);


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
        // Redirect based on user role
        if (formData.role === "founder" || formData.role === "startup") {
          router.push("/startup-dashboard");
        } else if (formData.role === "investor") {
          router.push("/investor-platform");
        } else {
          router.push("/cv-builder");
        }
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
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1557683316-973673baf926?w=1920&q=80')] opacity-5 bg-cover bg-center"></div>
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-float"></div>
        <div
          className="absolute bottom-0 right-0 w-96 h-96 bg-indigo-400/20 rounded-full blur-3xl animate-float"
          style={{ animationDelay: "2s" }}
        ></div>
        <div
          className="absolute top-1/2 left-1/2 w-96 h-96 bg-purple-400/20 rounded-full blur-3xl animate-float"
          style={{ animationDelay: "4s" }}
        ></div>
      </div>

      <div className="max-w-2xl w-full relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="card premium-shadow-lg"
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
              className="text-4xl font-bold text-premium-gradient mb-3"
            >
              Create Account
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="text-blue-600 font-medium"
            >
              Join TrustBridge and start your journey
            </motion.p>
          </div>


          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 w-5 h-5 z-10" />
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
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 w-5 h-5 z-10" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    className="input-field pl-10"
                    placeholder="your@email.com"
                    required
                  />
                </div>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
            >
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Password
              </label>
              <PasswordInput
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                placeholder="Create a password"
                required
                minLength={6}
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 }}
            >
              <label className="block text-sm font-bold text-blue-900 mb-2">
                I am a...
              </label>
              <select
                value={formData.role}
                onChange={(e) =>
                  setFormData({ ...formData, role: e.target.value })
                }
                className="input-field"
                required
              >
                <option value="student">Job Seeker</option>
                <option value="founder">Startup</option>
                <option value="investor">Investor</option>
              </select>
            </motion.div>

            {formData.role === "student" && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  University <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <GraduationCap className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 w-5 h-5 z-10" />
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
                <label className="block text-sm font-bold text-blue-900 mb-2">
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
              {formData.role !== "student" && (
                <p className="text-xs text-gray-500 mt-1">
                  A Solana wallet has been automatically created for you.
                </p>
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

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 1.1 }}
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
    </div>
  );
}
