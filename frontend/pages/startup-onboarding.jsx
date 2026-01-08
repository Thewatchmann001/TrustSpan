/**
 * Startup Onboarding Page
 * Complete profile creation form with business information, funding goals, and pitch deck
 */
import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../contexts/AuthContext";
import {
  Building2,
  DollarSign,
  FileText,
  Upload,
  CheckCircle,
  Loader,
} from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";

const INDUSTRIES = [
  "Technology",
  "Healthcare",
  "Agriculture",
  "Education",
  "Finance",
  "Tourism",
  "Construction",
  "Other",
];

export default function StartupOnboarding() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const [solanaAddress, setSolanaAddress] = useState(
    user?.wallet_address || ""
  );
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Basic Information
    name: "",
    sector: "",
    country: "Sierra Leone",
    year_founded: new Date().getFullYear(),

    // Business Details
    website: "",
    contact_email: "",
    phone: "",
    address: "",

    // Mission & Vision
    mission: "",
    vision: "",
    description: "",
    products_services: "",

    // Funding
    funding_goal: "",
    pitch_deck_url: "",

    // Team
    team_size: "",
    founder_experience_years: "",
  });

  const [errors, setErrors] = useState({});
  const [verificationStatus, setVerificationStatus] = useState("pending");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    // Use wallet address from user if available
    if (user?.wallet_address) {
      setSolanaAddress(user.wallet_address);
    } else {
      setSolanaAddress("");
    }
  }, [isAuthenticated, router, user]);

  const validateSolanaAddress = (address) => {
    if (!address || !address.trim()) return false;
    const addr = address.trim();
    // Basic Solana address validation: 32-44 characters, base58 encoded
    if (addr.length < 32 || addr.length > 44) return false;
    // Base58 characters (no 0, O, I, l)
    const base58Regex = /^[1-9A-HJ-NP-Za-km-z]+$/;
    return base58Regex.test(addr);
  };

  const validateStep = (step) => {
    const newErrors = {};

    if (step === 1) {
      if (!formData.name.trim()) newErrors.name = "Startup name is required";
      if (!formData.sector) newErrors.sector = "Industry sector is required";
      if (!formData.description.trim())
        newErrors.description = "Description is required";
    }

    if (step === 2) {
      if (!formData.contact_email.trim())
        newErrors.contact_email = "Email is required";
      if (!formData.phone.trim()) newErrors.phone = "Phone is required";
      if (!formData.address.trim()) newErrors.address = "Address is required";
    }

    if (step === 3) {
      if (!formData.mission.trim()) newErrors.mission = "Mission is required";
      if (!formData.vision.trim()) newErrors.vision = "Vision is required";
      if (!formData.products_services.trim())
        newErrors.products_services = "Products/Services is required";
    }

    if (step === 4) {
      if (!formData.funding_goal || parseFloat(formData.funding_goal) <= 0) {
        newErrors.funding_goal = "Valid funding goal is required";
      }
      if (!solanaAddress || !solanaAddress.trim()) {
        newErrors.solanaAddress = "Solana wallet address is required";
      } else if (!validateSolanaAddress(solanaAddress)) {
        newErrors.solanaAddress =
          "Invalid Solana wallet address format (must be 32-44 characters, base58 encoded)";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep(4)) return;

    if (!solanaAddress || !solanaAddress.trim()) {
      toast.error("Please enter your Solana wallet address");
      return;
    }

    const trimmedAddress = solanaAddress.trim();
    if (!validateSolanaAddress(trimmedAddress)) {
      toast.error("Invalid Solana wallet address format");
      return;
    }

    setLoading(true);
    try {
      // First, update user's wallet address if it's different
      if (user && user.id && trimmedAddress !== user.wallet_address) {
        try {
          const apiUrl =
            process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
          const updateResponse = await fetch(`${apiUrl}/api/users/${user.id}`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              wallet_address: trimmedAddress,
            }),
          });

          if (!updateResponse.ok) {
            const error = await updateResponse.json();
            toast.error(error.detail || "Failed to update wallet address");
            setLoading(false);
            return;
          }
        } catch (error) {
          console.error("Error updating wallet address:", error);
          // Continue with startup registration even if wallet update fails
        }
      }

      // Register startup
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/startups/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...formData,
          funding_goal: parseFloat(formData.funding_goal),
          team_size: parseInt(formData.team_size) || 1,
          founder_experience_years: parseInt(formData.founder_experience_years) || null,
          wallet_address: trimmedAddress,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.already_exists) {
          toast.success("Redirecting to your startup dashboard...");
          router.push("/startup-dashboard");
        } else {
          toast.success("Startup profile created successfully!");
          setVerificationStatus("pending");
          router.push("/startup-dashboard");
        }
      } else {
        const error = await response.json();
        // If error indicates startup already exists, redirect to dashboard
        if (
          error.detail &&
          error.detail.includes("already have a registered startup")
        ) {
          toast.info("You already have a startup. Redirecting to dashboard...");
          router.push("/startup-dashboard");
        } else {
          toast.error(error.detail || "Failed to create startup profile");
        }
      }
    } catch (error) {
      toast.error("An error occurred. Please try again.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { number: 1, title: "Basic Info", icon: Building2 },
    { number: 2, title: "Contact", icon: FileText },
    { number: 3, title: "Mission", icon: CheckCircle },
    { number: 4, title: "Funding", icon: DollarSign },
  ];

  if (!isAuthenticated) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 mb-8 shadow-xl"
        >
          <h1 className="text-4xl font-bold text-white mb-2">
            Startup Onboarding
          </h1>
          <p className="text-white/80">
            Create your startup profile and start raising funds
          </p>
        </motion.div>

        {/* Progress Steps */}
        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 mb-8">
          <div className="flex justify-between items-center">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all ${
                      currentStep >= step.number
                        ? "bg-blue-500 border-blue-500 text-white"
                        : "bg-white/10 border-white/20 text-white/60"
                    }`}
                  >
                    {currentStep > step.number ? (
                      <CheckCircle className="w-6 h-6" />
                    ) : (
                      <step.icon className="w-6 h-6" />
                    )}
                  </div>
                  <span className="mt-2 text-sm text-white/80">
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-4 ${
                      currentStep > step.number ? "bg-blue-500" : "bg-white/20"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Form Content */}
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 shadow-xl"
        >
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white mb-6">
                Basic Information
              </h2>

              <div>
                <label className="block text-white/80 mb-2">
                  Startup Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter your startup name"
                />
                {errors.name && (
                  <p className="text-red-400 text-sm mt-1">{errors.name}</p>
                )}
              </div>

              <div>
                <label className="block text-white/80 mb-2">
                  Industry Sector *
                </label>
                <select
                  value={formData.sector}
                  onChange={(e) =>
                    setFormData({ ...formData, sector: e.target.value })
                  }
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  <option value="" className="bg-gray-900">
                    Select industry
                  </option>
                  {INDUSTRIES.map((industry) => (
                    <option
                      key={industry}
                      value={industry}
                      className="bg-gray-900"
                    >
                      {industry}
                    </option>
                  ))}
                </select>
                {errors.sector && (
                  <p className="text-red-400 text-sm mt-1">{errors.sector}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-white/80 mb-2">Country</label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) =>
                      setFormData({ ...formData, country: e.target.value })
                    }
                    className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-white/80 mb-2">
                    Year Founded
                  </label>
                  <input
                    type="number"
                    value={formData.year_founded}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        year_founded: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-white/80 mb-2">
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows={5}
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Describe your startup..."
                />
                {errors.description && (
                  <p className="text-red-400 text-sm mt-1">
                    {errors.description}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Contact Information */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white mb-6">
                Contact Information
              </h2>

              <div>
                <label className="block text-white/80 mb-2">
                  Contact Email *
                </label>
                <input
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) =>
                    setFormData({ ...formData, contact_email: e.target.value })
                  }
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="contact@startup.com"
                />
                {errors.contact_email && (
                  <p className="text-red-400 text-sm mt-1">
                    {errors.contact_email}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-white/80 mb-2">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="+232 76 123 456"
                />
                {errors.phone && (
                  <p className="text-red-400 text-sm mt-1">{errors.phone}</p>
                )}
              </div>

              <div>
                <label className="block text-white/80 mb-2">Website</label>
                <input
                  type="url"
                  value={formData.website}
                  onChange={(e) =>
                    setFormData({ ...formData, website: e.target.value })
                  }
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="https://yourstartup.com"
                />
              </div>

              <div>
                <label className="block text-white/80 mb-2">Address *</label>
                <textarea
                  value={formData.address}
                  onChange={(e) =>
                    setFormData({ ...formData, address: e.target.value })
                  }
                  rows={3}
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Street address, City, Country"
                />
                {errors.address && (
                  <p className="text-red-400 text-sm mt-1">{errors.address}</p>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Mission & Vision */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white mb-6">
                Mission & Vision
              </h2>

              <div>
                <label className="block text-white/80 mb-2">
                  Mission Statement *
                </label>
                <textarea
                  value={formData.mission}
                  onChange={(e) =>
                    setFormData({ ...formData, mission: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="What is your startup's mission?"
                />
                {errors.mission && (
                  <p className="text-red-400 text-sm mt-1">{errors.mission}</p>
                )}
              </div>

              <div>
                <label className="block text-white/80 mb-2">
                  Vision Statement *
                </label>
                <textarea
                  value={formData.vision}
                  onChange={(e) =>
                    setFormData({ ...formData, vision: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="What is your startup's vision for the future?"
                />
                {errors.vision && (
                  <p className="text-red-400 text-sm mt-1">{errors.vision}</p>
                )}
              </div>

              <div>
                <label className="block text-white/80 mb-2">
                  Products & Services *
                </label>
                <textarea
                  value={formData.products_services}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      products_services: e.target.value,
                    })
                  }
                  rows={5}
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Describe your products and services..."
                />
                {errors.products_services && (
                  <p className="text-red-400 text-sm mt-1">
                    {errors.products_services}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-white/80 mb-2">Team Size</label>
                  <input
                    type="number"
                    value={formData.team_size}
                    onChange={(e) =>
                      setFormData({ ...formData, team_size: e.target.value })
                    }
                    className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="Number of team members"
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-white/80 mb-2">Founder Experience (Years)</label>
                  <input
                    type="number"
                    value={formData.founder_experience_years}
                    onChange={(e) =>
                      setFormData({ ...formData, founder_experience_years: e.target.value })
                    }
                    className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="Years of industry experience"
                    min="0"
                    max="50"
                  />
                  <p className="text-xs text-white/60 mt-1">Your years of experience in this industry</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Funding */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white mb-6">
                Funding Information
              </h2>

              <div>
                <label className="block text-white/80 mb-2">
                  Funding Goal (USDC) *
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/60 w-5 h-5" />
                  <input
                    type="number"
                    value={formData.funding_goal}
                    onChange={(e) =>
                      setFormData({ ...formData, funding_goal: e.target.value })
                    }
                    className="w-full pl-12 pr-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="500000"
                    min="0"
                    step="1000"
                  />
                </div>
                {errors.funding_goal && (
                  <p className="text-red-400 text-sm mt-1">
                    {errors.funding_goal}
                  </p>
                )}
                <p className="text-white/60 text-sm mt-2">
                  This is the total amount you're seeking to raise
                </p>
              </div>

              <div>
                <label className="block text-white/80 mb-2">
                  Pitch Deck URL
                </label>
                <div className="relative">
                  <Upload className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/60 w-5 h-5" />
                  <input
                    type="url"
                    value={formData.pitch_deck_url}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        pitch_deck_url: e.target.value,
                      })
                    }
                    className="w-full pl-12 pr-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="https://yourstartup.com/pitch-deck.pdf"
                  />
                </div>
                <p className="text-white/60 text-sm mt-2">
                  Link to your pitch deck (PDF, Google Slides, etc.)
                </p>
              </div>

              {/* Solana Wallet Address */}
              <div>
                <label className="block text-white/80 mb-2">
                  Solana Wallet Address *
                </label>
                <input
                  type="text"
                  value={solanaAddress || ""}
                  onChange={(e) => setSolanaAddress(e.target.value)}
                  className="w-full px-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400 font-mono text-sm"
                  placeholder="Enter your Solana wallet address (32-44 characters)"
                />
                {errors.solanaAddress && (
                  <p className="text-red-400 text-sm mt-1">
                    {errors.solanaAddress}
                  </p>
                )}
                <p className="text-white/60 text-xs mt-2">
                  Your Solana wallet address will be used for blockchain
                  transactions.
                  {user?.wallet_address && (
                    <span className="block mt-1">
                      Current profile address:{" "}
                      <span className="font-mono text-xs">
                        {user.wallet_address}
                      </span>
                    </span>
                  )}
                </p>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            <button
              onClick={handleBack}
              disabled={currentStep === 1}
              className="px-6 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-all"
            >
              Back
            </button>

            {currentStep < 4 ? (
              <button
                onClick={handleNext}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-all font-semibold"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit & Register"
                )}
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
