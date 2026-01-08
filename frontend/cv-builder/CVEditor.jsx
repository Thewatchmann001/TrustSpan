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

  // Initialize cvData if null
  const safeCvData = cvData || {
    summary: "",
    json_content: {
      personal_info: {},
      education: [],
      work_experience: [],
      personal_skills: {}
    }
  };

  const handleGetSuggestions = async (section, content) => {
    if (!content) {
      toast.error(`Please add ${section} content first`);
      return;
    }
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
      const response = await fetch(`${apiUrl}/api/cv/suggestions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section, content }),
      });
      const data = await response.json();
      setSuggestions({ ...suggestions, [section]: data });
    } catch (error) {
      toast.error("Failed to get suggestions");
    } finally {
      setLoading(false);
    }
  };

  if (!cvData) {
    return (
      <div className="cv-editor">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <h3 className="text-xl font-semibold text-blue-900 mb-2">No CV Found</h3>
          <p className="text-blue-700 mb-4">Start building your CV by filling in the form below.</p>
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
            onClick={() => handleGetSuggestions("summary", safeCvData.summary || safeCvData.json_content?.summary || "")}
            className="btn-secondary inline-flex items-center gap-2"
            disabled={loading}
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Suggestions</span>
          </button>
          <button onClick={onSave} className="btn-primary inline-flex items-center gap-2">
            <Save className="w-4 h-4" />
            <span>Save CV</span>
          </button>
          <button onClick={() => toast.info("PDF export coming soon")} className="btn-secondary inline-flex items-center gap-2">
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
                      full_name: e.target.value
                    }
                  }
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
                      email: e.target.value
                    }
                  }
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
                      phone: e.target.value
                    }
                  }
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
                      location: e.target.value
                    }
                  }
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
            value={(safeCvData.json_content?.personal_skills?.job_related_skills || []).join(", ")}
            onChange={(e) => {
              const skills = e.target.value.split(",").map(s => s.trim()).filter(s => s);
              const updated = {
                ...safeCvData,
                json_content: {
                  ...safeCvData.json_content,
                  personal_skills: {
                    ...safeCvData.json_content?.personal_skills,
                    job_related_skills: skills
                  }
                }
              };
              if (onUpdate) onUpdate(updated);
            }}
            className="input-field"
            placeholder="JavaScript, Python, React, Node.js"
          />
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700">
            <strong>Tip:</strong> Fill in your information above, then click "AI Suggestions" to get AI-powered improvements for your CV content.
          </p>
        </div>
      </div>
    </div>
  );
}

