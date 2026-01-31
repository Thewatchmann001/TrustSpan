/**
 * Attestation Badge Component
 * Displays verification badges for businesses and identities
 */
import { CheckCircle, Shield, Building2, Link as LinkIcon, Clock, XCircle, ExternalLink } from "lucide-react";

export default function AttestationBadge({ attestation, size = "md" }) {
  if (!attestation) return null;

  const { issuer, schema, status, verified, on_chain, badge_type, sas } = attestation;

  // Badge configuration
  const badgeConfig = {
    // Test/Dev badges
    "🧪 Test Verified Business (Devnet)": {
      icon: Building2,
      bgColor: "bg-amber-100",
      textColor: "text-amber-800",
      borderColor: "border-amber-300",
    },
    "🧪 Test Verified Identity (Devnet)": {
      icon: Shield,
      bgColor: "bg-amber-100",
      textColor: "text-amber-800",
      borderColor: "border-amber-300",
    },
    "🏢 Mock Verified Business": {
      icon: Building2,
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
      borderColor: "border-gray-300",
    },
    "🛡️ Mock Civic Verified Founder": {
      icon: Shield,
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
      borderColor: "border-gray-300",
    },
    "🛡️ Mock Verify Verified Identity": {
      icon: Shield,
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
      borderColor: "border-gray-300",
    },
    // Production badges (future)
    "🏢 Verified Business": {
      icon: Building2,
      bgColor: "bg-blue-100",
      textColor: "text-blue-700",
      borderColor: "border-blue-300",
    },
    "🛡️ Civic Verified Founder": {
      icon: Shield,
      bgColor: "bg-purple-100",
      textColor: "text-purple-700",
      borderColor: "border-purple-300",
    },
    "🛡️ Verify Verified Identity": {
      icon: Shield,
      bgColor: "bg-green-100",
      textColor: "text-green-700",
      borderColor: "border-green-300",
    },
    "⛓️ On-chain Business Attestation": {
      icon: LinkIcon,
      bgColor: "bg-slate-100",
      textColor: "text-slate-700",
      borderColor: "border-slate-300",
    },
    "⛓️ On-chain Identity Attestation": {
      icon: LinkIcon,
      bgColor: "bg-slate-100",
      textColor: "text-slate-700",
      borderColor: "border-slate-300",
    },
  };

  const config = badgeConfig[badge_type] || {
    icon: CheckCircle,
    bgColor: "bg-gray-100",
    textColor: "text-gray-700",
    borderColor: "border-gray-300",
  };

  const Icon = config.icon;
  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1.5",
    lg: "text-base px-4 py-2",
  };

  // Status indicators
  const statusIcon = verified ? (
    <CheckCircle className="w-4 h-4" />
  ) : status === "pending" ? (
    <Clock className="w-4 h-4" />
  ) : (
    <XCircle className="w-4 h-4" />
  );

  // Determine if this is a test/dev badge
  const isTestBadge = badge_type.includes("🧪") || badge_type.includes("Mock");
  const isDevnet = sas?.cluster === "devnet" || (on_chain && !sas?.cluster);

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${config.bgColor} ${config.textColor} ${config.borderColor} ${sizeClasses[size]}`}
      title={`${badge_type}${on_chain ? ` (On-chain${isDevnet ? ", Devnet" : ""})` : ""} - Status: ${status}`}
    >
      {statusIcon}
      <span>{badge_type}</span>
      {on_chain && (
        <LinkIcon className="w-3 h-3 opacity-70" title="On-chain attestation" />
      )}
      {sas?.explorer_url && (
        <a
          href={sas.explorer_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="ml-1 hover:opacity-100 opacity-70"
          title="View on Solana Explorer"
        >
          <ExternalLink className="w-3 h-3" />
        </a>
      )}
    </span>
  );
}

/**
 * Attestation Badge List Component
 * Displays multiple badges
 */
export function AttestationBadgeList({ attestations, size = "md" }) {
  if (!attestations || attestations.length === 0) {
    return (
      <div className="text-sm text-gray-500">No attestations</div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {attestations.map((att, index) => (
        <AttestationBadge key={att.id || index} attestation={att} size={size} />
      ))}
    </div>
  );
}
