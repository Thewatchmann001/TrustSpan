/**
 * Verification Flow Component
 * Handles business and identity verification requests
 */
import { useState } from "react";
import { Building2, Shield, Loader, CheckCircle, AlertCircle, ExternalLink } from "lucide-react";
import toast from "react-hot-toast";
import AttestationBadge from "./AttestationBadge";

export default function VerificationFlow({ user, onComplete }) {
  const [step, setStep] = useState(1); // 1: Type selection, 2: Form, 3: Processing, 4: Success
  const [verificationType, setVerificationType] = useState(null); // "business" or "identity"
  const [issuer, setIssuer] = useState("verify"); // "verify" or "civic"
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Form data
  const [businessData, setBusinessData] = useState({
    business_name: "",
    registration_number: "",
  });

  const [identityData, setIdentityData] = useState({
    full_name: user?.full_name || "",
    email: user?.email || "",
    date_of_birth: "",
    nationality: "",
  });

  const handleVerify = async () => {
    if (!user?.wallet_address) {
      toast.error("Wallet address required for verification");
      return;
    }

    setLoading(true);
    setStep(3);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const endpoint =
        verificationType === "business"
          ? "/api/attestations/verify/business"
          : "/api/attestations/verify/identity";

      const requestData =
        verificationType === "business"
          ? {
              wallet_address: user.wallet_address,
              business_name: businessData.business_name,
              registration_number: businessData.registration_number,
              issuer: issuer,
              create_sas_attestation: true,
            }
          : {
              wallet_address: user.wallet_address,
              full_name: identityData.full_name,
              email: identityData.email,
              date_of_birth: identityData.date_of_birth || null,
              nationality: identityData.nationality || null,
              issuer: issuer,
              create_sas_attestation: true,
            };

      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Verification failed");
      }

      const data = await response.json();
      setResult(data);
      setStep(4);

      if (data.success) {
        toast.success("Verification successful!");
        if (onComplete) onComplete(data);
      } else {
        toast.error(data.error || "Verification failed");
      }
    } catch (error) {
      toast.error(error.message || "Failed to verify");
      setStep(2); // Go back to form
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Type Selection
  if (step === 1) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold mb-4">Choose Verification Type</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => {
              setVerificationType("business");
              setIssuer("verify");
              setStep(2);
            }}
            className="p-6 border-2 border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
          >
            <Building2 className="w-8 h-8 text-blue-600 mb-2" />
            <h4 className="font-semibold text-lg mb-1">Business Verification</h4>
            <p className="text-sm text-gray-600">
              Verify business ownership and registration
            </p>
          </button>

          <button
            onClick={() => {
              setVerificationType("identity");
              setIssuer("civic");
              setStep(2);
            }}
            className="p-6 border-2 border-purple-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all text-left"
          >
            <Shield className="w-8 h-8 text-purple-600 mb-2" />
            <h4 className="font-semibold text-lg mb-1">Identity Verification</h4>
            <p className="text-sm text-gray-600">
              Verify personal identity and KYC
            </p>
          </button>
        </div>
      </div>
    );
  }

  // Step 2: Form
  if (step === 2) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold">
            {verificationType === "business"
              ? "Business Verification"
              : "Identity Verification"}
          </h3>
          <button
            onClick={() => setStep(1)}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            ← Back
          </button>
        </div>

        {verificationType === "business" ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Business Name *
              </label>
              <input
                type="text"
                value={businessData.business_name}
                onChange={(e) =>
                  setBusinessData({ ...businessData, business_name: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Your Company Name"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Registration Number *
              </label>
              <input
                type="text"
                value={businessData.registration_number}
                onChange={(e) =>
                  setBusinessData({
                    ...businessData,
                    registration_number: e.target.value,
                  })
                }
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Business Registration Number"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Verification Provider
              </label>
              <select
                value={issuer}
                onChange={(e) => setIssuer(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="verify">Verify (Business Verification)</option>
                <option value="civic" disabled>
                  Civic (Identity Only)
                </option>
              </select>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Full Name *</label>
              <input
                type="text"
                value={identityData.full_name}
                onChange={(e) =>
                  setIdentityData({ ...identityData, full_name: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Email *</label>
              <input
                type="email"
                value={identityData.email}
                onChange={(e) =>
                  setIdentityData({ ...identityData, email: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Date of Birth (Optional)
              </label>
              <input
                type="date"
                value={identityData.date_of_birth}
                onChange={(e) =>
                  setIdentityData({ ...identityData, date_of_birth: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Nationality (Optional)
              </label>
              <input
                type="text"
                value={identityData.nationality}
                onChange={(e) =>
                  setIdentityData({ ...identityData, nationality: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="e.g., Sierra Leone"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Verification Provider
              </label>
              <select
                value={issuer}
                onChange={(e) => setIssuer(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="civic">Civic (Identity Verification)</option>
                <option value="verify">Verify (Identity Verification)</option>
              </select>
            </div>
          </div>
        )}

        <div className="mt-6 flex gap-2">
          <button
            onClick={() => setStep(1)}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleVerify}
            disabled={
              loading ||
              (verificationType === "business" &&
                (!businessData.business_name || !businessData.registration_number)) ||
              (verificationType === "identity" &&
                (!identityData.full_name || !identityData.email))
            }
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex-1"
          >
            Verify
          </button>
        </div>
      </div>
    );
  }

  // Step 3: Processing
  if (step === 3) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
        <h3 className="text-xl font-bold mb-2">Verifying...</h3>
        <p className="text-gray-600">
          Please wait while we verify your {verificationType} information.
        </p>
        <p className="text-sm text-gray-500 mt-2">
          This may take a few seconds (using mock verification in development mode)
        </p>
      </div>
    );
  }

  // Step 4: Success/Error
  if (step === 4 && result) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        {result.success ? (
          <>
            <div className="text-center mb-6">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-2xl font-bold mb-2">Verification Successful!</h3>
              <p className="text-gray-600">
                Your {verificationType} has been verified and recorded on-chain.
              </p>
            </div>

            {result.attestation && (
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h4 className="font-semibold mb-2">Attestation Details</h4>
                <AttestationBadge attestation={result.attestation} size="lg" />
                <div className="mt-3 text-sm space-y-1">
                  <p>
                    <strong>ID:</strong> {result.attestation.id.slice(0, 20)}...
                  </p>
                  <p>
                    <strong>Issuer:</strong> {result.attestation.issuer}
                  </p>
                  {result.attestation.on_chain && (
                    <p className="text-green-600">
                      ✓ On-chain attestation created
                    </p>
                  )}
                  {result.sas && (
                    <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                      <p className="font-semibold text-blue-900 mb-1">On-Chain Transaction</p>
                      <p className="text-xs font-mono break-all">
                        <strong>TX:</strong> {result.sas.tx_signature}
                      </p>
                      <p className="text-xs">
                        <strong>Cluster:</strong> {result.sas.cluster}
                      </p>
                      {result.sas.explorer_url && (
                        <a
                          href={result.sas.explorer_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 underline text-xs flex items-center gap-1 mt-1"
                        >
                          View on Solana Explorer
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            <button
              onClick={() => {
                setStep(1);
                setResult(null);
                if (onComplete) onComplete(result);
              }}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Done
            </button>
          </>
        ) : (
          <>
            <div className="text-center mb-6">
              <AlertCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h3 className="text-2xl font-bold mb-2">Verification Failed</h3>
              <p className="text-gray-600">{result.error || "Unknown error"}</p>
            </div>

            <button
              onClick={() => setStep(2)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    );
  }

  return null;
}
