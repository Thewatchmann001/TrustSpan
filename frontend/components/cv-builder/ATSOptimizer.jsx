/**
 * ATS Optimization Component
 * Check CV formatting, keywords, and provide optimization suggestions
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  CheckCircle, AlertCircle, TrendingUp, 
  FileCheck, Download, RefreshCw, Eye, FileText, Sparkles
} from "lucide-react";
import toast from "react-hot-toast";

export default function ATSOptimizer({ cvData, onOptimize, userId }) {
  const [atsAnalysis, setAtsAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [optimizedCV, setOptimizedCV] = useState(null);
  const [showOptimizedPreview, setShowOptimizedPreview] = useState(false);
  const [optimizationDetails, setOptimizationDetails] = useState(null);

  useEffect(() => {
    if (cvData) {
      analyzeATS();
    }
  }, [cvData]);

  useEffect(() => {
    if (activeCvData) {
      analyzeATS();
    }
  }, [activeCvData]);

  const analyzeATS = async (forceRecalculate = false) => {
    if (!cvData) return;

    setLoading(true);
    try {
      const jsonContent = cvData.json_content || cvData;
      
      // CRITICAL FIX: Always call API to get fresh score from ATSEngine
      // Never use cached scores - the API endpoint always recalculates
      // This ensures consistency and prevents stale data issues
      if (!forceRecalculate && jsonContent.ats_score !== undefined && jsonContent.ats_score !== null) {
        // Check if this is a fresh score from ATSEngine (has component_scores)
        const atsMetadata = jsonContent.ats_metadata || {};
        const hasComponentScores = atsMetadata.component_scores || jsonContent.component_scores;
        const hasRecentScore = jsonContent.ats_score >= 70; // Only trust scores that look reasonable
        
        // Only use cached score if:
        // 1. It has component_scores (from ATSEngine)
        // 2. Score is reasonable (>= 70, not the old 41% bug)
        // 3. User didn't force recalculation
        if (hasComponentScores && hasRecentScore && !forceRecalculate) {
          const existingScore = jsonContent.ats_score;
          const existingGrade = jsonContent.ats_grade || (existingScore >= 90 ? "A+" : existingScore >= 80 ? "A" : existingScore >= 70 ? "B" : existingScore >= 60 ? "C" : "D");
          
          setAtsAnalysis({
            ats_score: existingScore,
            score: existingScore,
            grade: existingGrade,
            keyword_density: atsMetadata.keyword_density || 0,
            formatting_score: atsMetadata.formatting_score || existingScore,
            section_completeness: atsMetadata.section_completeness || {},
            recommendations: atsMetadata.recommendations || [],
            issues: atsMetadata.issues || [],
            suggestions: atsMetadata.recommendations || [],
            ats_metadata: atsMetadata,
            section_scores: atsMetadata.component_scores || {},
            component_feedback: atsMetadata.component_feedback || {}
          });
          setLoading(false);
          return;
        }
        // If score is suspiciously low (< 70) or missing component_scores, always recalculate
        console.log("Recalculating ATS score - cached score appears stale or invalid");
      }

      // Calculate new ATS score using ATSEngine (consistent with backend)
      // CRITICAL: Send user_id so backend can fetch complete CV from database (same as job search)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
      const endpoint = apiUrl + "/api/cv/optimize-ats";
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          cv_data: jsonContent,
          user_id: userId,  // Send user_id so backend fetches complete CV from database
          force_recompute: forceRecalculate
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Ensure all detailed fields are included
      const enhancedResult = {
        ...result,
        ats_score: result.ats_score || result.score || 0,
        grade: result.grade || (result.ats_score >= 90 ? "A+" : result.ats_score >= 80 ? "A" : result.ats_score >= 70 ? "B" : result.ats_score >= 60 ? "C" : "D"),
        section_scores: result.section_scores || {},
        section_feedback: result.section_feedback || {},
        keywords_found: result.keywords_found || [],
        keywords_missing: result.keywords_missing || [],
        formatting_score: result.formatting_score || result.ats_score || 0,
        keyword_density: result.keyword_density || 0,
        section_completeness: result.section_completeness || {}
      };
      
      setAtsAnalysis(enhancedResult);
      
      // Get optimized CV version
      try {
        const optimizeEndpoint = apiUrl + "/api/cv/get-optimized";
        const optimizeResponse = await fetch(optimizeEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cv_data: jsonContent }),
        });
        
        if (optimizeResponse.ok) {
          const optimized = await optimizeResponse.json();
          setOptimizedCV(optimized.optimized_cv || optimized);
          setOptimizationDetails(optimized.optimization_details || {
            changes: optimized.changes || [],
            improvements: optimized.improvements || [],
            keywords_added: optimized.keywords_added || []
          });
        }
      } catch (optError) {
        console.error("Error fetching optimized CV:", optError);
        // Fallback: use current CV data as optimized
        setOptimizedCV(jsonContent);
      }
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
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileCheck className="w-6 h-6" />
          ATS Optimization
        </h2>
        <button
          onClick={() => analyzeATS(true)}
          disabled={loading}
          className="btn-secondary flex items-center gap-2"
          title="Force recalculation with latest ATS engine"
        >
          <RefreshCw className={loading ? "w-4 h-4 animate-spin" : "w-4 h-4"} />
          Re-analyze
        </button>
      </div>
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
                {/* Show score improvement if available */}
                {atsAnalysis.ats_metadata?.improvements?.original_score !== undefined && (
                  <div className="mt-2 flex items-center gap-2 text-sm">
                    <span className="text-gray-600">Original Score:</span>
                    <span className="font-semibold text-gray-800">{atsAnalysis.ats_metadata.improvements.original_score}%</span>
                    <span className="text-green-600 font-bold">→</span>
                    <span className="font-semibold text-green-600">{atsAnalysis.ats_score}%</span>
                    {atsAnalysis.ats_metadata.improvements.score_increase > 0 && (
                      <span className="text-green-600 font-semibold">
                        (+{atsAnalysis.ats_metadata.improvements.score_increase}%)
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div className="text-right">
                <div className={"text-5xl font-bold " + getScoreColor(atsAnalysis.ats_score)}>
                  {atsAnalysis.ats_score}
                </div>
                <div className={"text-2xl font-bold " + getGradeColor(atsAnalysis.grade)}>
                  {atsAnalysis.grade}
                </div>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={
                  "h-3 rounded-full transition-all " +
                  (atsAnalysis.ats_score >= 80
                    ? "bg-green-500"
                    : atsAnalysis.ats_score >= 60
                    ? "bg-yellow-500"
                    : "bg-red-500")
                }
                style={{ width: atsAnalysis.ats_score + "%" }}
              />
            </div>
          </div>

          {/* ATS Modifications - Before/After Comparison */}
          {atsAnalysis.ats_metadata?.improvements?.changes_made && 
           atsAnalysis.ats_metadata.improvements.changes_made.length > 0 && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2 text-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
                ATS Modifications Applied
              </h4>
              <div className="space-y-4">
                {atsAnalysis.ats_metadata.improvements.changes_made.map((change, idx) => (
                  <div key={idx} className="bg-white rounded-lg p-4 border border-green-200 shadow-sm">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold uppercase">
                            {change.section}
                          </span>
                          <span className="text-sm font-semibold text-gray-900">{change.change}</span>
                        </div>
                        {change.before && change.after && (
                          <div className="space-y-3 mt-3">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              <div className="border-r border-gray-200 pr-3">
                                <p className="text-xs font-semibold text-red-600 mb-1 uppercase">Before</p>
                                <p className="text-sm text-gray-700 bg-red-50 p-2 rounded border border-red-100">
                                  {change.before}
                                </p>
                              </div>
                              <div className="pl-3">
                                <p className="text-xs font-semibold text-green-600 mb-1 uppercase">After</p>
                                <p className="text-sm text-gray-700 bg-green-50 p-2 rounded border border-green-100">
                                  {change.after}
                                </p>
                              </div>
                            </div>
                            {change.reason && (
                              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                                <p className="text-xs font-semibold text-blue-800 mb-1 uppercase">Why This Change Was Made</p>
                                <p className="text-sm text-blue-900">{change.reason}</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {atsAnalysis.ats_metadata.improvements.score_increase > 0 && (
                <div className="mt-4 p-3 bg-green-100 border border-green-300 rounded-lg">
                  <p className="text-sm font-semibold text-green-900">
                    🎉 Your ATS score improved by {atsAnalysis.ats_metadata.improvements.score_increase}% 
                    ({atsAnalysis.ats_metadata.improvements.original_score}% → {atsAnalysis.ats_score}%)
                  </p>
                </div>
              )}
            </div>
          )}

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

          {/* Detailed Score Breakdown */}
          {atsAnalysis.section_scores && (
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2 text-lg">
                <FileCheck className="w-6 h-6 text-indigo-600" />
                Detailed Score Breakdown
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(atsAnalysis.section_scores).map(([section, score]) => (
                  <div key={section} className="bg-white rounded-lg p-4 border border-indigo-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-gray-900 capitalize">{section}</span>
                      <span className={`text-lg font-bold ${
                        score >= 15 ? "text-green-600" : score >= 10 ? "text-yellow-600" : "text-red-600"
                      }`}>
                        {score}/20
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div
                        className={`h-2 rounded-full ${
                          score >= 15 ? "bg-green-500" : score >= 10 ? "bg-yellow-500" : "bg-red-500"
                        }`}
                        style={{ width: `${(score / 20) * 100}%` }}
                      />
                    </div>
                    {atsAnalysis.section_feedback && atsAnalysis.section_feedback[section] && (
                      <p className="text-xs text-gray-600 mt-1">{atsAnalysis.section_feedback[section]}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Keywords Analysis */}
          {(atsAnalysis.keywords_found || atsAnalysis.keywords_missing) && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-amber-600" />
                Keyword Analysis
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {atsAnalysis.keywords_found && atsAnalysis.keywords_found.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Keywords Found ({atsAnalysis.keywords_found.length})
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {atsAnalysis.keywords_found.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {atsAnalysis.keywords_missing && atsAnalysis.keywords_missing.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-orange-600" />
                      Missing Keywords ({atsAnalysis.keywords_missing.length})
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {atsAnalysis.keywords_missing.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-medium"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {atsAnalysis.keyword_density !== undefined && (
                <div className="mt-4 p-3 bg-white rounded border border-amber-200">
                  <p className="text-sm text-gray-700">
                    <span className="font-semibold">Keyword Density:</span> {atsAnalysis.keyword_density.toFixed(2)}%
                    {atsAnalysis.keyword_density < 2.0 && (
                      <span className="text-orange-600 ml-2">(Low - aim for 2.0% or higher)</span>
                    )}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Formatting Score */}
          {atsAnalysis.formatting_score !== undefined && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-gray-900">Formatting Score</span>
                <span className={`text-lg font-bold ${
                  atsAnalysis.formatting_score >= 90 ? "text-green-600" : 
                  atsAnalysis.formatting_score >= 70 ? "text-yellow-600" : "text-red-600"
                }`}>
                  {atsAnalysis.formatting_score}/100
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    atsAnalysis.formatting_score >= 90 ? "bg-green-500" : 
                    atsAnalysis.formatting_score >= 70 ? "bg-yellow-500" : "bg-red-500"
                  }`}
                  style={{ width: `${atsAnalysis.formatting_score}%` }}
                />
              </div>
              {atsAnalysis.formatting_score < 90 && (
                <p className="text-xs text-gray-600 mt-2">
                  Consider removing special characters and using plain text formatting for better ATS compatibility.
                </p>
              )}
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

          {/* Optimization Details */}
          {optimizationDetails && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-5">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                How Your CV Was Optimized
              </h4>
              <div className="space-y-3">
                {optimizationDetails.keywords_added && optimizationDetails.keywords_added.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-2">Keywords Added:</p>
                    <div className="flex flex-wrap gap-2">
                      {optimizationDetails.keywords_added.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {optimizationDetails.improvements && optimizationDetails.improvements.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-2">Improvements Made:</p>
                    <ul className="space-y-1">
                      {optimizationDetails.improvements.map((improvement, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                          <CheckCircle className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                          <span>{improvement}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {optimizationDetails.changes && optimizationDetails.changes.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-2">Changes Applied:</p>
                    <ul className="space-y-1">
                      {optimizationDetails.changes.map((change, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                          <TrendingUp className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                          <span>{change}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Optimized CV Preview & Download */}
          {optimizedCV && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-green-600" />
                    Optimized CV Version
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Your CV has been optimized for ATS systems
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowOptimizedPreview(!showOptimizedPreview)}
                    className="btn-secondary flex items-center gap-2 text-sm"
                  >
                    <Eye className="w-4 h-4" />
                    {showOptimizedPreview ? "Hide" : "Preview"}
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
                        const response = await fetch(`${apiUrl}/api/cv/export-pdf`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ cv_data: optimizedCV }),
                        });
                        
                        if (response.ok) {
                          const blob = await response.blob();
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          const fullName = optimizedCV.personal_info?.full_name || 
                                         `${optimizedCV.personal_info?.first_name || ""} ${optimizedCV.personal_info?.surname || ""}`.trim() ||
                                         "CV";
                          a.download = `Optimized-CV-${fullName.replace(/\s+/g, "-")}.pdf`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          window.URL.revokeObjectURL(url);
                          toast.success("Optimized CV downloaded successfully!");
                        } else {
                          toast.error("Failed to download optimized CV");
                        }
                      } catch (error) {
                        console.error("Download error:", error);
                        toast.error("Error downloading optimized CV");
                      }
                    }}
                    className="btn-primary flex items-center gap-2 text-sm"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </button>
                </div>
              </div>
              
              {showOptimizedPreview && (
                <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4 max-h-96 overflow-y-auto">
                  <div className="space-y-4">
                    {optimizedCV.personal_info && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2">Personal Information</h5>
                        <p className="text-sm text-gray-700">
                          {optimizedCV.personal_info.full_name || 
                           `${optimizedCV.personal_info.first_name || ""} ${optimizedCV.personal_info.surname || ""}`.trim()}
                        </p>
                        <p className="text-sm text-gray-600">{optimizedCV.personal_info.email}</p>
                      </div>
                    )}
                    {optimizedCV.summary && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2">Professional Summary</h5>
                        <p className="text-sm text-gray-700 leading-relaxed">{optimizedCV.summary}</p>
                      </div>
                    )}
                    {optimizedCV.experience && optimizedCV.experience.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2">Experience</h5>
                        <div className="space-y-2">
                          {optimizedCV.experience.slice(0, 2).map((exp, idx) => (
                            <div key={idx} className="text-sm">
                              <p className="font-medium text-gray-800">{exp.job_title} at {exp.company}</p>
                              <p className="text-gray-600 text-xs">{exp.start_date} - {exp.end_date || "Present"}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {optimizedCV.personal_skills && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2">Skills</h5>
                        <div className="flex flex-wrap gap-2">
                          {[
                            ...(optimizedCV.personal_skills.job_related_skills || []),
                            ...(optimizedCV.personal_skills.computer_skills || [])
                          ].slice(0, 10).map((skill, idx) => (
                            <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* No Issues */}
          {((!atsAnalysis.issues || atsAnalysis.issues.length === 0) &&
            (!atsAnalysis.suggestions || atsAnalysis.suggestions.length === 0)) ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-green-900">Excellent!</p>
                  <p className="text-sm text-green-700">
                    Your CV is well-optimized for ATS systems.
                  </p>
                </div>
              </div>
            ) : null}
        </motion.div>
      )}
    </div>
  );
}

