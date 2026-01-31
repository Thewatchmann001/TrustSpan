/**
 * ATS Score Display Component
 * Shows transparent ATS score breakdown with actionable recommendations
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import toast from "react-hot-toast";

export default function ATSScoreDisplay({ cvData, userId }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (cvData) {
      analyzeATS();
    }
  }, [cvData]);

  const analyzeATS = async () => {
    if (!cvData) return;

    setLoading(true);
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";

      // Extract actual CV content from database object
      let jsonContent = cvData;
      if (typeof cvData === "string") {
        jsonContent = JSON.parse(cvData);
      }

      // If cvData is from database, extract json_content property but keep all fields
      let cvPayload = jsonContent;
      if (
        jsonContent &&
        typeof jsonContent === "object" &&
        jsonContent.json_content
      ) {
        // Use json_content but merge with other important fields (experience, education from credentials)
        cvPayload = {
          ...jsonContent.json_content,
          // Ensure we have all sections from the full cvData
          experience: jsonContent.json_content.experience || jsonContent.experience || [],
          education: jsonContent.json_content.education || jsonContent.education || [],
          skills: jsonContent.json_content.skills || jsonContent.skills || {},
        };
      }

      // Ensure we have actual CV data
      if (
        !cvPayload ||
        (typeof cvPayload === "object" &&
          Object.keys(cvPayload).length === 0)
      ) {
        console.warn("No CV data to analyze:", cvPayload);
        setAnalysis(null);
        return;
      }

      // CRITICAL: Remove old ATS metadata to force fresh calculation
      const { ats_score, ats_grade, ats_metadata, ats_analysis, ...freshCvData } = cvPayload;

      // Use optimize-ats endpoint which always recalculates with ATSEngine
      // CRITICAL: Send user_id so backend can fetch complete CV from database (same as job search)
      // This ensures consistency - same CV → same hash → same score
      const response = await fetch(`${apiUrl}/api/cv/optimize-ats`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          cv_data: freshCvData,
          user_id: userId,  // Send user_id so backend fetches complete CV from database
          force_recompute: false  // Respect cache if CV unchanged
        }),
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      
      // Transform optimize-ats response to match ATSScoreDisplay format
      const transformedResult = {
        // Map optimize-ats response to ATSScoreDisplay expected format
        ats_score: result.ats_score || result.score || 0,
        overall_score: result.ats_score || result.score || 0,
        grade: result.grade || result.ats_grade || "D",
        ats_grade: result.grade || result.ats_grade || "D",
        component_scores: result.section_scores || {},
        cv_hash: result.cv_hash,
        ats_issues: result.issues || result.ats_issues || [],
        ats_recommendations: result.recommendations || result.ats_recommendations || [],
        issues: result.issues || result.ats_issues || [],
        recommendations: {
          critical: (result.issues || []).filter(i => i.severity === "critical").map(i => i.message || i),
          high: result.recommendations || result.ats_recommendations || [],
          medium: [],
          low: []
        },
        // Build score_breakdown from component_scores
        score_breakdown: {
          keyword_match: {
            score: (result.section_scores || {}).keyword_match || 0,
            max: 100,
            details: result.keywords_found || []
          },
          experience_quality: {
            score: (result.section_scores || {}).experience_quality || 0,
            max: 100,
            details: []
          },
          formatting_compatibility: {
            score: result.formatting_score || (result.section_scores || {}).formatting || 0,
            max: 100,
            details: []
          },
          completeness: {
            score: (result.section_scores || {}).completeness || 0,
            max: 100,
            details: []
          }
        }
      };
      
      setAnalysis(transformedResult);
    } catch (error) {
      console.error("ATS Analysis Error:", error);
      toast.error(`Failed to analyze ATS score: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">
          Analyzing CV for ATS compatibility...
        </span>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">
          Upload or edit your CV to see ATS analysis
        </p>
      </div>
    );
  }

  const getGradeColor = (grade) => {
    switch (grade) {
      case "A+":
      case "A":
        return "text-green-600";
      case "B":
        return "text-blue-600";
      case "C":
        return "text-yellow-600";
      default:
        return "text-red-600";
    }
  };

  const getScoreBarColor = (score) => {
    if (score >= 90) return "bg-green-500";
    if (score >= 80) return "bg-blue-500";
    if (score >= 70) return "bg-cyan-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-8">
      {/* Overall Score */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8 border border-blue-200"
      >
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              ATS Compatibility Score
            </h3>
            <p className="text-gray-600">
              How well your CV performs with Applicant Tracking Systems
            </p>
          </div>
          <Sparkles className="w-8 h-8 text-yellow-500" />
        </div>

        <div className="flex items-end gap-8 mb-6">
          <div className="text-center">
            <div
              className={`text-6xl font-bold ${getScoreBarColor(
                analysis.overall_score
              )} mb-2`}
            >
              {Math.round(analysis.overall_score)}
            </div>
            <p className="text-gray-600">out of 100</p>
          </div>

          <div>
            <div
              className={`text-5xl font-bold ${getGradeColor(
                analysis.grade
              )} mb-2`}
            >
              {analysis.grade}
            </div>
            <p className="text-gray-600">Grade</p>
          </div>

          <div className="flex-1">
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${analysis.overall_score}%` }}
                transition={{ duration: 1.5 }}
                className={`h-full ${getScoreBarColor(analysis.overall_score)}`}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {analysis.overall_score}% complete
            </p>
          </div>
        </div>
      </motion.div>

      {/* Category Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-lg p-8 border border-gray-200"
      >
        <h3 className="text-xl font-semibold text-gray-800 mb-6">
          Score Breakdown by Category
        </h3>

        <div className="space-y-6">
          {analysis.score_breakdown &&
            Object.entries(analysis.score_breakdown).map(([category, data]) => (
              <div key={category}>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-700 capitalize">
                    {category.replace(/_/g, " ")}
                  </span>
                  <span className="text-sm font-bold text-gray-600">
                    {data.score || 0} / {data.max || 25}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{
                      width: `${((data.score || 0) / (data.max || 25)) * 100}%`,
                    }}
                    transition={{ duration: 1 }}
                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500"
                  />
                </div>
                {data.details && data.details.length > 0 && (
                  <ul className="mt-2 text-sm text-gray-600 list-disc list-inside">
                    {data.details.slice(0, 2).map((detail, idx) => (
                      <li key={idx}>{detail}</li>
                    ))}
                    {data.details.length > 2 && (
                      <li className="text-gray-500 italic">
                        + {data.details.length - 2} more
                      </li>
                    )}
                  </ul>
                )}
              </div>
            ))}
        </div>
      </motion.div>

      {/* Issues */}
      {analysis.issues && analysis.issues.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-red-50 rounded-lg p-8 border border-red-200"
        >
          <div className="flex items-center gap-3 mb-6">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <h3 className="text-xl font-semibold text-gray-800">
              Areas to Improve
            </h3>
          </div>

          <div className="space-y-4">
            {analysis.issues.map((issue, idx) => (
              <div
                key={idx}
                className="bg-white rounded p-4 border-l-4 border-red-500"
              >
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-800">
                      {issue.message || issue.category}
                    </p>
                    {issue.severity && (
                      <span
                        className={`inline-block mt-2 px-3 py-1 rounded text-xs font-semibold ${
                          issue.severity === "critical"
                            ? "bg-red-100 text-red-800"
                            : issue.severity === "warning"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {issue.severity}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recommendations */}
      {analysis.recommendations && (
        <>
          {/* Critical/High Priority */}
          {(analysis.recommendations.critical?.length > 0 ||
            analysis.recommendations.high?.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-green-50 rounded-lg p-8 border border-green-200"
            >
              <div className="flex items-center gap-3 mb-6">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <h3 className="text-xl font-semibold text-gray-800">
                  Key Recommendations
                </h3>
              </div>

              <div className="space-y-4">
                {[
                  ...(analysis.recommendations.critical || []),
                  ...(analysis.recommendations.high || []),
                ].map((rec, idx) => (
                  <div
                    key={idx}
                    className="bg-white rounded p-4 border-l-4 border-green-500"
                  >
                    <p className="font-medium text-gray-800">{rec}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      This change will improve your ATS score
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Medium/Low Priority */}
          {(analysis.recommendations.medium?.length > 0 ||
            analysis.recommendations.low?.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <button
                onClick={() => setExpanded(!expanded)}
                className="w-full text-left p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-800">
                    Additional Suggestions
                  </span>
                  <span
                    className={`text-gray-600 transition-transform ${
                      expanded ? "rotate-180" : ""
                    }`}
                  >
                    ▼
                  </span>
                </div>
              </button>

              {expanded && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-4 space-y-3"
                >
                  {[
                    ...(analysis.recommendations.medium || []),
                    ...(analysis.recommendations.low || []),
                  ].map((rec, idx) => (
                    <div
                      key={idx}
                      className="bg-gray-50 rounded p-4 border border-gray-200"
                    >
                      <p className="text-gray-800">{rec}</p>
                    </div>
                  ))}
                </motion.div>
              )}
            </motion.div>
          )}
        </>
      )}

      {/* Refresh Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={analyzeATS}
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
        Reanalyze ATS Score
      </motion.button>
    </div>
  );
}
