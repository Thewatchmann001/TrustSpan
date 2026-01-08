/**
 * Team Member Manager Component
 * Allows founders to add team members with blockchain verification
 */
import { useState } from "react";
import { Users, Plus, CheckCircle, XCircle, Loader } from "lucide-react";
import toast from "react-hot-toast";

export default function TeamMemberManager({ startup, onUpdate }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    role: "",
    wallet_address: "",
    certificate_id: "", // Optional: if employee has a verified certificate
  });

  const handleAddEmployee = async () => {
    if (!formData.name || !formData.email || !formData.role) {
      toast.error("Please fill in name, email, and role");
      return;
    }

    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      
      // First, add employee to database
      const response = await fetch(
        `${apiUrl}/api/startups/${startup.startup_id}/add-employee`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: formData.name,
            email: formData.email,
            role: formData.role,
            wallet_address: formData.wallet_address || null,
            certificate_id: formData.certificate_id || null,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to add employee");
      }

      const data = await response.json();
      toast.success(`✅ ${formData.name} added successfully! ${data.verified_on_chain ? '(Verified on blockchain)' : ''}`);
      
      // Reset form
      setFormData({
        name: "",
        email: "",
        role: "",
        wallet_address: "",
        certificate_id: "",
      });
      setShowAddForm(false);
      
      // Refresh startup data to get updated employees_verified count
      if (onUpdate) {
        await onUpdate();
      }
    } catch (error) {
      toast.error(error.message || "Failed to add team member");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-white/80 text-sm">
          Current verified team members: <span className="font-bold text-white">{startup?.employees_verified || 0}</span>
        </p>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Member
        </button>
      </div>

      {showAddForm && (
        <div className="bg-white/5 border border-white/20 rounded-lg p-4 space-y-3">
          <h4 className="text-white font-semibold">Add Team Member</h4>
          
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
            placeholder="Full Name *"
          />
          
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
            placeholder="Email Address *"
          />
          
          <input
            type="text"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
            placeholder="Role/Position * (e.g., CTO, Developer, Designer)"
          />
          
          <input
            type="text"
            value={formData.wallet_address}
            onChange={(e) => setFormData({ ...formData, wallet_address: e.target.value })}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 font-mono text-sm"
            placeholder="Solana Wallet Address (optional, for on-chain verification)"
          />
          
          <input
            type="text"
            value={formData.certificate_id}
            onChange={(e) => setFormData({ ...formData, certificate_id: e.target.value })}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
            placeholder="Certificate ID (optional, if employee has verified certificate)"
          />
          
          <p className="text-xs text-white/60">
            💡 For on-chain verification, provide the employee's Solana wallet address. 
            If they have a verified certificate, include the certificate ID.
          </p>
          
          <div className="flex gap-2">
            <button
              onClick={handleAddEmployee}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Add Member
                </>
              )}
            </button>
            <button
              onClick={() => {
                setShowAddForm(false);
                setFormData({
                  name: "",
                  email: "",
                  role: "",
                  wallet_address: "",
                  certificate_id: "",
                });
              }}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
