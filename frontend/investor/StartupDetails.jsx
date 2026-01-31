/**
 * Startup Details Component
 * Shows detailed startup information with verification proof, QR code, and chat
 */
import { useState, useEffect } from "react";
import {
  Shield,
  TrendingUp,
  Users,
  Globe,
  Mail,
  Phone,
  MessageSquare,
  QrCode,
  FileText,
  DollarSign,
  Briefcase,
  Target,
  Wallet,
} from "lucide-react";
import { useRouter } from "next/router";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";
import Chat from "../components/Chat";
import CredibilityBreakdown from "./CredibilityBreakdown";
import { AttestationBadgeList } from "../components/attestation/AttestationBadge";
import AttestationStatus from "../components/attestation/AttestationStatus";

export default function StartupDetails({ startupId }) {
  const router = useRouter();
  const { user } = useAuth();
  const [startup, setStartup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qrCode, setQrCode] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [founderId, setFounderId] = useState(null);

  useEffect(() => {
    if (startupId) {
      console.log("Fetching startup with ID:", startupId);
      fetchStartupDetails();
    }
  }, [startupId]);

  // Only fetch QR code if needed (lazy load for download button)
  useEffect(() => {
    if (startupId && startup && user?.role === "investor") {
      fetchQRCode();
    }
  }, [startupId, startup, user]);

  const fetchStartupDetails = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/startups/${startupId}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to fetch startup: ${response.status}`
        );
      }

      const data = await response.json();
      setStartup(data);
      // Extract founder_id for attestation fetching
      if (data.founder?.id) {
        setFounderId(data.founder.id);
      } else if (data.founder_id) {
        setFounderId(data.founder_id);
      }
    } catch (error) {
      console.error("Error fetching startup:", error);
      toast.error(error.message || "Failed to fetch startup details");
      setStartup(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchQRCode = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/startups/${startupId}/qr`);
      if (response.ok) {
        const data = await response.json();
        setQrCode(data.qr_code);
      }
    } catch (error) {
      console.error("Error fetching QR code:", error);
      toast.error("Failed to load QR code");
    }
  };

  if (loading) {
    return <p>Loading startup details...</p>;
  }

  if (!startup) {
    return (
      <div className="card p-6 text-center">
        <p className="text-red-600 font-semibold mb-2">Startup not found</p>
        <p className="text-gray-600 text-sm mb-4">Startup ID: {startupId}</p>
        <p className="text-gray-500 text-xs">
          Please check that the startup ID is correct and try again.
        </p>
      </div>
    );
  }

  return (
    <div className="startup-details space-y-6">
      {/* Header with Startup Name and Status */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg shadow-md p-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold mb-2">{startup.name}</h1>
            <div className="flex items-center gap-4 text-blue-100">
              <span className="flex items-center gap-2">
                <Briefcase className="w-4 h-4" />
                {startup.sector}
              </span>
              <span>•</span>
              <span>{startup.country || "Location not specified"}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg">
            <Shield className="w-5 h-5" />
            <span className="font-semibold">Verified</span>
          </div>
        </div>
      </div>

      {/* Attestation Badges */}
      {founderId && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-600" />
            Verification Badges
          </h2>
          <AttestationStatus userId={founderId} />
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
          <TrendingUp className="w-6 h-6 text-blue-600 mb-2" />
          <p className="text-sm text-gray-600 mb-1">Credibility Score</p>
          <p className="text-3xl font-bold text-blue-600">
            {(startup.credibility_score || 0).toFixed(1)}%
          </p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
          <Users className="w-6 h-6 text-green-600 mb-2" />
          <p className="text-sm text-gray-600 mb-1">Verified Employees</p>
          <p className="text-3xl font-bold text-green-600">
            {startup.employees_verified || 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
          <DollarSign className="w-6 h-6 text-purple-600 mb-2" />
          <p className="text-sm text-gray-600 mb-1">Funding Goal</p>
          <p className="text-2xl font-bold text-purple-600">
            ${(startup.funding_goal || 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200">
          <Target className="w-6 h-6 text-orange-600 mb-2" />
          <p className="text-sm text-gray-600 mb-1">Total Raised</p>
          <p className="text-2xl font-bold text-orange-600">
            ${(startup.total_investments || 0).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Credibility Breakdown for Investors */}
      {user && user.role === "investor" && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Shield className="w-6 h-6 text-indigo-600" />
            Investment Risk Analysis
          </h2>
          <CredibilityBreakdown startupId={startupId} />
        </div>
      )}

      {/* Startup ID */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <p className="text-sm text-gray-600 mb-1">Startup ID</p>
        <p className="text-lg font-mono font-semibold text-gray-800 break-all">
          {startup.startup_id || "N/A"}
        </p>
      </div>

      {/* About Section */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Briefcase className="w-6 h-6 text-blue-600" />
          About the Startup
        </h2>
        <div className="space-y-6">
          {/* Description */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">Description</h3>
            <p className="text-gray-700 leading-relaxed">
              {startup.description || "No description available."}
            </p>
          </div>

          {/* Mission */}
          {startup.mission && (
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
              <h3 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-600" />
                Mission
              </h3>
              <p className="text-gray-700 leading-relaxed">{startup.mission}</p>
            </div>
          )}

          {/* Vision */}
          {startup.vision && (
            <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
              <h3 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-600" />
                Vision
              </h3>
              <p className="text-gray-700 leading-relaxed">{startup.vision}</p>
            </div>
          )}

          {/* Team Size */}
          {startup.team_size && (
            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded">
              <Users className="w-5 h-5 text-gray-600" />
              <div>
                <p className="text-sm text-gray-600">Team Size</p>
                <p className="text-lg font-semibold text-gray-800">
                  {startup.team_size} members
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Contact Information */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Mail className="w-6 h-6 text-blue-600" />
          Contact Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {startup.contact_email && (
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <Mail className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-sm text-gray-600 mb-1">Email</p>
                <a
                  href={`mailto:${startup.contact_email}`}
                  className="text-blue-600 hover:underline font-medium break-all"
                >
                  {startup.contact_email}
                </a>
              </div>
            </div>
          )}
          {startup.phone && (
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <Phone className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-sm text-gray-600 mb-1">Phone</p>
                <a
                  href={`tel:${startup.phone}`}
                  className="text-blue-600 hover:underline font-medium"
                >
                  {startup.phone}
                </a>
              </div>
            </div>
          )}
          {startup.website && (
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <Globe className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-sm text-gray-600 mb-1">Website</p>
                <a
                  href={startup.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-medium break-all"
                >
                  {startup.website}
                </a>
              </div>
            </div>
          )}
          {startup.pitch_deck_url && (
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-sm text-gray-600 mb-1">Pitch Deck</p>
                <a
                  href={startup.pitch_deck_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-medium"
                >
                  View Document
                </a>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Blockchain Verification */}
      {startup.transaction_signature && (
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <Shield className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-green-900 mb-2">
                Blockchain Verified
              </h3>
              <p className="text-sm text-green-800 mb-3">
                This startup has been verified on the Solana blockchain.
              </p>
              <a
                href={`https://explorer.solana.com/tx/${startup.transaction_signature}?cluster=devnet`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition font-medium text-sm"
              >
                View Transaction on Solana Explorer
              </a>
              <p className="text-xs text-green-700 mt-3 font-mono break-all">
                {startup.transaction_signature}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Funding Wallet Address */}
      {startup.founder && startup.founder.wallet_address && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mt-4">
          <div className="flex items-start gap-4">
            <Wallet className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-blue-900 mb-2">
                Funding Wallet Address
              </h3>
              <p className="text-sm text-blue-800 mb-3">
                USDC investments are sent to this address (Devnet - test tokens only):
              </p>
              <div className="bg-white p-3 rounded border border-blue-200 mb-3">
                <p className="text-xs text-blue-900 font-mono break-all">
                  {startup.founder.wallet_address}
                </p>
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(startup.founder.wallet_address);
                  toast.success("Wallet address copied to clipboard!");
                }}
                className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition font-medium text-sm"
              >
                Copy Address
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Download QR Code Button - Optional for investors who want to share */}
      {user && user.role === "investor" && qrCode && (
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <button
            onClick={() => {
              const link = document.createElement("a");
              link.href = qrCode;
              link.download = `startup-${startupId}-qr.png`;
              link.click();
            }}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition text-gray-700 text-sm"
          >
            <QrCode className="w-4 h-4" />
            Download QR Code for Sharing
          </button>
          <p className="text-xs text-gray-500 mt-2">
            Share this startup's verification QR code (e.g., for presentations or marketing materials)
          </p>
        </div>
      )}

      {/* Action Buttons */}
      {user && user.role === "investor" && (
        <div className="flex gap-3">
          <button
            onClick={() => setShowChat(!showChat)}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
          >
            <MessageSquare className="w-5 h-5" />
            {showChat ? "Hide Chat" : "Chat with Startup"}
          </button>
        </div>
      )}

      {/* Chat Section */}
      {showChat && user && user.role === "investor" && startup.id && (
        <div
          className="border rounded-lg overflow-hidden shadow-lg"
          style={{ height: "500px" }}
        >
          <Chat
            investorId={user.id}
            startupId={startup.id}
            currentUserId={user.id}
            onClose={() => setShowChat(false)}
          />
        </div>
      )}
    </div>
  );
}
