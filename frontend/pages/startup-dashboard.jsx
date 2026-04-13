/**
 * Startup Dashboard
 * Shows verification status, funding progress, and startup management
 */
import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../contexts/AuthContext";
import Chat from "../components/Chat";
import CredibilityImprovement from "../investor/CredibilityImprovement";
import AttestationStatus from "../components/attestation/AttestationStatus";
import VerificationFlow from "../components/attestation/VerificationFlow";
import {
  Shield,
  TrendingUp,
  DollarSign,
  Users,
  CheckCircle,
  Clock,
  XCircle,
  FileText,
  Edit,
  MessageSquare,
  ArrowLeft,
  Target,
  ExternalLink,
} from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import BackgroundImage from "../components/BackgroundImage";

export default function StartupDashboard() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const solanaAddress = user?.wallet_address || null;
  const [startup, setStartup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fundingProgress, setFundingProgress] = useState(0);
  const [activeTab, setActiveTab] = useState("overview");
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversationsLoading, setConversationsLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (user?.id) {
    fetchStartupData();
    }
  }, [isAuthenticated, user?.id]); // Removed router from deps, added user?.id

  const fetchStartupData = async () => {
    if (!user?.id) return; // Guard clause
    
    try {
      setLoading(true);
      // Fetch startup by founder/user ID
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/startups/by-founder/${user.id}`,
      );
      if (response.ok) {
        const data = await response.json();
        setStartup(data);

        // Calculate funding progress
        if (data.funding_goal && data.total_investments) {
          const progress = (data.total_investments / data.funding_goal) * 100;
          setFundingProgress(Math.min(100, progress));
        }
      } else if (response.status === 404) {
        // No startup found - redirect to onboarding
        console.log("No startup found, redirecting to onboarding...");
        router.push("/startup-onboarding");
        return;
      }
    } catch (error) {
      toast.error("Failed to load startup data");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConversations = async () => {
    try {
      setConversationsLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/conversations/user/${user?.id}`,
      );

      if (response.ok) {
        const data = await response.json();
        setConversations(data || []);
      }
    } catch (error) {
      console.error("Error loading conversations:", error);
      toast.error("Failed to load messages");
    } finally {
      setConversationsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "messages" && user?.id) {
      fetchConversations();
    }
  }, [activeTab, user?.id]);

  const getVerificationStatus = () => {
    if (!startup)
      return {
        status: "pending",
        label: "Pending",
        icon: Clock,
        color: "yellow",
      };

    if (startup.transaction_signature) {
      return {
        status: "verified",
        label: "Verified",
        icon: CheckCircle,
        color: "green",
      };
    }
    return {
      status: "pending",
      label: "Pending Verification",
      icon: Clock,
      color: "yellow",
    };
  };

  if (!isAuthenticated || loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
      </div>
    );
  }

  if (!startup) {
    return null; // Will redirect to onboarding
  }

  const verification = getVerificationStatus();
  const StatusIcon = verification.icon;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header Section with Background */}
      <BackgroundImage
        src="/images/backgrounds/hero/startup-dashboard-hero.jpg"
        alt="Startup Dashboard - TrustSpan"
        overlay="default"
        className="h-64 flex-shrink-0"
        priority={true}
      >
        <div className="max-w-7xl mx-auto px-6 py-12 h-full flex items-end">
          <div className="w-full flex justify-between items-end">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">
                {startup.name}
              </h1>
              <p className="text-xl text-white font-semibold mb-2">
                {startup.sector} • {startup.country}
              </p>
              <p className="text-white text-sm font-mono font-semibold">
                ID: {startup.startup_id || "N/A"}
              </p>
            </div>
            <button
              onClick={() => router.push("/startup-onboarding")}
              className="btn-secondary text-white border-white/30 hover:border-white/50 hover:bg-white/10"
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit Profile
            </button>
          </div>
        </div>
      </BackgroundImage>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-4 mb-8 border-b border-slate-200">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 flex items-center gap-2 transition-colors ${
              activeTab === "overview"
                ? "text-amber-600 border-b-2 border-amber-600 font-semibold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab("improve")}
            className={`px-4 py-2 flex items-center gap-2 transition-colors ${
              activeTab === "improve"
                ? "text-amber-600 border-b-2 border-amber-600 font-semibold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Target className="w-4 h-4" />
            Improve Credibility
          </button>
          <button
            onClick={() => setActiveTab("verification")}
            className={`px-4 py-2 flex items-center gap-2 transition-colors ${
              activeTab === "verification"
                ? "text-amber-600 border-b-2 border-amber-600 font-semibold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Shield className="w-4 h-4" />
            Verification
          </button>
          <button
            onClick={() => setActiveTab("messages")}
            className={`px-4 py-2 flex items-center gap-2 transition-colors ${
              activeTab === "messages"
                ? "text-amber-600 border-b-2 border-amber-600 font-semibold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Messages
          </button>
        </div>

        {/* Improve Credibility Tab */}
        {activeTab === "improve" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <CredibilityImprovement
              startup={startup}
              onUpdate={fetchStartupData}
            />
          </motion.div>
        )}

        {/* Verification Tab */}
        {activeTab === "verification" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            {/* Existing Attestations */}
            {user?.id && (
              <AttestationStatus
                userId={user.id}
                walletAddress={solanaAddress}
                onUpdate={fetchStartupData}
              />
            )}

            {/* Request New Verification */}
            {user && (
              <VerificationFlow
                user={user}
                onComplete={() => {
                  // Refresh startup data and attestations after verification
                  fetchStartupData();
                }}
              />
            )}
          </motion.div>
        )}

        {/* Messages Tab */}
        {activeTab === "messages" && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
            {/* Conversations List */}
            <div className="lg:col-span-1 card overflow-hidden">
              <div className="p-4 border-b border-slate-200">
                <h3 className="text-lg font-bold text-slate-900">
                  Conversations
                </h3>
              </div>
              {conversationsLoading ? (
                <div className="p-4 text-center text-slate-600">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-amber-600 mx-auto"></div>
                </div>
              ) : conversations.length === 0 ? (
                <div className="p-4 text-center text-slate-600">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                  <p className="text-sm">No conversations yet</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                  {conversations.map((conversation) => (
                    <button
                      key={conversation.id}
                      onClick={() => setSelectedConversation(conversation)}
                      className={`w-full p-4 text-left transition ${
                        selectedConversation?.id === conversation.id
                          ? "bg-amber-50 border-l-2 border-amber-600"
                          : "hover:bg-slate-50"
                      }`}
                    >
                      <div className="text-sm font-medium text-slate-900 truncate">
                        {conversation.investor_id === user?.id
                          ? conversation.startup_name
                          : conversation.investor_name}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {conversation.last_message_preview}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Chat View */}
            <div
              className="lg:col-span-3 card overflow-hidden flex flex-col"
              style={{ height: "600px" }}
            >
              {selectedConversation ? (
                <>
                  <div className="p-4 border-b border-slate-200 flex items-center gap-2">
                    <button
                      onClick={() => setSelectedConversation(null)}
                      className="text-slate-600 hover:text-slate-900 transition-colors"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <h3 className="text-lg font-bold text-slate-900">
                      {selectedConversation.investor_id === user?.id
                        ? selectedConversation.startup_name
                        : selectedConversation.investor_name}
                    </h3>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <Chat
                      investorId={selectedConversation.investor_id}
                      startupId={selectedConversation.startup_id}
                      currentUserId={user?.id}
                      onClose={() => setSelectedConversation(null)}
                    />
                  </div>
                </>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-600">
                  <div className="text-center">
                    <MessageSquare className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                    <p>Select a conversation to view messages</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Verification Status */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="card"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-slate-900">
                    Verification Status
                  </h2>
                  <StatusIcon
                    className={`w-6 h-6 ${
                      verification.color === "green"
                        ? "text-sky-600"
                        : "text-amber-600"
                    }`}
                  />
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">
                      On-Chain Verification
                    </span>
                    <span
                      className={`font-semibold ${
                        verification.color === "green"
                          ? "text-sky-600"
                          : "text-amber-600"
                      }`}
                    >
                      {verification.label}
                    </span>
                  </div>
                  {startup.transaction_signature && (
                    <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-lg">
                      <p className="text-slate-600 text-sm mb-2">
                        Transaction Signature
                      </p>
                      <p className="text-slate-900 font-mono text-xs break-all mb-3">
                        {startup.transaction_signature.substring(0, 20)}...
                      </p>
                      <a
                        href={`https://explorer.solana.com/tx/${startup.transaction_signature}?cluster=devnet`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        <ExternalLink size={14} />
                        View on Explorer
                      </a>
                    </div>
                  )}
                  {verification.status === "pending" && (
                    <p className="text-slate-600 text-sm mt-4">
                      Your startup is being verified on the blockchain. This
                      usually takes a few minutes.
                    </p>
                  )}
                </div>
              </motion.div>

              {/* Attestation Status */}
              {user?.id && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.05 }}
                >
                  <AttestationStatus
                    userId={user.id}
                    walletAddress={solanaAddress}
                    onUpdate={fetchStartupData}
                  />
                </motion.div>
              )}

              {/* Funding Progress */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="card"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-slate-900">
                    Funding Progress
                  </h2>
                  <DollarSign className="w-6 h-6 text-sky-600" />
                </div>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-slate-600 mb-2">
                      <span>Raised</span>
                      <span className="font-semibold text-slate-900">
                        ${(startup.total_investments || 0).toLocaleString()}{" "}
                        USDC
                      </span>
                    </div>
                    <div className="w-full h-4 bg-slate-200 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${fundingProgress}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="h-full bg-gradient-to-r from-sky-500 to-sky-600"
                      />
                    </div>
                    <div className="flex justify-between text-slate-600 text-sm mt-2">
                      <span>{fundingProgress.toFixed(1)}% Complete</span>
                      <span>
                        Goal: ${(startup.funding_goal || 0).toLocaleString()}{" "}
                        USDC
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mt-6">
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                      <p className="text-slate-600 text-sm">
                        Total Investments
                      </p>
                      <p className="text-2xl font-bold text-slate-900 mt-1">
                        {startup.investment_count || 0}
                      </p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                      <p className="text-slate-600 text-sm">Investors</p>
                      <p className="text-2xl font-bold text-slate-900 mt-1">
                        {startup.investor_count || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Startup Details */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="card"
              >
                <h2 className="text-2xl font-bold text-slate-900 mb-6">
                  About
                </h2>
                <div className="space-y-4 text-slate-700">
                  <div>
                    <h3 className="text-slate-900 font-semibold mb-2">
                      Description
                    </h3>
                    <p>{startup.description}</p>
                  </div>
                  {startup.mission && (
                    <div>
                      <h3 className="text-slate-900 font-semibold mb-2">
                        Mission
                      </h3>
                      <p>{startup.mission}</p>
                    </div>
                  )}
                  {startup.vision && (
                    <div>
                      <h3 className="text-slate-900 font-semibold mb-2">
                        Vision
                      </h3>
                      <p>{startup.vision}</p>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>

            {/* Sidebar */}
            <div className="space-y-8">
              {/* Quick Stats */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="card"
              >
                <h2 className="text-xl font-bold text-slate-900 mb-6">
                  Quick Stats
                </h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Users className="w-5 h-5" />
                      <span>Team Size</span>
                    </div>
                    <span className="text-slate-900 font-semibold">
                      {startup.team_size || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-600">
                      <TrendingUp className="w-5 h-5" />
                      <span>Credibility Score</span>
                    </div>
                    <span className="text-slate-900 font-semibold">
                      {startup.credibility_score?.toFixed(1) || "N/A"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Shield className="w-5 h-5" />
                      <span>Verified Employees</span>
                    </div>
                    <span className="text-slate-900 font-semibold">
                      {startup.employees_verified || 0}
                    </span>
                  </div>
                </div>
              </motion.div>

              {/* Contact Info */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="card"
              >
                <h2 className="text-xl font-bold text-slate-900 mb-6">
                  Contact
                </h2>
                <div className="space-y-3 text-slate-700">
                  {startup.contact_email && (
                    <div>
                      <p className="text-sm text-slate-600">Email</p>
                      <p className="text-slate-900">{startup.contact_email}</p>
                    </div>
                  )}
                  {startup.phone && (
                    <div>
                      <p className="text-sm text-slate-600">Phone</p>
                      <p className="text-slate-900">{startup.phone}</p>
                    </div>
                  )}
                  {startup.website && (
                    <div>
                      <p className="text-sm text-slate-600">Website</p>
                      <a
                        href={startup.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sky-600 hover:text-sky-700 underline transition-colors"
                      >
                        {startup.website}
                      </a>
                    </div>
                  )}
                  {startup.pitch_deck_url && (
                    <div>
                      <p className="text-sm text-slate-600">Pitch Deck</p>
                      <a
                        href={startup.pitch_deck_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sky-600 hover:text-sky-700 underline flex items-center gap-2 transition-colors"
                      >
                        <FileText className="w-4 h-4" />
                        View Pitch Deck
                      </a>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Wallet Info */}
              {solanaAddress && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="card"
                >
                  <h2 className="text-xl font-bold text-slate-900 mb-4">
                    Wallet
                  </h2>
                  <p className="text-slate-600 text-sm mb-2">Solana Address</p>
                  <p className="text-slate-900 font-mono text-xs break-all">
                    {solanaAddress}
                  </p>
                </motion.div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
