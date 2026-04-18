import { useState, useEffect } from "react";
import Link from "next/link";
import { Building2, MapPin, Users, TrendingUp, Award, X, ExternalLink, Shield } from "lucide-react";
import { startupAPI } from "../utils/api";
import toast from "react-hot-toast";
import { AttestationBadgeList } from "./attestation/AttestationBadge";

const StartupCard = ({ startup }) => {
  const [showEmployees, setShowEmployees] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [attestations, setAttestations] = useState([]);
  const [loadingAttestations, setLoadingAttestations] = useState(false);

  const credibilityGrade =
    startup.credibility_score >= 80
      ? "A+"
      : startup.credibility_score >= 70
      ? "A"
      : startup.credibility_score >= 60
      ? "B"
      : startup.credibility_score >= 50
      ? "C"
      : "D";

  const handleShowEmployees = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (showEmployees) {
      setShowEmployees(false);
      return;
    }
    try {
      setLoadingEmployees(true);
      const response = await startupAPI.getEmployees(startup.startup_id);
      setEmployees(response.data || []);
      setShowEmployees(true);
    } catch (error) {
      toast.error("Failed to load employees");
    } finally {
      setLoadingEmployees(false);
    }
  };

  // Fetch attestations if founder_id is available
  useEffect(() => {
    const founderId = startup.founder_id || startup.founder?.id;
    if (founderId) {
      fetchAttestations(founderId);
    }
  }, [startup.founder_id, startup.founder?.id]);

  const fetchAttestations = async (founderId) => {
    try {
      setLoadingAttestations(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/attestations/user/${founderId}`);
      if (response.ok) {
        const data = await response.json();
        // Only show verified attestations
        const verified = (data.attestations || []).filter(att => att.verified);
        setAttestations(verified.slice(0, 2)); // Show max 2 badges on card
      }
    } catch (error) {
      console.error("Error fetching attestations:", error);
    } finally {
      setLoadingAttestations(false);
    }
  };

  return (
    <>
      <Link href={`/investor/startup-profile?id=${startup.startup_id}`}>
        <div className="card hover:scale-105 cursor-pointer group">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3 flex-1">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-trust-blue to-trust-dark flex items-center justify-center text-white flex-shrink-0">
                <Building2 className="w-8 h-8" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-xl font-bold text-gray-900 group-hover:text-trust-blue transition-colors">
                  {startup.name}
                </h3>
                <p className="text-gray-600 text-sm">{startup.sector}</p>
                <p className="text-gray-500 text-xs font-mono mt-1 break-all">
                  ID: {startup.startup_id || "N/A"}
                </p>
              </div>
            </div>
            <div className="text-right flex-shrink-0 ml-2">
              <div className="text-2xl font-bold text-trust-blue">
                {credibilityGrade}
              </div>
              <div className="text-xs text-gray-500">Credibility</div>
            </div>
          </div>

          <div className="space-y-2 mb-4">
            {startup.country && (
              <div className="flex items-center gap-2 text-gray-600">
                <MapPin className="w-4 h-4" />
                <span className="text-sm">{startup.country}</span>
              </div>
            )}
            <button
              onClick={handleShowEmployees}
              className="flex items-center gap-2 text-gray-600 hover:text-trust-blue transition-colors w-full text-left"
            >
              <Users className="w-4 h-4" />
              <span className="text-sm">
                {startup.employees_verified || 0} Verified Employees (click to
                view)
              </span>
            </button>
            {startup.credibility_score !== undefined && (
              <div className="flex items-center gap-2 text-gray-600">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">
                  Score: {startup.credibility_score.toFixed(1)}/100
                </span>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-gray-200 space-y-2">
            {/* Attestation Badges */}
            {attestations.length > 0 && (
              <div className="mb-2">
                <AttestationBadgeList attestations={attestations} size="sm" />
              </div>
            )}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-green-600" />
                <span className="text-sm font-bold text-green-700">
                  Blockchain Verified
                </span>
              </div>
              <span className="text-sm text-trust-blue font-semibold group-hover:underline">
                View Details →
              </span>
            </div>
            {startup.transaction_signature && (
              <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-xs font-bold text-green-900 mb-1">Transaction Hash:</p>
                <a
                  href={`https://explorer.solana.com/tx/${startup.transaction_signature}?cluster=devnet`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-xs text-green-700 hover:text-green-900 font-mono break-all flex items-center gap-1 hover:underline"
                >
                  {startup.transaction_signature.substring(0, 16)}...
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              </div>
            )}
          </div>
        </div>
      </Link>

      {/* Employees Modal */}
      {showEmployees && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowEmployees(false)}
        >
          <div
            className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Employees - {startup.name}</h2>
              <button
                onClick={() => setShowEmployees(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            {loadingEmployees ? (
              <div className="text-center py-8">Loading employees...</div>
            ) : employees.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No employees found
              </div>
            ) : (
              <div className="space-y-4">
                {employees.map((emp) => (
                  <div key={emp.user_id} className="p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-semibold">{emp.full_name}</h3>
                    <p className="text-sm text-gray-600">{emp.email}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {emp.certificates_count} certificate(s)
                    </p>
                    {emp.certificates && emp.certificates.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {emp.certificates.map((cert, idx) => (
                          <div
                            key={idx}
                            className="text-xs bg-white p-2 rounded"
                          >
                            <span className="font-semibold">{cert.major}</span>{" "}
                            - {cert.university} ({cert.graduation_year})
                            {cert.verified === "verified" && (
                              <span className="ml-2 text-green-600">
                                ✓ Verified
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default StartupCard;
