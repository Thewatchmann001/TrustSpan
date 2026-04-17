import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import { employerAPI, cvAPI } from "../lib/api";
import toast from "react-hot-toast";
import { Search, Users, Star, MapPin, Briefcase, Filter, ShieldCheck, X, GraduationCap, Award, Mail, Phone, Calendar } from "lucide-react";
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
    location: "",
    education: "",
    qualifications: ""
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("search");
  const [selectedCV, setSelectedCV] = useState(null);
  const [skillsInput, setSkillsInput] = useState("");

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
      const skills = skillsInput.split(",").map(s => s.trim()).filter(s => s !== "");
      const response = await cvAPI.search({ ...searchParams, skills });
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
                  <label className="text-xs font-bold text-gray-400 uppercase">Skills (comma separated)</label>
                  <input className="input mt-1" placeholder="e.g. React, Python, SQL" value={skillsInput} onChange={e => setSkillsInput(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase">Education</label>
                  <input className="input mt-1" placeholder="e.g. Computer Science" value={searchParams.education} onChange={e => setSearchParams({...searchParams, education: e.target.value})} />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase">Qualifications</label>
                  <input className="input mt-1" placeholder="e.g. AWS Certified" value={searchParams.qualifications} onChange={e => setSearchParams({...searchParams, qualifications: e.target.value})} />
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
                        <button onClick={() => setSelectedCV(cv)} className="btn-secondary flex-1 text-sm py-2">View Profile</button>
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

      {selectedCV && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
            <div className="px-8 py-6 border-b flex justify-between items-center bg-slate-50">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl">{selectedCV.name[0]}</div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">{selectedCV.name}</h2>
                  <p className="text-blue-600 font-medium">{selectedCV.match_score}% Match</p>
                </div>
              </div>
              <button onClick={() => setSelectedCV(null)} className="p-2 hover:bg-slate-200 rounded-full transition-colors"><X size={24} className="text-slate-500" /></button>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-8">
              {selectedCV.summary && (
                <section>
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-3">Professional Summary</h3>
                  <p className="text-slate-700 leading-relaxed bg-blue-50/50 p-4 rounded-xl border border-blue-100">{selectedCV.summary}</p>
                </section>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <section className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><Briefcase size={16} /> Work Experience</h3>
                  <div className="space-y-6">
                    {selectedCV.work_experience?.map((exp, idx) => (
                      <div key={idx} className="relative pl-6 border-l-2 border-slate-100">
                        <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-2 border-blue-600" />
                        <h4 className="font-bold text-slate-900">{exp.job_title || exp.title}</h4>
                        <p className="text-sm text-slate-500 font-medium">{exp.company || exp.employer}</p>
                        <p className="text-xs text-slate-400 mb-2">{exp.start_date} - {exp.end_date || 'Present'}</p>
                        <p className="text-sm text-slate-600">{exp.description}</p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><GraduationCap size={18} /> Education</h3>
                  <div className="space-y-6">
                    {selectedCV.education?.map((edu, idx) => (
                      <div key={idx} className="relative pl-6 border-l-2 border-slate-100">
                        <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-2 border-green-600" />
                        <h4 className="font-bold text-slate-900">{edu.degree || edu.qualification}</h4>
                        <p className="text-sm text-slate-500 font-medium">{edu.institution || edu.school}</p>
                        <p className="text-xs text-slate-400">{edu.year || edu.end_date}</p>
                      </div>
                    ))}
                  </div>
                </section>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
                <section className="space-y-3">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Skills</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedCV.skills?.map((skill, idx) => (
                      <span key={idx} className="px-3 py-1 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium">{skill}</span>
                    ))}
                  </div>
                </section>

                <section className="space-y-3">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><Award size={16} /> Certifications</h3>
                  <div className="space-y-2">
                    {selectedCV.certifications?.map((cert, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm text-slate-700 bg-amber-50 p-2 rounded-lg border border-amber-100">
                        <Award size={14} className="text-amber-600" />
                        <span className="font-medium">{cert.name || cert.title}</span>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </div>

            <div className="p-6 border-t bg-slate-50 flex justify-end gap-3">
              <button onClick={() => setSelectedCV(null)} className="px-6 py-2 rounded-xl font-bold text-slate-600 hover:bg-slate-200 transition-colors">Close</button>
              <button onClick={() => { handleShortlist(selectedCV.cv_id); setSelectedCV(null); }} className="btn-primary px-8">Shortlist Candidate</button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
