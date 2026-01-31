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
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 mb-2" style={{ color: '#000', fontWeight: 700 }}>Team Members</h3>
          <p className="text-gray-700 text-sm font-semibold">
            Current verified team members: <span className="font-bold text-gray-900 text-base">{startup?.employees_verified || 0}</span>
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 rounded-lg hover:from-sky-700 hover:to-indigo-700 text-sm font-bold flex items-center gap-2 transition-all shadow-md"
          style={{ fontWeight: 700, color: '#ffffff', backgroundColor: '#2563eb' }}
        >
          <Plus className="w-4 h-4" style={{ color: '#ffffff', strokeWidth: 2.5 }} />
          <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '14px' }}>Add Member</span>
        </button>
      </div>

      {showAddForm && (
        <div className="card bg-white border-2 border-slate-300 rounded-lg p-6 space-y-4 shadow-md">
          <h4 className="text-xl font-bold text-gray-900 mb-4" style={{ color: '#000', fontWeight: 700 }}>Add Team Member</h4>
          
          <div>
            <label className="block text-sm font-bold mb-2" style={{ color: '#000', fontWeight: 700 }}>Full Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border-2 border-slate-300 rounded-lg font-medium"
              style={{ color: '#000' }}
              placeholder="Enter full name"
            />
          </div>
          
          <div>
            <label className="block text-sm font-bold mb-2" style={{ color: '#000', fontWeight: 700 }}>Email Address *</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border-2 border-slate-300 rounded-lg font-medium"
              style={{ color: '#000' }}
              placeholder="Enter email address"
            />
          </div>
          
          <div>
            <label className="block text-sm font-bold mb-2" style={{ color: '#000', fontWeight: 700 }}>Role/Position *</label>
            <input
              type="text"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border-2 border-slate-300 rounded-lg font-medium"
              style={{ color: '#000' }}
              placeholder="e.g., CTO, Developer, Designer"
            />
          </div>
          
          <div>
            <label className="block text-sm font-bold mb-2" style={{ color: '#000', fontWeight: 700 }}>
              Solana Wallet Address <span style={{ color: '#6b7280', fontWeight: 400 }}>(optional)</span>
            </label>
            <input
              type="text"
              value={formData.wallet_address}
              onChange={(e) => setFormData({ ...formData, wallet_address: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border-2 border-slate-300 rounded-lg font-mono text-sm"
              style={{ color: '#000' }}
              placeholder="For on-chain verification"
            />
          </div>
          
          <div>
            <label className="block text-sm font-bold mb-2" style={{ color: '#000', fontWeight: 700 }}>
              Certificate ID <span style={{ color: '#6b7280', fontWeight: 400 }}>(optional)</span>
            </label>
            <input
              type="text"
              value={formData.certificate_id}
              onChange={(e) => setFormData({ ...formData, certificate_id: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border-2 border-slate-300 rounded-lg font-medium"
              style={{ color: '#000' }}
              placeholder="If employee has verified certificate"
            />
          </div>
          
          <p className="text-xs font-medium bg-slate-50 border-2 border-slate-200 rounded-lg p-3" style={{ color: '#374151' }}>
            💡 For on-chain verification, provide the employee's Solana wallet address. 
            If they have a verified certificate, include the certificate ID.
          </p>
          
          <div className="flex gap-2 pt-2">
            <button
              onClick={handleAddEmployee}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-gradient-to-r from-emerald-600 to-green-600 rounded-lg hover:from-emerald-700 hover:to-green-700 disabled:opacity-50 flex items-center justify-center gap-2 font-bold transition-all"
              style={{ color: '#ffffff', fontWeight: 700 }}
            >
              {loading ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" style={{ color: '#ffffff' }} />
                  <span style={{ color: '#ffffff' }}>Adding...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" style={{ color: '#ffffff' }} />
                  <span style={{ color: '#ffffff' }}>Add Member</span>
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
              className="px-4 py-2 bg-slate-500 rounded-lg hover:bg-slate-600 font-bold transition-colors"
              style={{ color: '#ffffff', fontWeight: 700 }}
            >
              <XCircle className="w-4 h-4" style={{ color: '#ffffff' }} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
