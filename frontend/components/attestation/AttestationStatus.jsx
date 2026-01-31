/**
 * Attestation Status Component
 * Displays all attestations for a user/startup
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { Shield, Building2, RefreshCw, ExternalLink } from "lucide-react";
import { AttestationBadgeList } from "./AttestationBadge";
import toast from "react-hot-toast";

export default function AttestationStatus({ userId, walletAddress, onUpdate }) {
  const [attestations, setAttestations] = useState([]);
  const [loading, setLoading] = useState(true);

  const onUpdateRef = useRef(onUpdate);
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  const fetchAttestations = useCallback(async (shouldUpdate = false) => {
    if (!userId && !walletAddress) return;
    
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      const endpoint = userId
        ? `/api/attestations/user/${userId}`
        : `/api/attestations/wallet/${walletAddress}`;

      const response = await fetch(`${apiUrl}${endpoint}`);

      if (!response.ok) {
        throw new Error("Failed to fetch attestations");
      }

      const data = await response.json();
      const newAttestations = data.attestations || [];
      setAttestations(newAttestations);

      // Only call onUpdate if explicitly requested (e.g., manual refresh)
      if (shouldUpdate && onUpdateRef.current) {
        onUpdateRef.current();
      }
    } catch (error) {
      console.error("Error fetching attestations:", error);
      toast.error("Failed to load attestations");
    } finally {
      setLoading(false);
    }
  }, [userId, walletAddress]);

  useEffect(() => {
    if (userId || walletAddress) {
      fetchAttestations(false); // Don't trigger onUpdate on initial load
    }
  }, [userId, walletAddress, fetchAttestations]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Verification Status
        </h3>
        <button
          onClick={() => fetchAttestations(true)} // Trigger onUpdate on manual refresh
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {attestations.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Shield className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No attestations yet</p>
          <p className="text-sm mt-1">
            Complete verification to get verified badges
          </p>
        </div>
      ) : (
        <>
          <AttestationBadgeList attestations={attestations} size="md" />

          <div className="mt-4 space-y-2">
            {attestations.map((att, index) => (
              <div
                key={att.id || index}
                className="text-sm p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{att.badge_type}</span>
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      att.verified
                        ? "bg-green-100 text-green-700"
                        : att.status === "pending"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                    }`}
                  >
                    {att.status}
                  </span>
                </div>
                {att.on_chain && att.sas && (
                  <div className="text-xs text-gray-600 mt-2 space-y-1">
                    <p>
                      ✓ On-chain attestation ({att.sas.cluster || "devnet"})
                    </p>
                    {att.sas.tx_signature && (
                      <p className="font-mono text-xs break-all">
                        TX: {att.sas.tx_signature.substring(0, 16)}...
                      </p>
                    )}
                    {att.sas.explorer_url && (
                      <a
                        href={att.sas.explorer_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline flex items-center gap-1"
                      >
                        View on Explorer
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                )}
                {att.expires_at && (
                  <p className="text-xs text-gray-500 mt-1">
                    Expires: {new Date(att.expires_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
