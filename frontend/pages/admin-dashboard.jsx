import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import { adminAPI } from "../utils/api";
import toast from "react-hot-toast";
import { Users, FileText, Building2, CheckCircle, XCircle, Shield, BarChart3, Eye } from "lucide-react";
import { motion } from "framer-motion";
import Logo from "../components/Logo";

export default function AdminDashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState(null);
  const [employers, setEmployers] = useState([]);
  const [usersList, setUsersList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("stats");
  const [rejectionReason, setRejectionReason] = useState("");
  const [selectedEmployer, setSelectedEmployer] = useState(null);

  const SUPERADMIN_EMAIL = "josephemsamah@gmail.com";
  const isAdmin = user?.role === "admin" || user?.email === SUPERADMIN_EMAIL;

  useEffect(() => {
    if (!isAdmin) {
      router.push("/");
      return;
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, empRes, userRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.listEmployers(),
        adminAPI.listUsers()
      ]);
      setStats(statsRes.data);
      setEmployers(empRes.data);
      setUsersList(userRes.data);
    } catch (err) {
      toast.error("Failed to load admin data");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      await adminAPI.approveEmployer(id);
      toast.success("Employer approved!");
      loadData();
    } catch (err) {
      toast.error("Approval failed");
    }
  };

  const handleReject = async () => {
    if (!rejectionReason) return toast.error("Please provide a reason");
    try {
      await adminAPI.rejectEmployer(selectedEmployer.id, rejectionReason);
      toast.success("Employer rejected");
      setSelectedEmployer(null);
      setRejectionReason("");
      loadData();
    } catch (err) {
      toast.error("Rejection failed");
    }
  };

  if (!isAdmin) return null;
  if (loading) return <div className="p-12 text-center text-gray-500">Loading admin panel...</div>;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-slate-900 text-white px-8 py-6 shadow-xl">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
             <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-xl">A</div>
             <h1 className="text-2xl font-bold tracking-tight">Admin Control Panel</h1>
          </div>
          <div className="flex bg-slate-800 rounded-lg p-1">
             <button onClick={() => setActiveTab("stats")} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === "stats" ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}>Overview</button>
             <button onClick={() => setActiveTab("employers")} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === "employers" ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}>Applications</button>
             <button onClick={() => setActiveTab("users")} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === "users" ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}>Users</button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-8">
        {activeTab === "stats" && stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
             <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 flex items-center gap-6">
                <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center"><Users size={32} /></div>
                <div><p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Total Users</p><p className="text-4xl font-black text-slate-900">{stats.total_users}</p></div>
             </div>
             <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 flex items-center gap-6">
                <div className="w-16 h-16 bg-purple-50 text-purple-600 rounded-2xl flex items-center justify-center"><FileText size={32} /></div>
                <div><p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Total CVs</p><p className="text-4xl font-black text-slate-900">{stats.total_cvs}</p></div>
             </div>
             <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 flex items-center gap-6">
                <div className="w-16 h-16 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center"><Building2 size={32} /></div>
                <div><p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Employers</p><p className="text-4xl font-black text-slate-900">{stats.total_employers}</p></div>
             </div>

             {/* Pending Applications Banner */}
             {stats.pending_employers > 0 && (
               <div className="md:col-span-3 bg-amber-50 border border-amber-200 p-6 rounded-3xl flex justify-between items-center">
                  <div className="flex items-center gap-4">
                     <div className="w-12 h-12 bg-amber-200 text-amber-800 rounded-full flex items-center justify-center font-bold">{stats.pending_employers}</div>
                     <div><p className="font-bold text-amber-900">Pending Employer Applications</p><p className="text-sm text-amber-700">New companies are waiting for your review.</p></div>
                  </div>
                  <button onClick={() => setActiveTab("employers")} className="bg-amber-200 text-amber-900 px-6 py-2 rounded-xl font-bold hover:bg-amber-300 transition-colors">Review Now</button>
               </div>
             )}
          </div>
        )}

        {activeTab === "employers" && (
          <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
             <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-100">
                   <tr>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Company</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Industry</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Status</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Date</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Actions</th>
                   </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                   {employers.map((emp, i) => (
                     <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4">
                           <p className="font-bold text-slate-900">{emp.company_name}</p>
                           <p className="text-xs text-slate-500">{emp.contact_email}</p>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-600">{emp.industry}</td>
                        <td className="px-6 py-4">
                           <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${emp.status === "approved" ? "bg-green-100 text-green-700" : emp.status === "pending" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>{emp.status}</span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-500">{new Date(emp.applied_at).toLocaleDateString()}</td>
                        <td className="px-6 py-4">
                           <div className="flex gap-2">
                              {emp.status === "pending" && (
                                <>
                                   <button onClick={() => handleApprove(emp.id)} className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100"><CheckCircle size={18} /></button>
                                   <button onClick={() => setSelectedEmployer(emp)} className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100"><XCircle size={18} /></button>
                                </>
                              )}
                              <button className="p-2 bg-slate-50 text-slate-600 rounded-lg hover:bg-slate-100"><Eye size={18} /></button>
                           </div>
                        </td>
                     </tr>
                   ))}
                </tbody>
             </table>
          </div>
        )}

        {activeTab === "users" && (
          <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
             <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-100">
                   <tr>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">User</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Role</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">CV Status</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Join Date</th>
                   </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                   {usersList.map((u, i) => (
                     <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4">
                           <p className="font-bold text-slate-900">{u.full_name}</p>
                           <p className="text-xs text-slate-500">{u.email}</p>
                        </td>
                        <td className="px-6 py-4"><span className="text-xs font-bold bg-slate-100 px-2 py-1 rounded text-slate-600 uppercase tracking-tighter">{u.role}</span></td>
                        <td className="px-6 py-4">{u.has_cv ? <span className="text-green-600 flex items-center gap-1 text-sm font-medium"><CheckCircle size={14} /> Created</span> : <span className="text-slate-400 text-sm font-medium">No CV</span>}</td>
                        <td className="px-6 py-4 text-sm text-slate-500">{new Date(u.created_at).toLocaleDateString()}</td>
                     </tr>
                   ))}
                </tbody>
             </table>
          </div>
        )}
      </main>

      {/* Rejection Modal */}
      {selectedEmployer && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-6 z-50">
           <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl space-y-6">
              <h3 className="text-xl font-bold text-slate-900">Reject Application</h3>
              <p className="text-sm text-slate-500">Provide a reason for rejecting <b>{selectedEmployer.company_name}</b>. This will be visible to them.</p>
              <textarea className="input min-h-[100px]" placeholder="Reason for rejection..." value={rejectionReason} onChange={e => setRejectionReason(e.target.value)} />
              <div className="flex gap-3 pt-4">
                 <button onClick={() => setSelectedEmployer(null)} className="btn-secondary flex-1">Cancel</button>
                 <button onClick={handleReject} className="btn-primary flex-1 bg-red-600 hover:bg-red-700">Confirm Reject</button>
              </div>
           </motion.div>
        </div>
      )}
    </div>
  );
}
