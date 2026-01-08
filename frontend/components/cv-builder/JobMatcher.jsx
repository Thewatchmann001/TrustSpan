/**
 * Job Matching Component
 * Import job description, compute compatibility, and optimize CV
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { 
  FileText, Search, TrendingUp, AlertCircle, 
  CheckCircle, Sparkles, Download, Copy
} from "lucide-react";
import toast from "react-hot-toast";

export default function JobMatcher({ cvData }) {
  const [jobDescription, setJobDescription] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading] = useState(false);
  const [compatibility, setCompatibility] = useState(null);
  const [optimizedCv, setOptimizedCv] = useState(null);

  const handleMatchJob = async () => {
    if (!jobDescription.trim()) {
      toast.error("Please enter a job description");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000"}/api/cv/match-job", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cv_data: cvData,
          job_description: jobDescription,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setCompatibility(result.analysis);
        toast.success(`Compatibility: ${result.score}%`);
      } else {
        toast.error("Failed to analyze compatibility");
      }
    } catch (error) {
      toast.error("Error analyzing job match");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleOptimizeCV = async () => {
    if (!jobDescription.trim()) {
      toast.error("Please enter a job description first");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000"}/api/cv/optimize-for-job", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cv_data: cvData,
          job_description: jobDescription,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setOptimizedCv(result.optimized_cv);
        toast.success("CV optimized successfully!");
      } else {
        toast.error("Failed to optimize CV");
      }
    } catch (error) {
      toast.error("Error optimizing CV");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (score) => {
    if (score >= 80) return "bg-green-100";
    if (score >= 60) return "bg-yellow-100";
    return "bg-red-100";
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <Search className="w-6 h-6" />
        Job Matching & Optimization
      </h2>

      {/* Job Description Input */}
      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-bold text-blue-900 mb-2">
            Company Name (Optional)
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
            placeholder="Paste the full job description here..."
          />
        </div>
        <button
          onClick={handleMatchJob}
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          <TrendingUp className="w-4 h-4" />
          {loading ? "Analyzing..." : "Analyze Compatibility"}
        </button>
      </div>

      {/* Compatibility Results */}
      {compatibility && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className={`${getScoreBg(compatibility.compatibility_score)} rounded-lg p-6 mb-4`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">Compatibility Score</h3>
              <span className={`text-4xl font-bold ${getScoreColor(compatibility.compatibility_score)}`}>
                {compatibility.compatibility_score}%
              </span>
            </div>
            <p className="text-sm text-gray-700">
              {compatibility.compatibility_score >= 80
                ? "Excellent match! You're well-qualified for this role."
                : compatibility.compatibility_score >= 60
                ? "Good match. Some optimization could improve your chances."
                : "Consider adding more relevant skills and experience."}
            </p>
          </div>

          {/* Matched Skills */}
          {compatibility.matched_skills?.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                Matched Skills ({compatibility.matched_skills.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {compatibility.matched_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing Skills */}
          {compatibility.missing_skills?.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-orange-600" />
                Missing Skills ({compatibility.missing_skills.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {compatibility.missing_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {compatibility.recommendations?.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-900 mb-2">Recommendations</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                {compatibility.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Optimize Button */}
          <button
            onClick={handleOptimizeCV}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2 mt-4"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? "Optimizing..." : "Generate Job-Optimized CV"}
          </button>
        </motion.div>
      )}

      {/* Optimized CV Preview */}
      {optimizedCv && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-blue-200 rounded-lg p-4 bg-blue-50"
        >
          <h4 className="font-semibold text-gray-900 mb-2">Optimized CV Generated!</h4>
          <p className="text-sm text-gray-700 mb-4">
            Your CV has been tailored for this specific job. Review the changes and save if you're satisfied.
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => {
                navigator.clipboard.writeText(JSON.stringify(optimizedCv, null, 2));
                toast.success("Optimized CV copied to clipboard");
              }}
              className="btn-secondary flex items-center gap-2"
            >
              <Copy className="w-4 h-4" />
              Copy
            </button>
            <button
              onClick={() => toast.info("Save functionality coming soon")}
              className="btn-primary flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Save Optimized CV
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

