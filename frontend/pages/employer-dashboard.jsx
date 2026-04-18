import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import { employerAPI, cvAPI } from "../utils/api";
import toast from "react-hot-toast";
import { Search, Users, Star, MapPin, Briefcase, Filter, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import Logo from "../components/Logo";

export default function EmployerDashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [employer, setEmployer] = useState(null);
  const [searchParams, setSearchParams] = useState({
    job_title: "",
    skills: [],
    experience_level: "Mid",
    location: ""
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("search");

  useEffect(() => {
    if (user?.role !== "employer" && user?.active_role !== "employer") {
      router.push("/");
      return;
    }
    loadEmployerData();
  }, [user]);

  const loadEmployerData = async () => {
    try {
      const response = await employerAPI.getMe();
      setEmployer(response.data);
      if (response.data.status !== "approved") {
        toast.error("Your employer account is pending approval.");
      }
    } catch (err) {
      toast.error("Failed to load employer profile");
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await cvAPI.search(searchParams);
      setResults(response.data);
    } catch (err) {
      toast.error("Search failed");
    } finally {
      setLoading(false);
    }
  };

  const handleShortlist = async (cvId) => {
    try {
      await employerAPI.shortlist(cvId);
      toast.success("Candidate shortlisted!");
    } catch (err) {
      toast.error("Action failed");
    }
  };

  if (!employer) return <div className="p-12 text-center">Loading dashboard...</div>;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-8 py-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
             {employer.logo_url ? <img src={employer.logo_url} className="w-12 h-12 rounded-lg" /> : <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 font-bold text-xl">{employer.company_name[0]}</div>}
             <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  {employer.company_name}
                  {employer.status === "approved" && <ShieldCheck className="text-green-500" size={20} />}
                </h1>
                <p className="text-gray-500 text-sm">{employer.industry} • {employer.company_size} employees</p>
             </div>
          </div>
          <div className="flex gap-2">
             <button onClick={() => setActiveTab("search")} className={`px-4 py-2 rounded-lg font-medium ${activeTab === "search" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600"}`}>CV Search</button>
             <button onClick={() => setActiveTab("shortlist")} className={`px-4 py-2 rounded-lg font-medium ${activeTab === "shortlist" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600"}`}>Shortlisted</button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-8">
        {activeTab === "search" ? (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Sidebar Filters */}
            <aside className="space-y-6">
              <div className="bg-white p-6 rounded-2xl shadow-sm border space-y-4">
                <h3 className="font-bold flex items-center gap-2"><Filter size={18} /> Search Criteria</h3>
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase">Job Title</label>
                  <input className="input mt-1" placeholder="e.g. Frontend Developer" value={searchParams.job_title} onChange={e => setSearchParams({...searchParams, job_title: e.target.value})} />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase">Experience</label>
                  <select className="input mt-1" value={searchParams.experience_level} onChange={e => setSearchParams({...searchParams, experience_level: e.target.value})}>
                    <option>Entry</option>
                    <option>Mid</option>
                    <option>Senior</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase">Location</label>
                  <input className="input mt-1" placeholder="e.g. Freetown" value={searchParams.location} onChange={e => setSearchParams({...searchParams, location: e.target.value})} />
                </div>
                <button onClick={handleSearch} disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                  {loading ? "Searching..." : <><Search size={18} /> Search with AI</>}
                </button>
              </div>
            </aside>

            {/* Results Grid */}
            <div className="lg:col-span-3 space-y-6">
               <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold">{results.length} Candidates Found</h2>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {results.map((cv, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-white p-6 rounded-2xl shadow-sm border hover:shadow-md transition-all relative overflow-hidden"
                    >
                      <div className="absolute top-0 right-0 bg-blue-600 text-white px-4 py-1 rounded-bl-xl font-bold">
                        {cv.match_score}% Match
                      </div>
                      <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center text-gray-400">
                          <Users size={24} />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg blur-sm select-none">{cv.name}</h3>
                          <div className="flex items-center gap-3 text-sm text-gray-500">
                             <span className="flex items-center gap-1"><Briefcase size={14} /> {cv.experience_years}y Experience</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 mb-4">
                         {cv.skills.slice(0, 4).map((s, idx) => (
                           <span key={idx} className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">{s}</span>
                         ))}
                      </div>
                      <p className="text-sm text-gray-600 italic mb-6">"{cv.match_reason}"</p>
                      <div className="flex gap-2">
                        <button className="btn-secondary flex-1 text-sm py-2">View Profile</button>
                        <button onClick={() => handleShortlist(cv.cv_id)} className="btn-primary flex-1 text-sm py-2 flex items-center justify-center gap-1">
                          <Star size={14} /> Shortlist
                        </button>
                      </div>
                    </motion.div>
                  ))}
               </div>

               {results.length === 0 && !loading && (
                 <div className="bg-white rounded-2xl border border-dashed p-12 text-center space-y-4">
                    <Search className="mx-auto text-gray-300" size={48} />
                    <p className="text-gray-500">No search results yet. Enter criteria and search with AI.</p>
                 </div>
               )}
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-gray-500">
             Shortlisted candidates will appear here.
          </div>
        )}
      </main>
    </div>
  );
}
