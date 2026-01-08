/**
 * ATS Optimization Component
 * Check CV formatting, keywords, and provide optimization suggestions
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  CheckCircle, AlertCircle, TrendingUp, 
  FileCheck, Download, RefreshCw
} from "lucide-react";
import toast from "react-hot-toast";

export default function ATSOptimizer({ cvData, onOptimize }) {
  const [atsAnalysis, setAtsAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (cvData) {
      analyzeATS();
    }
  }, [cvData]);

  const analyzeATS = async () => {
    if (!cvData) return;

    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000"}/api/cv/optimize-ats", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cv_data: cvData }),
      });

      const result = await response.json();
      setAtsAnalysis(result);
    } catch (error) {
      toast.error("Error analyzing ATS compatibility");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    if (grade.startsWith("A")) return "text-green-600";
    if (grade.startsWith("B")) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  if (!cvData) {
    return (
      <div className="card">
        <p className="text-gray-600">Create a CV first to analyze ATS compatibility</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileCheck className="w-6 h-6" />
          ATS Optimization
        </h2>
        <button
          onClick={analyzeATS}
          disabled={loading}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Re-analyze
        </button>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing your CV...</p>
        </div>
      )}

      {atsAnalysis && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Score Display */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">ATS Compatibility Score</h3>
                <p className="text-sm text-gray-600">How well your CV will pass ATS systems</p>
              </div>
              <div className="text-right">
                <div className={`text-5xl font-bold ${getScoreColor(atsAnalysis.ats_score)}`}>
                  {atsAnalysis.ats_score}
                </div>
                <div className={`text-2xl font-bold ${getGradeColor(atsAnalysis.grade)}`}>
                  {atsAnalysis.grade}
                </div>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  atsAnalysis.ats_score >= 80
                    ? "bg-green-500"
                    : atsAnalysis.ats_score >= 60
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${atsAnalysis.ats_score}%` }}
              />
            </div>
          </div>

          {/* Issues */}
          {atsAnalysis.issues && atsAnalysis.issues.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-orange-600" />
                Issues Found ({atsAnalysis.issues.length})
              </h4>
              <ul className="space-y-2">
                {atsAnalysis.issues.map((issue, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-sm text-gray-700 bg-orange-50 border border-orange-200 rounded p-3"
                  >
                    <AlertCircle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggestions */}
          {atsAnalysis.suggestions && atsAnalysis.suggestions.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Optimization Suggestions
              </h4>
              <ul className="space-y-2">
                {atsAnalysis.suggestions.map((suggestion, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-sm text-gray-700 bg-blue-50 border border-blue-200 rounded p-3"
                  >
                    <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* No Issues */}
          {(!atsAnalysis.issues || atsAnalysis.issues.length === 0) &&
            (!atsAnalysis.suggestions || atsAnalysis.suggestions.length === 0) && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-green-900">Excellent!</p>
                  <p className="text-sm text-green-700">
                    Your CV is well-optimized for ATS systems.
                  </p>
                </div>
              </div>
            )}
        </motion.div>
      )}
    </div>
  );
}

