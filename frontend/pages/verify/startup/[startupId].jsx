/**
 * Startup Verification Page
 * Public page that displays blockchain verification proof and startup details
 */
import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import {
  Shield,
  ExternalLink,
  CheckCircle,
  TrendingUp,
  Users,
  Globe,
  Mail,
  Phone,
  Download,
} from "lucide-react";
import toast from "react-hot-toast";

export default function VerifyStartup() {
  const router = useRouter();
  const { startupId } = router.query;
  const [startup, setStartup] = useState(null);
  const [blockchainData, setBlockchainData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (startupId) {
      fetchVerificationData();
    }
  }, [startupId]);

  const fetchVerificationData = async () => {
    try {
      setLoading(true);

      // Use environment variable or default to localhost for API calls
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      // Get startup details (database + blockchain)
      const response = await fetch(`${apiUrl}/api/startups/${startupId}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Startup not found");
      }
      const data = await response.json();
      setStartup(data);

      // Get blockchain verification
      try {
        const verifyResponse = await fetch(
          `${apiUrl}/api/startups/verify/${startupId}`
        );
        if (verifyResponse.ok) {
          const verifyData = await verifyResponse.json();
          setBlockchainData(verifyData);
        }
      } catch (error) {
        console.error("Error fetching blockchain data:", error);
      }
    } catch (error) {
      console.error("Error fetching verification:", error);
      toast.error(error.message || "Failed to fetch verification data");
    } finally {
      setLoading(false);
    }
  };

  const downloadQRCode = () => {
    if (!startup) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/startups/${startupId}/qr`)
      .then((res) => res.json())
      .then((data) => {
        const link = document.createElement("a");
        link.href = data.qr_code;
        link.download = `startup-${startupId}-qr.png`;
        link.click();
      })
      .catch((err) => {
        toast.error("Failed to download QR code");
      });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading verification...</p>
        </div>
      </div>
    );
  }

  if (!startup) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-md p-6 text-center max-w-md">
          <p className="text-red-600 font-semibold mb-2 text-xl">
            Startup Not Found
          </p>
          <p className="text-gray-600 text-sm mb-4">Startup ID: {startupId}</p>
          <p className="text-gray-500 text-xs">
            Please check that the startup ID is correct and try again.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-green-600" />
            <div>
              <h1 className="text-2xl font-bold text-green-800">
                Verified Startup
              </h1>
              <p className="text-green-600">Blockchain-verified on Solana</p>
            </div>
          </div>
        </div>

        {/* Startup Info */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-3xl font-bold mb-2">{startup.name}</h2>
              <p className="text-gray-600 text-lg">{startup.sector}</p>
            </div>
            {startup.verified && (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="w-6 h-6" />
                <span className="font-semibold">Verified</span>
              </div>
            )}
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <TrendingUp className="w-6 h-6 mx-auto mb-2 text-blue-600" />
              <p className="text-2xl font-bold">
                {startup.credibility_score || 0}%
              </p>
              <p className="text-sm text-gray-600">Credibility Score</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <Users className="w-6 h-6 mx-auto mb-2 text-green-600" />
              <p className="text-2xl font-bold">
                {startup.employees_verified || 0}
              </p>
              <p className="text-sm text-gray-600">Verified Employees</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <span className="text-2xl font-bold">
                ${startup.funding_goal?.toLocaleString() || "N/A"}
              </span>
              <p className="text-sm text-gray-600">Funding Goal</p>
            </div>
          </div>

          {/* Description */}
          {startup.description && (
            <div className="mb-4">
              <h3 className="font-semibold mb-2">About</h3>
              <p className="text-gray-700">{startup.description}</p>
            </div>
          )}

          {/* Contact Information */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            {startup.website && (
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-gray-400" />
                <a
                  href={startup.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {startup.website}
                </a>
              </div>
            )}
            {startup.contact_email && (
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-gray-400" />
                <a
                  href={`mailto:${startup.contact_email}`}
                  className="text-blue-600 hover:underline"
                >
                  {startup.contact_email}
                </a>
              </div>
            )}
            {startup.phone && (
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-gray-400" />
                <span>{startup.phone}</span>
              </div>
            )}
          </div>
        </div>

        {/* Blockchain Proof */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2 text-lg">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Blockchain Verification
          </h3>

          <div className="space-y-3">
            {startup.transaction_signature && (
              <div>
                <p className="text-sm text-gray-600 mb-1">
                  Transaction Signature
                </p>
                <a
                  href={`https://explorer.solana.com/tx/${startup.transaction_signature}?cluster=devnet`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-mono text-sm flex items-center gap-2 break-all"
                >
                  {startup.transaction_signature}
                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                </a>
              </div>
            )}

            {blockchainData?.blockchain_proof?.account_address && (
              <div>
                <p className="text-sm text-gray-600 mb-1">On-Chain Account</p>
                <a
                  href={`https://explorer.solana.com/address/${blockchainData.blockchain_proof.account_address}?cluster=devnet`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-mono text-sm flex items-center gap-2 break-all"
                >
                  {blockchainData.blockchain_proof.account_address}
                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                </a>
              </div>
            )}

            <div>
              <p className="text-sm text-gray-600 mb-1">Verification Status</p>
              <p
                className={`font-semibold ${
                  startup.verified ? "text-green-600" : "text-yellow-600"
                }`}
              >
                {startup.verified
                  ? "✓ Verified on Blockchain"
                  : "Pending Verification"}
              </p>
            </div>

            {startup.founder && (
              <div>
                <p className="text-sm text-gray-600 mb-1">Founder</p>
                <p className="font-semibold">{startup.founder.name}</p>
                {startup.founder.email && (
                  <p className="text-sm text-gray-600">
                    {startup.founder.email}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* QR Code Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-lg">Verification QR Code</h3>
            <button
              onClick={downloadQRCode}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>
          <div className="flex justify-center">
            <QRCodeDisplay startupId={startupId} />
          </div>
        </div>
      </div>
    </div>
  );
}

function QRCodeDisplay({ startupId }) {
  const [qrData, setQrData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (startupId) {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
      fetch(`${apiUrl}/api/startups/${startupId}/qr`)
        .then((res) => res.json())
        .then((data) => {
          setQrData(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching QR code:", err);
          setLoading(false);
        });
    }
  }, [startupId]);

  if (loading) {
    return <div className="p-8">Loading QR code...</div>;
  }

  if (!qrData) {
    return <div className="p-8 text-gray-500">QR code unavailable</div>;
  }

  return (
    <div className="text-center">
      <img
        src={qrData.qr_code}
        alt="Startup Verification QR Code"
        className="mx-auto border-4 border-gray-200 rounded-lg"
      />
      <p className="text-sm text-gray-600 mt-4">
        Scan to verify this startup on blockchain
      </p>
    </div>
  );
}
