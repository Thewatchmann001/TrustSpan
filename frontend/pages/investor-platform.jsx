/**
 * New Investor Platform Page
 * Uses the new Investment Platform components
 */
import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import StartupList from "../investor/StartupList";
import StartupListEnhanced from "../investor/StartupListEnhanced";
import StartupDetails from "../investor/StartupDetails";
import InvestFlow from "../investor/InvestFlow";
import WalletConnect from "../investor/WalletConnect";
import { TrendingUp, Wallet, Shield, ExternalLink, Clock } from "lucide-react";

export default function InvestorPlatformPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [selectedStartup, setSelectedStartup] = useState(null);
  const [showInvestFlow, setShowInvestFlow] = useState(false);
  const [portfolio, setPortfolio] = useState(null);

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    if (user?.id) {
      fetchPortfolio();
    }
  }, [user]);

  const fetchPortfolio = async () => {
    if (!user?.id) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/investments/portfolio/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setPortfolio(data);
      }
    } catch (error) {
      console.error("Failed to fetch portfolio:", error);
    }
  };

  const handleStartupSelect = (startup) => {
    setSelectedStartup(startup);
    setShowInvestFlow(false);
  };

  const handleInvest = () => {
    if (selectedStartup) {
      setShowInvestFlow(true);
    }
  };

  const handleInvestmentSuccess = () => {
    setShowInvestFlow(false);
    setSelectedStartup(null);
    fetchPortfolio();
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Diaspora Investment Platform</h1>
          <p className="text-gray-600">
            Invest in verified Sierra Leone startups using USDC stablecoins. Zero fees, zero currency risk.
          </p>
        </div>

        {/* Wallet Connection */}
        <div className="mb-8">
          <WalletConnect
            userId={user.id}
            onConnect={(address) => {
              console.log("Wallet connected:", address);
            }}
          />
        </div>

        {/* Portfolio Summary */}
        {portfolio && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Your Portfolio</h2>
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg p-4">
                <p className="text-sm text-gray-600">Total Invested</p>
                <p className="text-2xl font-bold text-blue-600">
                  ${portfolio.total_invested_usdc?.toLocaleString() || "0"} USDC
                </p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <p className="text-sm text-gray-600">Total Investments</p>
                <p className="text-2xl font-bold text-indigo-600">
                  {portfolio.total_investments || 0}
                </p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <p className="text-sm text-gray-600">Startups</p>
                <p className="text-2xl font-bold text-purple-600">
                  {portfolio.startup_count || 0}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Investment History */}
        {portfolio && portfolio.all_investments && portfolio.all_investments.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold">Investment History</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">Startup</th>
                    <th className="text-left py-3 px-4">Amount</th>
                    <th className="text-left py-3 px-4">Date</th>
                    <th className="text-left py-3 px-4">Transaction</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.all_investments.map((investment) => (
                    <tr key={investment.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{investment.startup_name}</td>
                      <td className="py-3 px-4">
                        <span className="font-semibold text-blue-600">
                          {investment.amount.toLocaleString()} USDC
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {investment.timestamp
                          ? new Date(investment.timestamp).toLocaleDateString()
                          : "N/A"}
                      </td>
                      <td className="py-3 px-4">
                        {investment.explorer_url ? (
                          <a
                            href={investment.explorer_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-purple-600 hover:text-purple-700 font-medium text-sm"
                          >
                            <ExternalLink className="w-4 h-4" />
                            View on Explorer
                          </a>
                        ) : (
                          <span className="text-gray-400 text-sm">
                            {investment.tx_signature
                              ? `${investment.tx_signature.substring(0, 8)}...`
                              : "Pending"}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Startup List */}
          <div className={selectedStartup ? "lg:col-span-2" : "lg:col-span-3"}>
            {!selectedStartup && !showInvestFlow && (
              <StartupListEnhanced onStartupSelect={handleStartupSelect} />
            )}
            {selectedStartup && !showInvestFlow && (
              <div>
                <button
                  onClick={() => setSelectedStartup(null)}
                  className="mb-4 text-blue-600 hover:underline"
                >
                  ← Back to List
                </button>
                <StartupDetails startupId={selectedStartup.startup_id} />
                <div className="mt-6">
                  <button
                    onClick={handleInvest}
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
                  >
                    Invest in this Startup
                  </button>
                </div>
              </div>
            )}
            {showInvestFlow && selectedStartup && (
              <div>
                <button
                  onClick={() => setShowInvestFlow(false)}
                  className="mb-4 text-blue-600 hover:underline"
                >
                  ← Back to Details
                </button>
                <InvestFlow
                  startupId={selectedStartup.startup_id}
                  investorId={user.id}
                  onSuccess={handleInvestmentSuccess}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

