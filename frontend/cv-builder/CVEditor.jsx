/**
 * CV Editor Component
 * Main editor for CV content with real-time AI suggestions
 */
import { useState, useEffect } from "react";
import { Sparkles, Save, Download } from "lucide-react";
import toast from "react-hot-toast";

export default function CVEditor({ cvData, onSave, onUpdate }) {
  const [suggestions, setSuggestions] = useState({});
  const [loading, setLoading] = useState(false);

  // Initialize cvData if null and ensure proper structure
  const safeCvData = cvData || {
    summary: "",
    json_content: {
      personal_info: {},
      education: [],
      work_experience: [],
      personal_skills: {},
    },
  };

  // Ensure json_content exists and has required structure
  if (!safeCvData.json_content) {
    safeCvData.json_content = {};
  }
  if (!safeCvData.json_content.personal_info) {
    safeCvData.json_content.personal_info = {};
  }
  if (!safeCvData.json_content.personal_skills) {
    safeCvData.json_content.personal_skills = { job_related_skills: [] };
  }
  if (
    !Array.isArray(safeCvData.json_content.personal_skills.job_related_skills)
  ) {
    safeCvData.json_content.personal_skills.job_related_skills = [];
  }

  const handleGetSuggestions = async (section, content) => {
    if (!content || content.trim().length < 10) {
      toast.error(
        `Please add at least 10 characters of ${section} content first`
      );
      return;
    }
    try {
      setLoading(true);
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
      toast.loading("Generating AI suggestions...", { id: "suggestions" });
      const response = await fetch(`${apiUrl}/api/cv/suggestions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section, content }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Check if we got valid suggestions
      const hasImprovements = data.improvements && data.improvements.length > 0;
      const hasRecommendations =
        data.recommendations && data.recommendations.length > 0;

      if (hasImprovements || hasRecommendations) {
        setSuggestions({ ...suggestions, [section]: data });
        toast.success(
          `Generated ${
            (data.improvements?.length || 0) +
            (data.recommendations?.length || 0)
          } suggestions`,
          { id: "suggestions" }
        );
      } else {
        toast.error(
          "No suggestions generated. Please try again or add more content.",
          { id: "suggestions" }
        );
      }
    } catch (error) {
      console.error("Failed to get suggestions:", error);
      toast.error(`Failed to get suggestions: ${error.message}`, {
        id: "suggestions",
      });
    } finally {
      setLoading(false);
    }
  };

  // Debug: Log cvData structure and show actual values
  useEffect(() => {
    if (cvData) {
      console.log("[CVEditor] CV Data loaded:", {
        hasJsonContent: !!cvData.json_content,
        hasPersonalInfo: !!cvData.json_content?.personal_info,
        personalInfo: cvData.json_content?.personal_info,
        hasSummary: !!cvData.summary || !!cvData.json_content?.summary,
        summary: cvData.summary || cvData.json_content?.summary,
        hasSkills: !!cvData.json_content?.personal_skills,
        skills: cvData.json_content?.personal_skills,
        jsonContentKeys: cvData.json_content
          ? Object.keys(cvData.json_content)
          : [],
        fullCvData: cvData,
      });

      // Show toast if data seems empty
      if (
        !cvData.json_content?.personal_info?.full_name &&
        !cvData.json_content?.personal_info?.email &&
        !cvData.summary &&
        !cvData.json_content?.summary
      ) {
        toast.error(
          "CV data appears empty. Please create or upload a CV first.",
          { duration: 5000 }
        );
      }
    } else {
      console.log("[CVEditor] No CV data provided");
    }
  }, [cvData]);

  // Check if CV data is actually empty (not just null)
  const hasActualData =
    cvData &&
    (cvData.json_content?.personal_info?.full_name ||
      cvData.json_content?.personal_info?.email ||
      cvData.summary ||
      cvData.json_content?.summary ||
      cvData.json_content?.personal_skills?.job_related_skills?.length > 0 ||
      cvData.json_content?.experience?.length > 0 ||
      cvData.json_content?.education?.length > 0);

  if (!cvData || !hasActualData) {
    return (
      <div className="cv-editor">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-yellow-900 mb-2">
            No CV Data Found
          </h3>
          <p className="text-yellow-700 mb-4">
            {!cvData
              ? "No CV found. Please create a CV using 'Create CV' or upload one using 'Quick Upload'."
              : "CV exists but appears to be empty. Please use 'Quick Upload' to upload your CV or 'Create CV' to build one."}
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => window.location.reload()}
              className="btn-secondary"
            >
              Refresh Page
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <h2 className="text-2xl font-bold text-gray-900">CV Editor</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() =>
              handleGetSuggestions(
                "summary",
                safeCvData.summary || safeCvData.json_content?.summary || ""
              )
            }
            className="btn-secondary inline-flex items-center gap-2"
            disabled={loading}
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Suggestions</span>
          </button>
          <button
            onClick={onSave}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            <span>Save CV</span>
          </button>
          <button
            onClick={() => toast("PDF export coming soon", { icon: "ℹ️" })}
            className="btn-secondary inline-flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* CV editing form */}
      <div className="space-y-6">
        {/* Summary Section */}
        <div>
          <label className="block text-sm font-bold text-blue-900 mb-2">
            Professional Summary
          </label>
          <textarea
            value={safeCvData.summary || safeCvData.json_content?.summary || ""}
            onChange={(e) => {
              const updated = { ...safeCvData, summary: e.target.value };
              if (onUpdate) onUpdate(updated);
            }}
            className="input-field min-h-[120px] resize-y"
            placeholder="Write a brief professional summary highlighting your key skills and experience..."
          />
        </div>

        {/* Personal Info Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-bold text-blue-900 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={safeCvData.json_content?.personal_info?.full_name || ""}
              onChange={(e) => {
                const updated = {
                  ...safeCvData,
                  json_content: {
                    ...safeCvData.json_content,
                    personal_info: {
                      ...safeCvData.json_content?.personal_info,
                      full_name: e.target.value,
                    },
                  },
                };
                if (onUpdate) onUpdate(updated);
              }}
              className="input-field"
              placeholder="John Doe"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-blue-900 mb-2">
              Email
            </label>
            <input
              type="email"
              value={safeCvData.json_content?.personal_info?.email || ""}
              onChange={(e) => {
                const updated = {
                  ...safeCvData,
                  json_content: {
                    ...safeCvData.json_content,
                    personal_info: {
                      ...safeCvData.json_content?.personal_info,
                      email: e.target.value,
                    },
                  },
                };
                if (onUpdate) onUpdate(updated);
              }}
              className="input-field"
              placeholder="john.doe@email.com"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-blue-900 mb-2">
              Phone
            </label>
            <input
              type="tel"
              value={safeCvData.json_content?.personal_info?.phone || ""}
              onChange={(e) => {
                const updated = {
                  ...safeCvData,
                  json_content: {
                    ...safeCvData.json_content,
                    personal_info: {
                      ...safeCvData.json_content?.personal_info,
                      phone: e.target.value,
                    },
                  },
                };
                if (onUpdate) onUpdate(updated);
              }}
              className="input-field"
              placeholder="+1234567890"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-blue-900 mb-2">
              Location
            </label>
            <input
              type="text"
              value={safeCvData.json_content?.personal_info?.location || ""}
              onChange={(e) => {
                const updated = {
                  ...safeCvData,
                  json_content: {
                    ...safeCvData.json_content,
                    personal_info: {
                      ...safeCvData.json_content?.personal_info,
                      location: e.target.value,
                    },
                  },
                };
                if (onUpdate) onUpdate(updated);
              }}
              className="input-field"
              placeholder="City, Country"
            />
          </div>
        </div>

        {/* Skills Section */}
        <div>
          <label className="block text-sm font-bold text-blue-900 mb-2">
            Skills (comma-separated)
          </label>
          <input
            type="text"
            value={(
              safeCvData.json_content?.personal_skills?.job_related_skills || []
            ).join(", ")}
            onChange={(e) => {
              const skills = e.target.value
                .split(",")
                .map((s) => s.trim())
                .filter((s) => s);
              const updated = {
                ...safeCvData,
                json_content: {
                  ...safeCvData.json_content,
                  personal_skills: {
                    ...safeCvData.json_content?.personal_skills,
                    job_related_skills: skills,
                  },
                },
              };
              if (onUpdate) onUpdate(updated);
            }}
            className="input-field"
            placeholder="JavaScript, Python, React, Node.js"
          />
        </div>

        {/* Experience Section */}
        <div>
          <label className="block text-sm font-bold text-blue-900 mb-2">
            Work Experience
          </label>
          {(
            safeCvData.json_content?.experience ||
            safeCvData.json_content?.work_experience ||
            []
          ).length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center text-gray-500">
              No experience entries found. Use the CV Builder wizard to add
              experience.
            </div>
          ) : (
            <div className="space-y-4">
              {(
                safeCvData.json_content?.experience ||
                safeCvData.json_content?.work_experience ||
                []
              ).map((exp, idx) => (
                <div
                  key={idx}
                  className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Job Title
                      </label>
                      <p className="text-sm text-gray-900">
                        {exp.job_title || exp.position || "N/A"}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Company
                      </label>
                      <p className="text-sm text-gray-900">
                        {exp.company || exp.employer || "N/A"}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Start Date
                      </label>
                      <p className="text-sm text-gray-900">
                        {exp.start_date || "N/A"}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        End Date
                      </label>
                      <p className="text-sm text-gray-900">
                        {exp.end_date || "Present"}
                      </p>
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Description
                      </label>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {exp.description || "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Education Section */}
        <div>
          <label className="block text-sm font-bold text-blue-900 mb-2">
            Education
          </label>
          {(safeCvData.json_content?.education || []).length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center text-gray-500">
              No education entries found. Use the CV Builder wizard to add
              education.
            </div>
          ) : (
            <div className="space-y-4">
              {(safeCvData.json_content?.education || []).map((edu, idx) => (
                <div
                  key={idx}
                  className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Degree
                      </label>
                      <p className="text-sm text-gray-900">
                        {edu.degree || edu.qualification || "N/A"}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Institution
                      </label>
                      <p className="text-sm text-gray-900">
                        {edu.institution || edu.school || "N/A"}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Start Date
                      </label>
                      <p className="text-sm text-gray-900">
                        {edu.start_date || "N/A"}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Graduation Year
                      </label>
                      <p className="text-sm text-gray-900">
                        {edu.graduation_year || edu.end_date || "N/A"}
                      </p>
                    </div>
                    {edu.field_of_study && (
                      <div className="md:col-span-2">
                        <label className="block text-xs font-semibold text-gray-700 mb-1">
                          Field of Study
                        </label>
                        <p className="text-sm text-gray-700">
                          {edu.field_of_study}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700">
            <strong>Tip:</strong> To edit experience or education, use the
            "Create CV" wizard. This editor shows your current CV content.
          </p>
        </div>
      </div>
    </div>
  );
}
