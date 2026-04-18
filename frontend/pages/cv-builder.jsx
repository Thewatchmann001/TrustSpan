import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import { cvAPI } from "../utils/api";
import toast from "react-hot-toast";
import {
  User, FileText, Briefcase, GraduationCap,
  Wand2, Download, Upload, Layout, ChevronRight, ChevronLeft,
  Plus, Trash2, CheckCircle2, X, Mail, Phone, MapPin, Linkedin, Globe
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Logo from "../components/Logo";

export default function CVBuilder() {
  const { user } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [cvData, setCvData] = useState({
    personal_info: {
      full_name: "",
      email: "",
      phone: "",
      location: "",
      linkedin: "",
      portfolio: "",
      photo_url: ""
    },
    summary: "",
    work_experience: [],
    education: [],
    skills: {
      technical: [],
      soft: [],
      languages: []
    },
    certifications: [],
    template_name: "Modern"
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    loadExistingCV();
  }, [user]);

  const loadExistingCV = async () => {
    try {
      const response = await cvAPI.getMe();
      if (response.data) {
        setCvData(response.data);
      }
    } catch (err) {
      console.log("No existing CV found or error loading");
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await cvAPI.save(cvData);
      toast.success("CV Saved Successfully!");
    } catch (err) {
      toast.error("Failed to save CV");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await cvAPI.exportPDF(cvData);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'my-cv.pdf');
      document.body.appendChild(link);
      link.click();
    } catch (err) {
      toast.error("Failed to export PDF");
    }
  };

  const handleAIEnhance = async (section, content) => {
    try {
      const response = await cvAPI.aiEnhance({ section, content });
      return response.data.enhanced_content;
    } catch (err) {
      toast.error("AI Enhancement failed");
      return content;
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    try {
      const response = await cvAPI.uploadParse(formData);
      setCvData(prev => ({ ...prev, ...response.data }));
      toast.success("CV Parsed Successfully!");
    } catch (err) {
      toast.error("Failed to parse CV");
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => setStep(s => Math.min(s + 1, 7));
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center sticky top-0 z-10">
        <Logo />
        <div className="flex items-center gap-4">
          <button onClick={handleSave} className="btn-secondary flex items-center gap-2">
            <FileText size={18} /> Save Draft
          </button>
          <button onClick={handleExport} className="btn-primary flex items-center gap-2">
            <Download size={18} /> Export PDF
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className="w-64 bg-white border-r p-4 hidden md:block">
          <nav className="space-y-1">
            {[
              { id: 1, label: "Personal Info", icon: User },
              { id: 2, label: "Summary", icon: FileText },
              { id: 3, label: "Work Experience", icon: Briefcase },
              { id: 4, label: "Education", icon: GraduationCap },
              { id: 5, label: "Skills", icon: Wand2 },
              { id: 6, label: "Certifications", icon: CheckCircle2 },
              { id: 7, label: "Template", icon: Layout },
            ].map(i => (
              <button
                key={i.id}
                onClick={() => setStep(i.id)}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  step === i.id ? "bg-blue-50 text-blue-600" : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <i.icon size={18} />
                {i.label}
              </button>
            ))}
          </nav>

          <div className="mt-8 pt-8 border-t">
             <label className="block text-xs font-semibold text-gray-500 uppercase mb-4">Import Existing</label>
             <div className="relative group">
                <input type="file" onChange={handleFileUpload} className="absolute inset-0 opacity-0 cursor-pointer" />
                <div className="border-2 border-dashed rounded-lg p-4 text-center group-hover:border-blue-400 transition-colors">
                  <Upload className="mx-auto text-gray-400 mb-2" />
                  <span className="text-xs text-gray-600">Upload PDF/DOCX</span>
                </div>
             </div>
          </div>
        </aside>

        {/* Form Area */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-3xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                {step === 1 && (
                  <section className="space-y-4">
                    <h2 className="text-2xl font-bold">Personal Information</h2>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="col-span-2">
                        <label className="label">Full Name</label>
                        <input
                          type="text"
                          className="input"
                          value={cvData.personal_info.full_name}
                          onChange={e => setCvData({...cvData, personal_info: {...cvData.personal_info, full_name: e.target.value}})}
                        />
                      </div>
                      <div>
                        <label className="label">Email</label>
                        <input type="email" className="input" value={cvData.personal_info.email}
                          onChange={e => setCvData({...cvData, personal_info: {...cvData.personal_info, email: e.target.value}})}
                        />
                      </div>
                      <div>
                        <label className="label">Phone</label>
                        <input type="text" className="input" value={cvData.personal_info.phone}
                          onChange={e => setCvData({...cvData, personal_info: {...cvData.personal_info, phone: e.target.value}})}
                        />
                      </div>
                    </div>
                  </section>
                )}

                {step === 2 && (
                  <section className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h2 className="text-2xl font-bold">Professional Summary</h2>
                      <button
                        onClick={async () => {
                          const enhanced = await handleAIEnhance("summary", cvData.summary || "Professional summary based on my experience");
                          setCvData({...cvData, summary: enhanced});
                        }}
                        className="btn-secondary text-xs flex items-center gap-1"
                      >
                        <Wand2 size={14} /> AI Generate
                      </button>
                    </div>
                    <textarea
                      className="input min-h-[150px]"
                      placeholder="Briefly describe your professional background and goals..."
                      value={cvData.summary}
                      onChange={e => setCvData({...cvData, summary: e.target.value})}
                    ></textarea>
                  </section>
                )}

                {step === 3 && (
                  <section className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h2 className="text-2xl font-bold">Work Experience</h2>
                      <button
                        onClick={() => setCvData({...cvData, work_experience: [...cvData.work_experience, {job_title: "", company: "", description: ""}]})}
                        className="btn-primary text-xs flex items-center gap-1"
                      >
                        <Plus size={14} /> Add Role
                      </button>
                    </div>
                    {cvData.work_experience.map((exp, idx) => (
                      <div key={idx} className="p-4 border rounded-xl space-y-4 relative group">
                        <button
                          onClick={() => {
                            const newExp = [...cvData.work_experience];
                            newExp.splice(idx, 1);
                            setCvData({...cvData, work_experience: newExp});
                          }}
                          className="absolute top-2 right-2 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 size={18} />
                        </button>
                        <div className="grid grid-cols-2 gap-4">
                          <input
                            placeholder="Job Title" className="input"
                            value={exp.job_title}
                            onChange={e => {
                              const newExp = [...cvData.work_experience];
                              newExp[idx].job_title = e.target.value;
                              setCvData({...cvData, work_experience: newExp});
                            }}
                          />
                          <input
                            placeholder="Company" className="input"
                            value={exp.company}
                            onChange={e => {
                              const newExp = [...cvData.work_experience];
                              newExp[idx].company = e.target.value;
                              setCvData({...cvData, work_experience: newExp});
                            }}
                          />
                          <div className="col-span-2 space-y-2">
                            <div className="flex justify-between items-center">
                              <label className="text-xs font-semibold">Description</label>
                              <button
                                onClick={async () => {
                                  const enhanced = await handleAIEnhance("experience", exp.description);
                                  const newExp = [...cvData.work_experience];
                                  newExp[idx].description = enhanced;
                                  setCvData({...cvData, work_experience: newExp});
                                }}
                                className="text-xs text-blue-600 flex items-center gap-1"
                              >
                                <Wand2 size={12} /> Enhance with AI
                              </button>
                            </div>
                            <textarea
                              className="input min-h-[100px]"
                              value={exp.description}
                              onChange={e => {
                                const newExp = [...cvData.work_experience];
                                newExp[idx].description = e.target.value;
                                setCvData({...cvData, work_experience: newExp});
                              }}
                            ></textarea>
                          </div>
                        </div>
                      </div>
                    ))}
                  </section>
                )}

                {step === 4 && (
                  <section className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h2 className="text-2xl font-bold">Education</h2>
                      <button
                        onClick={() => setCvData({...cvData, education: [...cvData.education, {degree: "", institution: "", year: "", grade: ""}]})}
                        className="btn-primary text-xs flex items-center gap-1"
                      >
                        <Plus size={14} /> Add Education
                      </button>
                    </div>
                    {cvData.education.map((edu, idx) => (
                      <div key={idx} className="p-4 border rounded-xl space-y-4 relative group">
                        <button
                          onClick={() => {
                            const newEdu = [...cvData.education];
                            newEdu.splice(idx, 1);
                            setCvData({...cvData, education: newEdu});
                          }}
                          className="absolute top-2 right-2 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 size={18} />
                        </button>
                        <div className="grid grid-cols-2 gap-4">
                          <input
                            placeholder="Degree" className="input"
                            value={edu.degree}
                            onChange={e => {
                              const newEdu = [...cvData.education];
                              newEdu[idx].degree = e.target.value;
                              setCvData({...cvData, education: newEdu});
                            }}
                          />
                          <input
                            placeholder="Institution" className="input"
                            value={edu.institution}
                            onChange={e => {
                              const newEdu = [...cvData.education];
                              newEdu[idx].institution = e.target.value;
                              setCvData({...cvData, education: newEdu});
                            }}
                          />
                          <input
                            placeholder="Year" className="input"
                            value={edu.year}
                            onChange={e => {
                              const newEdu = [...cvData.education];
                              newEdu[idx].year = e.target.value;
                              setCvData({...cvData, education: newEdu});
                            }}
                          />
                          <input
                            placeholder="Grade / GPA" className="input"
                            value={edu.grade}
                            onChange={e => {
                              const newEdu = [...cvData.education];
                              newEdu[idx].grade = e.target.value;
                              setCvData({...cvData, education: newEdu});
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </section>
                )}

                {step === 5 && (
                  <section className="space-y-6">
                    <h2 className="text-2xl font-bold">Skills</h2>
                    {["technical", "soft", "languages"].map(cat => (
                      <div key={cat} className="space-y-2">
                        <label className="label capitalize">{cat} Skills</label>
                        <div className="flex flex-wrap gap-2 mb-2">
                          {(cvData.skills[cat] || []).map((s, i) => (
                            <span key={i} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                              {s}
                              <X size={14} className="cursor-pointer" onClick={() => {
                                const newSkills = {...cvData.skills};
                                newSkills[cat].splice(i, 1);
                                setCvData({...cvData, skills: newSkills});
                              }} />
                            </span>
                          ))}
                        </div>
                        <input
                          placeholder={`Add ${cat} skill...`}
                          className="input"
                          onKeyDown={e => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              const val = e.target.value.trim();
                              if (val) {
                                const newSkills = {...cvData.skills};
                                if (!newSkills[cat]) newSkills[cat] = [];
                                newSkills[cat].push(val);
                                setCvData({...cvData, skills: newSkills});
                                e.target.value = "";
                              }
                            }
                          }}
                        />
                      </div>
                    ))}
                  </section>
                )}

                {step === 6 && (
                  <section className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h2 className="text-2xl font-bold">Certifications & Awards</h2>
                      <button
                        onClick={() => setCvData({...cvData, certifications: [...cvData.certifications, {name: "", issuer: "", year: ""}]})}
                        className="btn-primary text-xs flex items-center gap-1"
                      >
                        <Plus size={14} /> Add Item
                      </button>
                    </div>
                    {cvData.certifications.map((cert, idx) => (
                      <div key={idx} className="p-4 border rounded-xl space-y-4 relative group">
                        <button
                          onClick={() => {
                            const newCert = [...cvData.certifications];
                            newCert.splice(idx, 1);
                            setCvData({...cvData, certifications: newCert});
                          }}
                          className="absolute top-2 right-2 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 size={18} />
                        </button>
                        <div className="grid grid-cols-3 gap-4">
                          <input
                            placeholder="Name" className="input col-span-2"
                            value={cert.name}
                            onChange={e => {
                              const newCert = [...cvData.certifications];
                              newCert[idx].name = e.target.value;
                              setCvData({...cvData, certifications: newCert});
                            }}
                          />
                          <input
                            placeholder="Year" className="input"
                            value={cert.year}
                            onChange={e => {
                              const newCert = [...cvData.certifications];
                              newCert[idx].year = e.target.value;
                              setCvData({...cvData, certifications: newCert});
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </section>
                )}

                {step === 7 && (
                  <section className="space-y-6">
                    <h2 className="text-2xl font-bold">Select Template</h2>
                    <div className="grid grid-cols-3 gap-6">
                      {["Modern", "Classic", "ATS-Friendly"].map(t => (
                        <div
                          key={t}
                          onClick={() => setCvData({...cvData, template_name: t})}
                          className={`cursor-pointer border-2 rounded-xl p-4 text-center transition-all ${
                            cvData.template_name === t ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                          }`}
                        >
                          <div className="bg-gray-200 aspect-[1/1.414] rounded mb-3"></div>
                          <span className="font-semibold">{t}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                <div className="pt-8 flex justify-between border-t mt-12">
                  <button onClick={prevStep} disabled={step === 1} className="btn-secondary flex items-center gap-2">
                    <ChevronLeft size={18} /> Previous
                  </button>
                  <button onClick={nextStep} className="btn-primary flex items-center gap-2">
                    {step === 7 ? "Finish" : "Next Step"} <ChevronRight size={18} />
                  </button>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </main>

        {/* Live Preview */}
        <aside className="w-[450px] bg-gray-100 p-6 hidden lg:block overflow-y-auto border-l">
          <div className="sticky top-6">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Layout size={14} /> Live Preview: {cvData.template_name}
            </h3>

            <div className={`bg-white shadow-2xl rounded-sm aspect-[1/1.414] w-full p-8 origin-top transition-all duration-300 overflow-hidden ${
              cvData.template_name === "Classic" ? "font-serif" : "font-sans"
            }`} style={{ fontSize: '10px' }}>

              {/* MODERN TEMPLATE */}
              {cvData.template_name === "Modern" && (
                <div className="h-full flex flex-col">
                  <div className="bg-slate-800 -mx-8 -mt-8 p-6 text-white mb-6">
                    <h1 className="text-2xl font-bold tracking-tight mb-1">{cvData.personal_info.full_name || "YOUR NAME"}</h1>
                    <div className="flex flex-wrap gap-3 opacity-80 text-[8px]">
                      {cvData.personal_info.email && <span className="flex items-center gap-1"><Mail size={8} /> {cvData.personal_info.email}</span>}
                      {cvData.personal_info.phone && <span className="flex items-center gap-1"><Phone size={8} /> {cvData.personal_info.phone}</span>}
                      {cvData.personal_info.location && <span className="flex items-center gap-1"><MapPin size={8} /> {cvData.personal_info.location}</span>}
                    </div>
                  </div>

                  <div className="flex gap-6 flex-1">
                    <div className="flex-1 space-y-4">
                      <section>
                        <h2 className="text-[10px] font-bold text-slate-800 uppercase tracking-wider border-b-2 border-slate-800 mb-2">Profile</h2>
                        <p className="text-gray-600 leading-relaxed text-[9px]">{cvData.summary || "Add a summary to highlight your key achievements."}</p>
                      </section>

                      <section>
                        <h2 className="text-[10px] font-bold text-slate-800 uppercase tracking-wider border-b-2 border-slate-800 mb-2">Experience</h2>
                        <div className="space-y-3">
                          {cvData.work_experience.length > 0 ? cvData.work_experience.map((e, i) => (
                            <div key={i}>
                              <div className="flex justify-between font-bold text-slate-700">
                                <span>{e.job_title || "Job Title"}</span>
                                <span className="text-slate-500 font-normal">{e.company || "Company"}</span>
                              </div>
                              <p className="text-[8px] text-gray-500 mt-0.5 leading-relaxed">{e.description}</p>
                            </div>
                          )) : <p className="text-gray-400 italic">No experience added yet.</p>}
                        </div>
                      </section>
                    </div>

                    <div className="w-32 space-y-4">
                      <section>
                        <h2 className="text-[10px] font-bold text-slate-800 uppercase tracking-wider border-b-2 border-slate-800 mb-2">Skills</h2>
                        <div className="flex flex-wrap gap-1">
                          {Object.values(cvData.skills).flat().map((s, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded text-[7px]">{s}</span>
                          ))}
                        </div>
                      </section>
                      <section>
                        <h2 className="text-[10px] font-bold text-slate-800 uppercase tracking-wider border-b-2 border-slate-800 mb-2">Education</h2>
                        {cvData.education.map((edu, i) => (
                          <div key={i} className="mb-2">
                            <p className="font-bold text-slate-700 text-[8px]">{edu.degree}</p>
                            <p className="text-slate-500 text-[7px]">{edu.institution}</p>
                            <p className="text-slate-400 text-[7px]">{edu.year}</p>
                          </div>
                        ))}
                      </section>
                    </div>
                  </div>
                </div>
              )}

              {/* CLASSIC TEMPLATE */}
              {cvData.template_name === "Classic" && (
                <div className="text-center space-y-4">
                  <header className="border-b-2 border-gray-900 pb-2">
                    <h1 className="text-2xl font-bold uppercase tracking-widest mb-1">{cvData.personal_info.full_name || "YOUR NAME"}</h1>
                    <p className="text-[9px] text-gray-600">
                      {cvData.personal_info.email} • {cvData.personal_info.phone} • {cvData.personal_info.location}
                    </p>
                  </header>

                  <div className="text-left space-y-4">
                    <section>
                      <h2 className="text-[11px] font-bold border-b border-gray-300 mb-1">PROFESSIONAL SUMMARY</h2>
                      <p className="text-[9px] text-gray-800">{cvData.summary}</p>
                    </section>

                    <section>
                      <h2 className="text-[11px] font-bold border-b border-gray-300 mb-1">EXPERIENCE</h2>
                      {cvData.work_experience.map((e, i) => (
                        <div key={i} className="mb-2">
                          <div className="flex justify-between font-bold">
                            <span>{e.company}</span>
                            <span className="font-normal">Freetown, SL</span>
                          </div>
                          <div className="flex justify-between italic text-[9px]">
                            <span>{e.job_title}</span>
                            <span className="font-normal">2020 - Present</span>
                          </div>
                          <p className="text-[9px] text-gray-700 mt-1">{e.description}</p>
                        </div>
                      ))}
                    </section>

                    <section>
                      <h2 className="text-[11px] font-bold border-b border-gray-300 mb-1">EDUCATION</h2>
                      {cvData.education.map((edu, i) => (
                        <div key={i} className="flex justify-between text-[9px]">
                          <span><strong>{edu.institution}</strong>, {edu.degree}</span>
                          <span>{edu.year}</span>
                        </div>
                      ))}
                    </section>
                  </div>
                </div>
              )}

              {/* ATS-FRIENDLY TEMPLATE */}
              {cvData.template_name === "ATS-Friendly" && (
                <div className="space-y-4 font-mono text-gray-900">
                  <header>
                    <h1 className="text-xl font-bold">{cvData.personal_info.full_name || "YOUR NAME"}</h1>
                    <p className="text-[9px]">Email: {cvData.personal_info.email} | Phone: {cvData.personal_info.phone}</p>
                    <p className="text-[9px]">Location: {cvData.personal_info.location}</p>
                  </header>

                  <section>
                    <h2 className="text-[10px] font-bold border-b border-black uppercase">Professional Summary</h2>
                    <p className="text-[9px] mt-1">{cvData.summary}</p>
                  </section>

                  <section>
                    <h2 className="text-[10px] font-bold border-b border-black uppercase">Experience</h2>
                    {cvData.work_experience.map((e, i) => (
                      <div key={i} className="mt-2">
                        <p className="font-bold text-[9px]">{e.company} | {e.job_title}</p>
                        <p className="text-[9px] mt-0.5">{e.description}</p>
                      </div>
                    ))}
                  </section>

                  <section>
                    <h2 className="text-[10px] font-bold border-b border-black uppercase">Skills</h2>
                    <p className="text-[9px] mt-1">
                      {Object.values(cvData.skills).flat().join(", ")}
                    </p>
                  </section>

                  <section>
                    <h2 className="text-[10px] font-bold border-b border-black uppercase">Education</h2>
                    {cvData.education.map((edu, i) => (
                      <div key={i} className="mt-1">
                        <p className="text-[9px]">{edu.institution} - {edu.degree} ({edu.year})</p>
                      </div>
                    ))}
                  </section>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
