/**
 * CV Export Component
 * Export CV as PDF, DOCX, or shareable web profile
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { Download, FileText, Globe, Share2, Copy } from "lucide-react";
import toast from "react-hot-toast";

export default function CVExporter({ cvData, userId }) {
  const [loading, setLoading] = useState(false);
  const [shareLink, setShareLink] = useState("");

  const handleExportPDF = async () => {
    setLoading(true);
    try {
      // For now, create a simple text-based export
      // In production, use a library like jsPDF or send to backend
      const cvText = formatCVAsText(cvData);
      const blob = new Blob([cvText], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `CV-${cvData?.personal_info?.full_name || "resume"}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("CV exported! (PDF export coming soon)");
    } catch (error) {
      toast.error("Error exporting CV");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportDOCX = async () => {
    toast("DOCX export coming soon. Use PDF export for now.", { icon: 'ℹ️' });
  };

  const handleCreateShareLink = async () => {
    setLoading(true);
    try {
      // In production, this would create a shareable link via backend
      const link = `${window.location.origin}/cv/public/${userId || "preview"}`;
      setShareLink(link);
      navigator.clipboard.writeText(link);
      toast.success("Shareable link created and copied!");
    } catch (error) {
      toast.error("Error creating share link");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const formatCVAsText = (cv) => {
    if (!cv) return "";
    
    const lines = [];
    
    // Personal Info
    if (cv.personal_info) {
      lines.push(cv.personal_info.full_name || "");
      lines.push(`${cv.personal_info.email || ""} | ${cv.personal_info.phone || ""}`);
      lines.push(cv.personal_info.location || "");
      lines.push("");
    }
    
    // Summary
    if (cv.summary) {
      lines.push("PROFESSIONAL SUMMARY");
      lines.push(cv.summary);
      lines.push("");
    }
    
    // Experience
    if (cv.experience && cv.experience.length > 0) {
      lines.push("EXPERIENCE");
      cv.experience.forEach(exp => {
        lines.push(`${exp.job_title || ""} at ${exp.company || ""}`);
        lines.push(`${exp.start_date || ""} - ${exp.end_date || "Present"}`);
        lines.push(exp.description || "");
        lines.push("");
      });
    }
    
    // Education
    if (cv.education && cv.education.length > 0) {
      lines.push("EDUCATION");
      cv.education.forEach(edu => {
        lines.push(`${edu.degree || ""} - ${edu.institution || ""}`);
        lines.push(`${edu.field_of_study || ""} (${edu.graduation_year || ""})`);
        lines.push("");
      });
    }
    
    // Skills
    if (cv.skills) {
      lines.push("SKILLS");
      if (cv.skills.technical) {
        lines.push(`Technical: ${cv.skills.technical.join(", ")}`);
      }
      if (cv.skills.soft) {
        lines.push(`Soft Skills: ${cv.skills.soft.join(", ")}`);
      }
    }
    
    return lines.join("\n");
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <Download className="w-6 h-6" />
        Export & Share CV
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* PDF Export */}
        <button
          onClick={handleExportPDF}
          disabled={loading || !cvData}
          className="btn-secondary flex flex-col items-center gap-3 p-6 hover:bg-blue-50 transition-colors"
        >
          <FileText className="w-8 h-8 text-blue-600" />
          <div className="text-center">
            <p className="font-semibold text-gray-900">Export as PDF</p>
            <p className="text-xs text-gray-600 mt-1">Download PDF version</p>
          </div>
        </button>

        {/* DOCX Export */}
        <button
          onClick={handleExportDOCX}
          disabled={loading || !cvData}
          className="btn-secondary flex flex-col items-center gap-3 p-6 hover:bg-blue-50 transition-colors"
        >
          <FileText className="w-8 h-8 text-blue-600" />
          <div className="text-center">
            <p className="font-semibold text-gray-900">Export as DOCX</p>
            <p className="text-xs text-gray-600 mt-1">Download Word document</p>
          </div>
        </button>

        {/* Share Link */}
        <button
          onClick={handleCreateShareLink}
          disabled={loading || !cvData}
          className="btn-secondary flex flex-col items-center gap-3 p-6 hover:bg-blue-50 transition-colors"
        >
          <Globe className="w-8 h-8 text-blue-600" />
          <div className="text-center">
            <p className="font-semibold text-gray-900">Create Share Link</p>
            <p className="text-xs text-gray-600 mt-1">Generate public profile</p>
          </div>
        </button>
      </div>

      {/* Share Link Display */}
      {shareLink && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4"
        >
          <p className="text-sm font-semibold text-gray-900 mb-2">Your Shareable Link:</p>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={shareLink}
              readOnly
              className="input-field flex-1 text-sm"
            />
            <button
              onClick={() => {
                navigator.clipboard.writeText(shareLink);
                toast.success("Link copied!");
              }}
              className="btn-secondary flex items-center gap-2"
            >
              <Copy className="w-4 h-4" />
              Copy
            </button>
          </div>
          <p className="text-xs text-gray-600 mt-2">
            Share this link with employers or add it to your portfolio
          </p>
        </motion.div>
      )}
    </div>
  );
}

