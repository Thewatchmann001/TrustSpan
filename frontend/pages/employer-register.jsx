import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import { employerAPI } from "../lib/api";
import toast from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { Building2, User, FileCheck, CheckCircle2, ChevronRight, ChevronLeft, Upload } from "lucide-react";
import Logo from "../components/Logo";

export default function EmployerRegister() {
  const { user } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    company_name: "",
    registration_number: "",
    industry: "Technology",
    company_size: "1-10",
    website: "",
    country: "Sierra Leone",
    city: "",
    contact_name: "",
    contact_title: "",
    contact_email: "",
    contact_phone: "",
    hiring_description: "",
    certificate_url: "",
    logo_url: ""
  });

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await employerAPI.apply(formData);
      toast.success("Application submitted successfully! Our team will review it.");
      router.push("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Application failed");
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-6">
      <Logo size="large" className="mb-12" />

      <div className="max-w-3xl w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex justify-between mb-12 relative">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className={`flex flex-col items-center z-10 ${step >= i ? "text-blue-600" : "text-gray-400"}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold mb-2 ${step >= i ? "bg-blue-600 text-white" : "bg-gray-200"}`}>
                {step > i ? <CheckCircle2 size={20} /> : i}
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider">
                {i === 1 && "Company"}
                {i === 2 && "Contact"}
                {i === 3 && "Documents"}
                {i === 4 && "Review"}
              </span>
            </div>
          ))}
          <div className="absolute top-5 left-0 w-full h-0.5 bg-gray-200 -z-0"></div>
          <div className="absolute top-5 left-0 h-0.5 bg-blue-600 transition-all duration-300 -z-0" style={{ width: `${(step - 1) * 33.33}%` }}></div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {step === 1 && (
              <div className="grid grid-cols-2 gap-6">
                <div className="col-span-2">
                  <label className="label">Company Name</label>
                  <input className="input" value={formData.company_name} onChange={e => setFormData({...formData, company_name: e.target.value})} />
                </div>
                <div>
                  <label className="label">Registration Number</label>
                  <input className="input" value={formData.registration_number} onChange={e => setFormData({...formData, registration_number: e.target.value})} />
                </div>
                <div>
                  <label className="label">Industry</label>
                  <select className="input" value={formData.industry} onChange={e => setFormData({...formData, industry: e.target.value})}>
                    <option>Technology</option>
                    <option>Healthcare</option>
                    <option>Finance</option>
                    <option>Education</option>
                    <option>Manufacturing</option>
                  </select>
                </div>
                <div>
                  <label className="label">Company Size</label>
                  <select className="input" value={formData.company_size} onChange={e => setFormData({...formData, company_size: e.target.value})}>
                    <option>1-10</option>
                    <option>11-50</option>
                    <option>51-200</option>
                    <option>200+</option>
                  </select>
                </div>
                <div>
                  <label className="label">Website URL</label>
                  <input className="input" value={formData.website} onChange={e => setFormData({...formData, website: e.target.value})} />
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="grid grid-cols-2 gap-6">
                <div className="col-span-2">
                  <label className="label">Full Name</label>
                  <input className="input" value={formData.contact_name} onChange={e => setFormData({...formData, contact_name: e.target.value})} />
                </div>
                <div>
                  <label className="label">Job Title</label>
                  <input className="input" value={formData.contact_title} onChange={e => setFormData({...formData, contact_title: e.target.value})} />
                </div>
                <div>
                  <label className="label">Work Email</label>
                  <input className="input" type="email" value={formData.contact_email} onChange={e => setFormData({...formData, contact_email: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <label className="label">Phone Number</label>
                  <input className="input" value={formData.contact_phone} onChange={e => setFormData({...formData, contact_phone: e.target.value})} />
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <label className="label">Business Registration Certificate</label>
                  <div className="border-2 border-dashed rounded-xl p-8 text-center hover:border-blue-500 transition-colors cursor-pointer bg-gray-50">
                    <Upload className="mx-auto text-gray-400 mb-2" />
                    <p className="text-sm text-gray-600">Click to upload PDF or Image</p>
                  </div>
                </div>
                <div>
                  <label className="label">Briefly describe your hiring needs</label>
                  <textarea className="input min-h-[120px]" value={formData.hiring_description} onChange={e => setFormData({...formData, hiring_description: e.target.value})} />
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-6">
                <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
                  <h3 className="font-bold text-blue-900 mb-4 flex items-center gap-2">
                    <CheckCircle2 size={20} /> Review Details
                  </h3>
                  <div className="grid grid-cols-2 gap-y-3 text-sm">
                    <span className="text-gray-500">Company:</span>
                    <span className="font-semibold">{formData.company_name}</span>
                    <span className="text-gray-500">Industry:</span>
                    <span className="font-semibold">{formData.industry}</span>
                    <span className="text-gray-500">Contact:</span>
                    <span className="font-semibold">{formData.contact_name} ({formData.contact_title})</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 text-center">
                  By submitting, you agree to TrustSpan Sierra Leone's Terms of Service for Employers.
                </p>
              </div>
            )}

            <div className="flex justify-between pt-8">
              <button
                onClick={prevStep}
                disabled={step === 1}
                className="btn-secondary flex items-center gap-2 disabled:opacity-0"
              >
                <ChevronLeft size={18} /> Back
              </button>
              {step < 4 ? (
                <button onClick={nextStep} className="btn-primary flex items-center gap-2">
                  Continue <ChevronRight size={18} />
                </button>
              ) : (
                <button onClick={handleSubmit} disabled={loading} className="btn-primary flex items-center gap-2">
                  {loading ? "Submitting..." : "Submit Application"} <FileCheck size={18} />
                </button>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
