/**
 * Proposal Writer Component
 * Generates customized freelancing proposals with AI
 */
import { useState } from "react";
import { FileText, Sparkles, Edit2, Download, Copy, Check } from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";

export default function ProposalWriter({ jobData = null, onClose = null }) {
  const { user } = useAuth();
  const [jobDescription, setJobDescription] = useState(jobData?.description || jobData?.summary || "");
  const [clientRequirements, setClientRequirements] = useState("");
  const [tone, setTone] = useState("professional");
  const [generatedProposal, setGeneratedProposal] = useState("");
  const [editingProposal, setEditingProposal] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!jobDescription.trim()) {
      toast.error("Please provide a job description");
      return;
    }

    setIsGenerating(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
      
      // Get user's CV data for skills/experience
      let userSkills = [];
      let userExperience = [];
      
      if (user?.id) {
        try {
          const cvResponse = await fetch(`${apiUrl}/api/cv/${user.id}`);
          if (cvResponse.ok) {
            const cvData = await cvResponse.json();
            if (cvData.json_content) {
              const skillsData = cvData.json_content.personal_skills || cvData.json_content.skills || {};
              if (skillsData.job_related_skills) {
                userSkills = skillsData.job_related_skills;
              } else if (Array.isArray(skillsData)) {
                userSkills = skillsData;
              }
              
              userExperience = cvData.json_content.work_experience || cvData.json_content.experience || [];
            }
          }
        } catch (e) {
          console.warn("Could not fetch CV data:", e);
        }
      }

      // Use timeout to ensure fast response (5 seconds max)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${apiUrl}/api/proposals/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_description: jobDescription,
          client_requirements: clientRequirements,
          user_id: user?.id,
          user_skills: userSkills,
          user_experience: userExperience,
          tone: tone
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success && result.proposal) {
        setGeneratedProposal(result.proposal);
        setEditingProposal(result.proposal);
        setIsEditing(false);
        toast.success("Proposal generated successfully!");
      } else {
        throw new Error("Failed to generate proposal");
      }
    } catch (error) {
      console.error("Error generating proposal:", error);
      if (error.name === 'AbortError') {
        toast.error("Proposal generation timed out. Please try again.");
      } else {
        toast.error(`Failed to generate proposal: ${error.message}`);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    const textToCopy = editingProposal || generatedProposal;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    toast.success("Proposal copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const textToDownload = editingProposal || generatedProposal;
    const blob = new Blob([textToDownload], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Proposal-${new Date().toISOString().split("T")[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    toast.success("Proposal downloaded!");
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Freelancing Proposal Writer</h2>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          )}
        </div>

        {/* Input Form */}
        {!generatedProposal && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Job Description <span className="text-red-500">*</span>
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here..."
                className="w-full min-h-[200px] px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Client Requirements (Optional)
              </label>
              <textarea
                value={clientRequirements}
                onChange={(e) => setClientRequirements(e.target.value)}
                placeholder="Any specific requirements, deadlines, or preferences mentioned by the client..."
                className="w-full min-h-[120px] px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Proposal Tone
              </label>
              <div className="flex gap-4">
                {["professional", "friendly", "confident"].map((t) => (
                  <label key={t} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="tone"
                      value={t}
                      checked={tone === t}
                      onChange={(e) => setTone(e.target.value)}
                      className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 capitalize">{t}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={isGenerating || !jobDescription.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? (
                <>
                  <Sparkles className="w-5 h-5 animate-spin" />
                  Generating Proposal...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate Proposal
                </>
              )}
            </button>
          </div>
        )}

        {/* Generated Proposal */}
        {generatedProposal && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-gray-900">Generated Proposal</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                >
                  <Edit2 className="w-4 h-4" />
                  {isEditing ? "View Mode" : "Edit"}
                </button>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? "Copied!" : "Copy"}
                </button>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>
            </div>

            {isEditing ? (
              <textarea
                value={editingProposal}
                onChange={(e) => setEditingProposal(e.target.value)}
                className="w-full min-h-[400px] px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y font-mono text-sm"
              />
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg p-6 min-h-[400px] whitespace-pre-wrap text-gray-800 leading-relaxed">
                {editingProposal || generatedProposal}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setGeneratedProposal("");
                  setEditingProposal("");
                  setIsEditing(false);
                }}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                Generate New Proposal
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Done
                </button>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
