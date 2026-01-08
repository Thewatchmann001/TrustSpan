/**
 * Cover Letter Generator Component
 * Generate personalized cover letters based on CV and job description
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { FileText, Sparkles, Download, Copy, Edit } from "lucide-react";
import toast from "react-hot-toast";

export default function CoverLetterGenerator({ cvData }) {
  const [jobDescription, setJobDescription] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [editing, setEditing] = useState(false);

  const handleGenerate = async () => {
    if (!jobDescription.trim()) {
      toast.error("Please enter a job description");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000"}/api/cv/generate-cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cv_data: cvData,
          job_description: jobDescription,
          company_name: companyName,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setCoverLetter(result.cover_letter);
        setEditing(false);
        toast.success("Cover letter generated successfully!");
      } else {
        toast.error("Failed to generate cover letter");
      }
    } catch (error) {
      toast.error("Error generating cover letter");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(coverLetter);
    toast.success("Cover letter copied to clipboard!");
  };

  const handleDownload = () => {
    const blob = new Blob([coverLetter], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cover-letter-${companyName || "application"}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Cover letter downloaded!");
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <FileText className="w-6 h-6" />
        Cover Letter Generator
      </h2>

      {/* Input Form */}
      {!coverLetter && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-bold text-blue-900 mb-2">
              Company Name
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="input-field"
              placeholder="e.g., Google, Microsoft"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-blue-900 mb-2">
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              className="input-field min-h-[200px]"
              placeholder="Paste the job description here..."
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? "Generating..." : "Generate Cover Letter"}
          </button>
        </div>
      )}

      {/* Generated Cover Letter */}
      {coverLetter && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Your Cover Letter</h3>
            <div className="flex gap-2">
              <button
                onClick={() => setEditing(!editing)}
                className="btn-secondary flex items-center gap-2"
              >
                <Edit className="w-4 h-4" />
                {editing ? "Done" : "Edit"}
              </button>
              <button
                onClick={handleCopy}
                className="btn-secondary flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                Copy
              </button>
              <button
                onClick={handleDownload}
                className="btn-primary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
          </div>

          {editing ? (
            <textarea
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              className="input-field min-h-[400px] font-mono text-sm"
            />
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-6 min-h-[400px] whitespace-pre-wrap text-gray-800">
              {coverLetter}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => {
                setCoverLetter("");
                setJobDescription("");
                setCompanyName("");
              }}
              className="btn-secondary"
            >
              Generate New
            </button>
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="btn-primary"
            >
              Regenerate
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

