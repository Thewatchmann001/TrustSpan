/**
 * Credibility Breakdown Component
 * Shows investor-friendly credibility view with verification checklist,
 * risk assessment, and red/green flags
 */
import { useState, useEffect } from "react";
import {
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Users,
  Briefcase,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import toast from "react-hot-toast";

export default function CredibilityBreakdown({ startupId }) {
  const [credibilityView, setCredibilityView] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState(null);

  useEffect(() => {
    if (startupId) {
      fetchCredibilityView();
    }
  }, [startupId]);

  const fetchCredibilityView = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const url = `${apiUrl}/api/startups/${startupId}/credibility-for-investor`;
      console.log("Fetching credibility view from:", url);
      
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      console.log("Credibility response status:", response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Credibility API error:", response.status, errorText);
        throw new Error(
          `Failed to fetch credibility view: ${response.status} ${response.statusText} - ${errorText}`
        );
      }

      const data = await response.json();
      console.log("Credibility data received:", data);
      setCredibilityView(data);
    } catch (error) {
      console.error("Error fetching credibility view:", error);
      toast.error(`Failed to load credibility information: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-8">
        <div className="space-y-4">
          <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-40 bg-gray-100 rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (!credibilityView) {
    return null;
  }

  const {
    verification_checklist,
    risk_assessment,
    red_flags,
    green_flags,
    investor_summary,
    investment_history,
  } = credibilityView;

  // Risk level colors and emojis
  const riskColors = {
    LOW: {
      bg: "bg-green-50",
      border: "border-green-200",
      text: "text-green-700",
      emoji: "✅",
    },
    MODERATE: {
      bg: "bg-yellow-50",
      border: "border-yellow-200",
      text: "text-yellow-700",
      emoji: "⚠️",
    },
    MEDIUM: {
      bg: "bg-orange-50",
      border: "border-orange-200",
      text: "text-orange-700",
      emoji: "⚠️",
    },
    HIGH: {
      bg: "bg-red-50",
      border: "border-red-200",
      text: "text-red-700",
      emoji: "🔴",
    },
    "VERY HIGH": {
      bg: "bg-red-100",
      border: "border-red-300",
      text: "text-red-800",
      emoji: "🔴",
    },
  };

  const riskColors_bg = riskColors[risk_assessment.level] || riskColors.MEDIUM;

  const SectionCard = ({ title, children, expanded, onToggle, icon: Icon }) => (
    <div
      className={`rounded-lg border transition-all ${
        expanded ? "border-indigo-300 bg-indigo-50" : "border-gray-200 bg-white"
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-indigo-600" />
          <span className="font-semibold text-gray-900">{title}</span>
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-gray-600" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-600" />
        )}
      </button>
      {expanded && (
        <div className="px-6 py-4 border-t border-gray-200 bg-white">
          {children}
        </div>
      )}
    </div>
  );

  const VerificationItem = ({ completed, label, value, description }) => (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-1">
        {completed ? (
          <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
        ) : (
          <div className="w-5 h-5 border-2 border-gray-300 rounded-full flex-shrink-0"></div>
        )}
        <span
          className={
            completed
              ? "text-gray-900 font-medium"
              : "text-gray-500 font-medium"
          }
        >
          {label}
        </span>
      </div>
      {value && <p className="ml-7 text-sm text-gray-600">{value}</p>}
      {description && (
        <p className="ml-7 text-xs text-gray-500 italic">{description}</p>
      )}
    </div>
  );

  const ProgressBar = ({ label, percentage }) => (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-semibold text-indigo-600">
          {percentage}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-indigo-600 h-2 rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Investor Summary */}
      <div
        className={`rounded-lg border-2 p-6 ${riskColors_bg.bg} ${riskColors_bg.border}`}
      >
        <div className="flex items-start gap-3">
          <span className="text-2xl">{riskColors_bg.emoji}</span>
          <div>
            <p className={`font-semibold ${riskColors_bg.text} mb-2`}>
              Investment Risk: {risk_assessment.level}
            </p>
            <p className="text-gray-700">{investor_summary}</p>
            {risk_assessment.description && (
              <p className={`text-sm ${riskColors_bg.text} mt-2`}>
                {risk_assessment.description}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Verification Sections */}
      <div className="space-y-3">
        {/* Team Verification */}
        <SectionCard
          title="👥 Team Verification"
          icon={Users}
          expanded={expandedSection === "team"}
          onToggle={() =>
            setExpandedSection(expandedSection === "team" ? null : "team")
          }
        >
          <div className="space-y-4">
            <ProgressBar
              label="Team Verification Complete"
              percentage={verification_checklist.team.completion}
            />
            <div className="space-y-2">
              {verification_checklist.team.items.map((item, idx) => (
                <VerificationItem
                  key={idx}
                  completed={item.verified}
                  label={item.label}
                  value={item.value}
                  description={item.description}
                />
              ))}
            </div>
          </div>
        </SectionCard>

        {/* Business Legitimacy */}
        <SectionCard
          title="🏢 Business Legitimacy"
          icon={Briefcase}
          expanded={expandedSection === "business"}
          onToggle={() =>
            setExpandedSection(
              expandedSection === "business" ? null : "business"
            )
          }
        >
          <div className="space-y-4">
            <ProgressBar
              label="Business Documents Complete"
              percentage={verification_checklist.business.completion}
            />
            <div className="space-y-2">
              {verification_checklist.business.items.map((item, idx) => (
                <VerificationItem
                  key={idx}
                  completed={item.verified}
                  label={item.label}
                  value={item.value}
                  description={item.description}
                />
              ))}
            </div>
          </div>
        </SectionCard>

        {/* Product Traction */}
        <SectionCard
          title="🚀 Product Traction"
          icon={TrendingUp}
          expanded={expandedSection === "product"}
          onToggle={() =>
            setExpandedSection(expandedSection === "product" ? null : "product")
          }
        >
          <div className="space-y-4">
            <ProgressBar
              label="Product Traction Complete"
              percentage={verification_checklist.product.completion}
            />
            <div className="space-y-2">
              {verification_checklist.product.items.map((item, idx) => (
                <VerificationItem
                  key={idx}
                  completed={item.verified}
                  label={item.label}
                  value={item.value}
                  description={item.description}
                />
              ))}
            </div>
          </div>
        </SectionCard>

        {/* Blockchain Verification */}
        <SectionCard
          title="⛓️ Blockchain Verification"
          icon={Zap}
          expanded={expandedSection === "blockchain"}
          onToggle={() =>
            setExpandedSection(
              expandedSection === "blockchain" ? null : "blockchain"
            )
          }
        >
          <div className="space-y-4">
            <ProgressBar
              label="Blockchain Verification Complete"
              percentage={verification_checklist.blockchain.completion}
            />
            <div className="space-y-2">
              {verification_checklist.blockchain.items.map((item, idx) => (
                <VerificationItem
                  key={idx}
                  completed={item.verified}
                  label={item.label}
                  value={item.value}
                  description={item.description}
                />
              ))}
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Red & Green Flags */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Red Flags */}
        {red_flags && red_flags.length > 0 && (
          <div className="bg-red-50 rounded-lg border border-red-200 p-6">
            <h3 className="font-semibold text-red-900 mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Risk Indicators
            </h3>
            <ul className="space-y-2">
              {red_flags.map((flag, idx) => (
                <li
                  key={idx}
                  className="text-red-800 text-sm flex items-start gap-2"
                >
                  <span className="text-lg">⚠️</span>
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Green Flags */}
        {green_flags && green_flags.length > 0 && (
          <div className="bg-green-50 rounded-lg border border-green-200 p-6">
            <h3 className="font-semibold text-green-900 mb-4 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5" />
              Positive Signals
            </h3>
            <ul className="space-y-2">
              {green_flags.map((flag, idx) => (
                <li
                  key={idx}
                  className="text-green-800 text-sm flex items-start gap-2"
                >
                  <span className="text-lg">✅</span>
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Investment History */}
      {investment_history && (
        <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg border border-indigo-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">
            Investment History
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total Investors</p>
              <p className="text-2xl font-bold text-indigo-600">
                {investment_history.total_investors || 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Raised</p>
              <p className="text-2xl font-bold text-indigo-600">
                ${(investment_history.total_raised || 0).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Investments</p>
              <p className="text-2xl font-bold text-indigo-600">
                {investment_history.number_of_investments || 0}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
