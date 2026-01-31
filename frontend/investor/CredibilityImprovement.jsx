/**
 * Credibility Improvement Component
 * Shows actionable items to improve startup credibility score
 */
import { useState, useEffect } from "react";
import {
  AlertCircle,
  CheckCircle,
  Upload,
  Edit,
  Users,
  Rocket,
  Building2,
  UserCheck,
  ExternalLink,
  Mail,
  MapPin,
  FileText,
  TrendingUp,
  DollarSign,
} from "lucide-react";
import toast from "react-hot-toast";
import TeamMemberManager from "./TeamMemberManager";

export default function CredibilityImprovement({ startup, onUpdate }) {
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({
    founder_experience_years: startup?.founder_experience_years || "",
    has_mvp: startup?.has_mvp || false,
    user_base_count: startup?.user_base_count || "",
    monthly_revenue: startup?.monthly_revenue || "",
    employees_verified: startup?.employees_verified || 0,
    website: startup?.website || "",
    contact_email: startup?.contact_email || "",
    address: startup?.address || "",
    business_registration_verified: startup?.business_registration_verified || false,
    documents_url: startup?.documents_url || "",
    founder_profile_verified: startup?.founder_profile_verified || false,
    mvp_url: "",
    registration_doc_url: "",
    founder_profile_url: "",
  });

  const handleUpdate = async (updates) => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      
      const response = await fetch(
        `${apiUrl}/api/startups/${startup.startup_id}/update-credibility`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updates),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update");
      }

      const data = await response.json();
      toast.success("✅ Updated successfully! Credibility score: " + data.credibility_score.toFixed(1));
      setEditing(null);
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error("Failed to update. Please try again.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const improvementItems = [
    {
      id: "founder_experience",
      title: "Founder Experience",
      icon: UserCheck,
      description: "Add your years of industry experience",
      issue: !startup?.founder_experience_years || startup.founder_experience_years < 2,
      action: (
        <div className="space-y-2">
          <input
            type="number"
            min="0"
            max="50"
            value={formData.founder_experience_years}
            onChange={(e) => setFormData({ ...formData, founder_experience_years: parseInt(e.target.value) || 0 })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="Years of experience"
          />
          <button
            onClick={() => handleUpdate({ founder_experience_years: formData.founder_experience_years })}
            disabled={loading}
            className="w-full px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 transition-all"
          >
            Save
          </button>
        </div>
      ),
    },
    {
      id: "mvp",
      title: "MVP / Working Product",
      icon: Rocket,
      description: "Provide a link to your working MVP or product",
      issue: !startup?.has_mvp,
      action: (
        <div className="space-y-2">
          <input
            type="url"
            value={formData.mvp_url || ""}
            onChange={(e) => setFormData({ ...formData, mvp_url: e.target.value })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="https://your-mvp.com or https://demo-link.com"
          />
          <p className="text-xs text-slate-600 font-medium">Provide a working link to your MVP or product demo</p>
          <button
            onClick={() => {
              if (!formData.mvp_url || !formData.mvp_url.trim()) {
                toast.error("Please provide a link to your MVP/product first");
                return;
              }
              handleUpdate({
                has_mvp: true,
                documents_url: formData.mvp_url
              });
            }}
            disabled={loading || !formData.mvp_url?.trim()}
            className="w-full px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? "Saving..." : "Verify MVP"}
          </button>
        </div>
      ),
    },
    {
      id: "user_base",
      title: "Active User Base",
      icon: Users,
      description: "Enter your current number of active users/customers",
      issue: !startup?.user_base_count || startup.user_base_count === 0,
      action: (
        <div className="space-y-2">
          <input
            type="number"
            min="0"
            value={formData.user_base_count}
            onChange={(e) => setFormData({ ...formData, user_base_count: parseInt(e.target.value) || 0 })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="Number of active users"
          />
          <button
            onClick={() => handleUpdate({ user_base_count: formData.user_base_count })}
            disabled={loading}
            className="w-full px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 transition-all"
          >
            Save
          </button>
        </div>
      ),
    },
    {
      id: "revenue",
      title: "Monthly Revenue",
      icon: DollarSign,
      description: "Enter your monthly revenue in USDC",
      issue: !startup?.monthly_revenue || startup.monthly_revenue === 0,
      action: (
        <div className="space-y-2">
          <input
            type="number"
            min="0"
            step="0.01"
            value={formData.monthly_revenue}
            onChange={(e) => setFormData({ ...formData, monthly_revenue: parseFloat(e.target.value) || 0 })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="Monthly revenue in USDC"
          />
          <button
            onClick={() => handleUpdate({ monthly_revenue: formData.monthly_revenue })}
            disabled={loading}
            className="w-full px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 transition-all"
          >
            Save
          </button>
        </div>
      ),
    },
    {
      id: "team_verification",
      title: "Verified Team Members",
      icon: Users,
      description: "Add and verify team members on the blockchain",
      issue: !startup?.employees_verified || startup.employees_verified === 0,
      action: (
        <TeamMemberManager startup={startup} onUpdate={onUpdate} />
      ),
    },
    {
      id: "contact_info",
      title: "Complete Contact Information",
      icon: Mail,
      description: "Ensure all contact details are complete",
      issue: !startup?.contact_email || !startup?.website || !startup?.address,
      action: (
        <div className="space-y-3">
          <input
            type="email"
            value={formData.contact_email}
            onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="Contact email"
            onBlur={() => formData.contact_email && handleUpdate({ contact_email: formData.contact_email })}
          />
          <input
            type="url"
            value={formData.website}
            onChange={(e) => setFormData({ ...formData, website: e.target.value })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="Website URL"
            onBlur={() => formData.website && handleUpdate({ website: formData.website })}
          />
          <textarea
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="Business address"
            rows="2"
            onBlur={() => formData.address && handleUpdate({ address: formData.address })}
          />
        </div>
      ),
    },
    {
      id: "business_registration",
      title: "Business Registration",
      icon: Building2,
      description: "Provide link to your business registration documents",
      issue: !startup?.business_registration_verified,
      action: (
        <div className="space-y-2">
          <input
            type="url"
            value={formData.registration_doc_url || ""}
            onChange={(e) => setFormData({ ...formData, registration_doc_url: e.target.value })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="https://link-to-registration-documents.com or Google Drive/Dropbox link"
          />
          <p className="text-xs text-slate-600 font-medium">Provide a link to your business registration documents (PDF, Google Drive, etc.)</p>
          <button
            onClick={() => {
              if (!formData.registration_doc_url || !formData.registration_doc_url.trim()) {
                toast.error("Please provide a link to your registration documents first");
                return;
              }
              handleUpdate({
                business_registration_verified: true,
                documents_url: formData.registration_doc_url
              });
            }}
            disabled={loading || !formData.registration_doc_url?.trim()}
            className="w-full px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? "Verifying..." : "Verify Business Registration"}
          </button>
        </div>
      ),
    },
    {
      id: "founder_profile",
      title: "Founder Profile Verification",
      icon: UserCheck,
      description: "Provide link to your verified professional profile",
      issue: !startup?.founder_profile_verified,
      action: (
        <div className="space-y-2">
          <input
            type="url"
            value={formData.founder_profile_url || ""}
            onChange={(e) => setFormData({ ...formData, founder_profile_url: e.target.value })}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-500 font-medium"
            placeholder="https://linkedin.com/in/yourprofile or professional profile link"
          />
          <p className="text-xs text-slate-600 font-medium">Provide a link to your verified LinkedIn or professional profile</p>
          <button
            onClick={() => {
              if (!formData.founder_profile_url || !formData.founder_profile_url.trim()) {
                toast.error("Please provide a link to your professional profile first");
                return;
              }
              handleUpdate({ founder_profile_verified: true });
            }}
            disabled={loading || !formData.founder_profile_url?.trim()}
            className="w-full px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? "Verifying..." : "Verify Founder Profile"}
          </button>
        </div>
      ),
    },
  ].filter((item) => item.issue); // Only show items that need improvement

  if (improvementItems.length === 0) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-8 h-8 text-emerald-600" />
          <div>
            <h3 className="text-xl font-bold text-slate-900">All Good! 🎉</h3>
            <p className="text-slate-700">Your startup profile is complete and credible!</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="card bg-gradient-to-r from-sky-50 to-amber-50 border border-sky-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-sky-600" />
          Improve Your Credibility Score
        </h3>
        <p className="text-slate-700 text-sm mb-4 font-semibold">
          Current Score: <span className="font-bold text-slate-900 text-lg">{startup?.credibility_score?.toFixed(1) || 0}%</span>
        </p>
        <p className="text-slate-600 text-sm">
          Complete the following items to boost your credibility and attract more investors:
        </p>
      </div>

      {improvementItems.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.id}
            className="card bg-white border-2 border-slate-300 rounded-lg p-6 shadow-md"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-red-100 rounded-lg flex-shrink-0">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-5 h-5 text-slate-900 flex-shrink-0" />
                  <h4 className="text-lg font-bold text-slate-900 leading-tight">{item.title}</h4>
                </div>
                <p className="text-slate-700 text-sm mb-4 font-semibold leading-relaxed">{item.description}</p>
                {item.id === "team_verification" && (
                  <h5 className="text-base font-bold text-gray-900 mb-3 mt-4" style={{ color: '#000', fontWeight: 700 }}>
                    Team Members
                  </h5>
                )}
                <div className="mt-4">
                  {item.action}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
