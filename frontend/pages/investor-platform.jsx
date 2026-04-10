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
import BackgroundImage from "../components/BackgroundImage";
import { TrendingUp, Wallet, Shield, ExternalLink, Clock, Download } from "lucide-react";
import toast from "react-hot-toast";

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

  // After Stripe Checkout success redirect: confirm session and record investment
  useEffect(() => {
    const { payment, session_id } = router.query;
    if (payment !== "success" || !session_id || !user?.id) return;
    const confirm = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
        const res = await fetch(`${apiUrl}/api/payments/confirm-session`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({ session_id }),
        });
        if (res.ok) {
          const data = await res.json();
          toast.success(
            `Investment recorded! $${data.amount} invested.`,
            { duration: 4000 }
          );
          fetchPortfolio();
        } else {
          const err = await res.json().catch(() => ({}));
          toast.error(err.detail || "Could not confirm payment");
        }
      } catch (e) {
        toast.error("Could not confirm payment");
      } finally {
        router.replace("/investor-platform", undefined, { scroll: false });
      }
    };
    confirm();
  }, [router.query.payment, router.query.session_id, user?.id]);

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

  const handleDownloadReceipt = async (investmentId) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/investments/${investmentId}/receipt`);
      
      if (!response.ok) {
        throw new Error('Failed to download receipt');
      }
      
      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `Investment-Receipt-${investmentId}.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Receipt downloaded successfully!');
    } catch (error) {
      console.error('Error downloading receipt:', error);
      toast.error('Failed to download receipt');
    }
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header Section with Background */}
      <BackgroundImage
        src="/images/backgrounds/hero/investor-hero.jpg"
        alt="Investor Platform - TrustBridge"
        overlay="default"
        className="h-64 flex-shrink-0"
        priority={true}
      >
        <div className="max-w-7xl mx-auto px-6 py-12 h-full flex items-end">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-3">
              Professional Investment Platform
            </h1>
            <p className="text-xl text-white font-semibold max-w-3xl">
              Invest in verified startups. Zero fees. Full transparency. Blockchain-verified credibility.
            </p>
          </div>
        </div>
      </BackgroundImage>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">

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
          <div className="card-premium mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-slate-900">Your Portfolio</h2>
              <TrendingUp className="w-6 h-6 text-amber-600" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-slate-50 to-white rounded-xl p-6 border border-slate-200">
                <p className="text-sm text-slate-600 mb-2">Total Invested</p>
                <p className="text-3xl font-bold text-amber-600">
                  ${portfolio.total_invested_usdc?.toLocaleString() || "0"} USDC
                </p>
              </div>
              <div className="bg-gradient-to-br from-slate-50 to-white rounded-xl p-6 border border-slate-200">
                <p className="text-sm text-slate-600 mb-2">Total Investments</p>
                <p className="text-3xl font-bold text-sky-600">
                  {portfolio.total_investments || 0}
                </p>
              </div>
              <div className="bg-gradient-to-br from-slate-50 to-white rounded-xl p-6 border border-slate-200">
                <p className="text-sm text-slate-600 mb-2">Startups</p>
                <p className="text-3xl font-bold text-violet-600">
                  {portfolio.startup_count || 0}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Investment History */}
        {portfolio && portfolio.all_investments && portfolio.all_investments.length > 0 && (
          <div className="card mb-8">
            <div className="flex items-center gap-2 mb-6">
              <Clock className="w-6 h-6 text-amber-600" />
              <h2 className="text-2xl font-bold text-slate-900">Investment History</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-slate-900 font-semibold">Startup</th>
                    <th className="text-left py-3 px-4 text-slate-900 font-semibold">Amount</th>
                    <th className="text-left py-3 px-4 text-slate-900 font-semibold">Date</th>
                    <th className="text-left py-3 px-4 text-slate-900 font-semibold">Transaction</th>
                    <th className="text-left py-3 px-4 text-slate-900 font-semibold">Receipt</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.all_investments.map((investment) => (
                    <tr key={investment.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-900">{investment.startup_name}</td>
                      <td className="py-3 px-4">
                        <span className="font-semibold text-amber-600">
                          {investment.amount.toLocaleString()} USDC
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-600">
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
                            className="flex items-center gap-2 text-violet-600 hover:text-violet-700 font-medium text-sm transition-colors"
                          >
                            <ExternalLink className="w-4 h-4" />
                            View on Explorer
                          </a>
                        ) : (
                          <span className="text-slate-400 text-sm">
                            {investment.tx_signature
                              ? `${investment.tx_signature.substring(0, 8)}...`
                              : "Pending"}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => handleDownloadReceipt(investment.id)}
                          className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 font-medium text-sm transition-colors"
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </button>
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
                  className="mb-4 text-slate-700 hover:text-slate-900 font-medium transition-colors"
                >
                  ← Back to List
                </button>
                <StartupDetails startupId={selectedStartup.startup_id} />
                <div className="mt-6">
                  <button
                    onClick={handleInvest}
                    className="btn-cta"
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
                  className="mb-4 text-slate-700 hover:text-slate-900 font-medium transition-colors"
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

