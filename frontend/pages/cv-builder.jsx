/**
 * AI CV Builder Page with Sidebar Navigation
 * All features accessible via sidebar, except Job Match
 */
import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRouter } from "next/router";
import StepperUI from "../cv-builder/StepperUI";
import CVEditor from "../cv-builder/CVEditor";
import CVSuggestions from "../cv-builder/CVSuggestions";
import JobList from "../components/JobList";
import EuropassCVWizard from "../components/cv-builder/EuropassCVWizard";
import JobMatcher from "../components/cv-builder/JobMatcher";
import CoverLetterGenerator from "../components/cv-builder/CoverLetterGenerator";
import InterviewPrep from "../components/cv-builder/InterviewPrep";
import ATSScoreDisplay from "../components/cv-builder/ATSScoreDisplay";
import ATSOptimizer from "../components/cv-builder/ATSOptimizer";
import CVExporter from "../components/cv-builder/CVExporter";
import JobApplicationTracker from "../components/cv-builder/JobApplicationTracker";
import QuickUpload from "../components/cv-builder/QuickUpload";
import ProposalWriter from "../components/ProposalWriter";
import BackgroundImage from "../components/BackgroundImage";
import toast from "react-hot-toast";
import {
  FileText,
  Search,
  MessageSquare,
  FileCheck,
  Download,
  UserPlus,
  Briefcase,
  Menu,
  X,
  Sparkles,
  Upload,
  Trash2,
  PenTool,
} from "lucide-react";

// Helper function to extract keywords from CV
// Uses the SAME logic as backend upload_linkedin_pdf to ensure consistency
function extractKeywordsFromCV(cvData) {
  if (!cvData) return [];

  const keywords = [];

  // Handle both json_content structure and direct structure
  const content = cvData.json_content || cvData;

  // STEP 1: Extract technical skills (same as backend)
  const skills = content.personal_skills || content.skills || {};

  if (skills.job_related_skills && Array.isArray(skills.job_related_skills)) {
    keywords.push(...skills.job_related_skills.slice(0, 5));
  }
  if (skills.computer_skills && Array.isArray(skills.computer_skills)) {
    keywords.push(...skills.computer_skills.slice(0, 5));
  }
  if (skills.technical && Array.isArray(skills.technical)) {
    keywords.push(...skills.technical.slice(0, 5));
  }
  if (skills.technical_skills && Array.isArray(skills.technical_skills)) {
    keywords.push(...skills.technical_skills.slice(0, 5));
  }
  if (skills.programming_skills && Array.isArray(skills.programming_skills)) {
    keywords.push(...skills.programming_skills.slice(0, 5));
  }

  // STEP 2: Extract job titles from experience (NOT company names or event names)
  // Only extract actual job titles, filter out event names, competitions, etc.
  const experience = content.work_experience || content.experience || [];
  if (Array.isArray(experience)) {
    experience.forEach((exp) => {
      const jobTitle = exp.job_title || exp.position;
      if (jobTitle) {
        // Filter out event names, competitions, hackathons
        const titleLower = jobTitle.toLowerCase();
        const isEvent =
          titleLower.includes("hackathon") ||
          titleLower.includes("competition") ||
          titleLower.includes("participant") ||
          titleLower.includes("winner") ||
          titleLower.includes("event");

        // Only add if it's a real job title (contains common job keywords)
        const isJobTitle =
          titleLower.includes("developer") ||
          titleLower.includes("engineer") ||
          titleLower.includes("programmer") ||
          titleLower.includes("analyst") ||
          titleLower.includes("manager") ||
          titleLower.includes("specialist") ||
          titleLower.includes("consultant") ||
          titleLower.includes("architect") ||
          titleLower.includes("designer") ||
          titleLower.includes("scientist");

        if (!isEvent && (isJobTitle || jobTitle.length > 10)) {
          keywords.push(jobTitle);
        }
      }
    });
  }

  // STEP 3: Extract from summary (same as backend)
  const summary = content.summary || "";
  if (summary) {
    // Extract key terms from summary (simple approach - same as backend)
    const summaryWords = summary.split(/\s+/).filter((w) => w.length > 4);
    keywords.push(...summaryWords.slice(0, 10));
  }

  // Remove duplicates and filter out empty strings
  const uniqueKeywords = [
    ...new Set(keywords.filter((k) => k && k.trim().length > 0)),
  ];

  // If still no keywords, use default tech keywords (same as backend)
  if (uniqueKeywords.length === 0) {
    return ["software", "developer", "engineer", "technology"];
  }

  return uniqueKeywords.slice(0, 10);
}

// Helper function to extract job titles from CV
// Only extracts actual job titles, filters out events/competitions
function extractJobTitlesFromCV(cvData) {
  if (!cvData) return [];

  const titles = [];

  // Handle both json_content structure and direct structure
  const content = cvData.json_content || cvData;

  // Extract from work experience - handle multiple formats
  const experience = content.work_experience || content.experience || [];
  if (Array.isArray(experience)) {
    experience.forEach((exp) => {
      const jobTitle = exp.job_title || exp.position;
      if (jobTitle) {
        // Filter out event names, competitions, hackathons
        const titleLower = jobTitle.toLowerCase();
        const isEvent =
          titleLower.includes("hackathon") ||
          titleLower.includes("competition") ||
          titleLower.includes("participant") ||
          titleLower.includes("winner") ||
          titleLower.includes("event");

        // Only add if it's a real job title
        const isJobTitle =
          titleLower.includes("developer") ||
          titleLower.includes("engineer") ||
          titleLower.includes("programmer") ||
          titleLower.includes("analyst") ||
          titleLower.includes("manager") ||
          titleLower.includes("specialist") ||
          titleLower.includes("consultant") ||
          titleLower.includes("architect") ||
          titleLower.includes("designer") ||
          titleLower.includes("scientist");

        if (!isEvent && (isJobTitle || jobTitle.length > 10)) {
          titles.push(jobTitle);
        }
      }
    });
  }

  return [...new Set(titles.filter((t) => t && t.trim().length > 0))].slice(
    0,
    5
  );
}

// Sidebar menu items
const SIDEBAR_ITEMS = [
  {
    id: "quick-upload",
    label: "Quick Upload",
    icon: Upload,
    alwaysVisible: true,
  },
  { id: "wizard", label: "Create CV", icon: UserPlus, alwaysVisible: true },
  { id: "editor", label: "Edit CV", icon: FileText, requiresCV: true },
  {
    id: "cover-letter",
    label: "Cover Letter",
    icon: MessageSquare,
    requiresCV: false,
  },
  {
    id: "proposal",
    label: "Proposal Writer",
    icon: PenTool,
    requiresCV: false,
  },
  {
    id: "interview",
    label: "Interview Prep",
    icon: MessageSquare,
    requiresCV: false,
  },
  { id: "ats", label: "ATS Optimizer", icon: FileCheck, requiresCV: false },
  { id: "export", label: "Export CV", icon: Download, requiresCV: false },
  { id: "tracker", label: "Applications", icon: Briefcase, requiresCV: false },
];

export default function CVBuilderPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("wizard");
  const [currentStep, setCurrentStep] = useState(1);
  const [cvData, setCvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showJobMatch, setShowJobMatch] = useState(false);

  // Check if CV exists - simpler check: if cvData exists and has content
  const hasCV =
    cvData &&
    (cvData.id ||
      (cvData.json_content && Object.keys(cvData.json_content).length > 0) ||
      (cvData.summary && cvData.summary.length > 0) ||
      (cvData.personal_info && Object.keys(cvData.personal_info).length > 0));

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    fetchCV();
  }, [user]);

  const fetchCV = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
      const response = await fetch(`${apiUrl}/api/cv/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        console.log("[CV Builder] Fetched CV data:", {
          id: data.id,
          hasJsonContent: !!data.json_content,
          jsonContentKeys: data.json_content ? Object.keys(data.json_content) : [],
          personalInfo: data.json_content?.personal_info,
          summary: data.summary || data.json_content?.summary,
          skills: data.json_content?.personal_skills
        });
        setCvData(data);
        if (data && data.id) {
          setActiveTab("editor");
        }
      } else if (response.status === 404) {
        console.log("[CV Builder] No CV found for user");
        setCvData(null);
        setActiveTab("wizard");
      }
    } catch (error) {
      console.error("Failed to fetch CV:", error);
      toast.error("Failed to load CV. Please try again.");
      setCvData(null);
      setActiveTab("wizard");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      toast.success("CV saved successfully!");
    } catch (error) {
      toast.error("Failed to save CV");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = (updatedData) => {
    setCvData(updatedData);
  };

  const handleApplySuggestion = (suggestion) => {
    toast.success("Suggestion applied!");
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  const handleWizardComplete = async (savedCv) => {
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
      const response = await fetch(`${apiUrl}/api/cv/${user.id}`);
      if (response.ok) {
        const fullCv = await response.json();
        setCvData(fullCv);
        setActiveTab("editor");
        toast.success("CV created and saved! You can now use all features.");
      } else {
        setCvData(savedCv);
        setActiveTab("editor");
        toast.success("CV created and saved!");
      }
    } catch (error) {
      setCvData(savedCv);
      setActiveTab("editor");
      toast.success("CV created and saved!");
    }
  };

  // Show all sidebar items, but disable CV-dependent ones if no CV exists
  const visibleSidebarItems = SIDEBAR_ITEMS;

  const renderTabContent = () => {
    switch (activeTab) {
      case "quick-upload":
        return (
          <QuickUpload
            onComplete={async (result) => {
              try {
                // Fetch the saved CV to ensure we have the latest data
                await fetchCV();

                // If CV was saved successfully, set active tab
                if (cvData || result) {
                  setActiveTab("editor");
                  setShowJobMatch(false); // Don't auto-show job match - let user click the button

                  // Show success message with job match count
                  const matchCount =
                    result?.match_count || result?.job_matches?.length || 0;
                  const atsScore = result?.ats_score || "N/A";
                  toast.success(
                    `CV saved! ATS Score: ${atsScore}% | Found ${matchCount} job matches`
                  );
                } else {
                  toast.error("Failed to load CV. Please try again.");
                }
              } catch (error) {
                console.error("Error completing CV upload:", error);
                toast.error("Failed to load CV. Please refresh the page.");
              }
            }}
            onCancel={() => {
              setActiveTab("wizard");
            }}
          />
        );

      case "wizard":
        return (
          <EuropassCVWizard
            onComplete={handleWizardComplete}
            key="europass-cv-wizard-stable"
            onCancel={() => {
              if (hasCV) {
                setActiveTab("editor");
              } else {
                toast("Please complete the CV creation wizard first", {
                  icon: "ℹ️",
                });
              }
            }}
          />
        );

      case "editor":
        if (!hasCV) {
          return (
            <div className="card p-6 text-center">
              <p className="text-gray-600 mb-4">
                No CV found. Please create one first.
              </p>
              <button
                onClick={() => setActiveTab("wizard")}
                className="btn-primary"
              >
                Create CV
              </button>
            </div>
          );
        }
        return (
          <>
            <StepperUI
              currentStep={currentStep}
              onStepChange={setCurrentStep}
              cvData={cvData}
              onUpdate={handleUpdate}
            />
            <div className="mt-8">
              {currentStep <= 5 ? (
                <CVEditor
                  cvData={cvData}
                  onSave={handleSave}
                  onUpdate={handleUpdate}
                />
              ) : (
                <div className="card">
                  <h2 className="text-2xl font-bold mb-4">Review Your CV</h2>
                  {cvData && (
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                      <pre className="whitespace-pre-wrap text-sm">
                        {JSON.stringify(cvData, null, 2)}
                      </pre>
                    </div>
                  )}
                  <div className="flex gap-4">
                    <button
                      onClick={handleSave}
                      className="btn-primary"
                      disabled={loading}
                    >
                      {loading ? "Saving..." : "Save CV"}
                    </button>
                    <button
                      onClick={() => setCurrentStep(1)}
                      className="btn-secondary"
                    >
                      Edit CV
                    </button>
                  </div>
                </div>
              )}
            </div>
            {suggestions && Object.keys(suggestions).length > 0 && (
              <CVSuggestions
                suggestions={suggestions}
                onApply={handleApplySuggestion}
                onDismiss={() => setSuggestions({})}
              />
            )}
          </>
        );

      case "cover-letter":
        if (!hasCV) {
          return (
            <div className="card p-6 text-center">
              <p className="text-gray-600 mb-4">Please create a CV first.</p>
              <button
                onClick={() => setActiveTab("wizard")}
                className="btn-primary"
              >
                Create CV
              </button>
            </div>
          );
        }
        return <CoverLetterGenerator cvData={cvData} userId={user?.id} />;

      case "proposal":
        return <ProposalWriter jobData={null} />;

      case "interview":
        if (!hasCV) {
          return (
            <div className="card p-6 text-center">
              <p className="text-gray-600 mb-4">Please create a CV first.</p>
              <button
                onClick={() => setActiveTab("wizard")}
                className="btn-primary"
              >
                Create CV
              </button>
            </div>
          );
        }
        return <InterviewPrep cvData={cvData} userId={user?.id} />;

      case "ats":
        if (!hasCV) {
          return (
            <div className="card p-6 text-center">
              <p className="text-gray-600 mb-4">Please create a CV first.</p>
              <button
                onClick={() => setActiveTab("wizard")}
                className="btn-primary"
              >
                Create CV
              </button>
            </div>
          );
        }
        return <ATSScoreDisplay cvData={cvData} userId={user?.id} />;

      case "export":
        if (!hasCV) {
          return (
            <div className="card p-6 text-center">
              <p className="text-gray-600 mb-4">Please create a CV first.</p>
              <button
                onClick={() => setActiveTab("wizard")}
                className="btn-primary"
              >
                Create CV
              </button>
            </div>
          );
        }
        return <CVExporter cvData={cvData} userId={user?.id} />;

      case "tracker":
        return <JobApplicationTracker userId={user?.id} />;

      default:
        return (
          <div className="card p-6 text-center">
            <p className="text-gray-600">Select a feature from the sidebar</p>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header Section with Background */}
      <BackgroundImage
        src="/images/backgrounds/hero/cv-builder-hero.jpg"
        alt="CV Builder - TrustBridge"
        overlay="default"
        className="h-64 flex-shrink-0"
        priority={true}
      >
        <div className="max-w-7xl mx-auto px-6 py-12 h-full flex items-end">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-3">
              AI-Powered CV Builder
            </h1>
            <p className="text-xl text-white font-semibold max-w-3xl">
              Build a CV that gets you hired. AI-powered optimization, ATS compatibility, and global job matching—all in one place.
            </p>
          </div>
        </div>
      </BackgroundImage>

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } transition-all duration-300 bg-white border-r border-slate-200 flex-shrink-0 overflow-hidden`}
      >
        <div className="h-full flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">CV Builder</h2>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
          </div>

          {/* Sidebar Menu */}
          <nav className="flex-1 overflow-y-auto p-4">
            <ul className="space-y-2">
              {visibleSidebarItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                const isDisabled = item.requiresCV && !hasCV;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => {
                        if (isDisabled) {
                          toast(
                            "Please create a CV first to use this feature",
                            { icon: "ℹ️" }
                          );
                          setActiveTab("wizard");
                        } else {
                          setActiveTab(item.id);
                        }
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                        isActive
                          ? "bg-gradient-to-r from-sky-500 to-violet-500 text-white shadow-lg"
                          : isDisabled
                          ? "text-slate-400 cursor-not-allowed opacity-60"
                          : "text-slate-700 hover:bg-sky-50 hover:text-sky-700"
                      }`}
                      disabled={isDisabled}
                      title={isDisabled ? "Create a CV first" : ""}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{item.label}</span>
                      {isDisabled && (
                        <span className="ml-auto text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                          Locked
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>

            {/* CV Preview - Removed */}

            {/* Delete CV Button */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={async () => {
                  if (
                    confirm(
                      "Are you sure you want to delete your CV? This action cannot be undone."
                    )
                  ) {
                    try {
                      setLoading(true);
                      const apiUrl =
                        process.env.NEXT_PUBLIC_API_URL ||
                        "http://192.168.100.93:8000";
                      const response = await fetch(
                        `${apiUrl}/api/cv/${user.id}`,
                        {
                          method: "DELETE",
                        }
                      );

                      if (response.ok) {
                        setCvData(null);
                        setActiveTab("wizard");
                        toast.success("CV deleted successfully");
                      } else {
                        const error = await response.json();
                        toast.error(error.detail || "Failed to delete CV");
                      }
                    } catch (error) {
                      console.error("Delete CV error:", error);
                      toast.error("Failed to delete CV");
                    } finally {
                      setLoading(false);
                    }
                  }
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                disabled={loading}
              >
                <Trash2 className="w-4 h-4" />
                Delete CV
              </button>
            </div>

            {/* Job Match Button - Not in sidebar but accessible */}
            {hasCV && (
              <div className="mt-6 pt-6 border-t border-slate-200">
                <button
                  onClick={() => setShowJobMatch(!showJobMatch)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                    showJobMatch
                      ? "bg-gradient-to-r from-sky-500 to-sky-600 text-white shadow-lg"
                      : "text-slate-700 hover:bg-sky-50 hover:text-sky-700 border-2 border-sky-200"
                  }`}
                >
                  <Search className="w-5 h-5" />
                  <span>Job Match</span>
                </button>
              </div>
            )}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar - Simplified (header now in hero section) */}
        <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-600">
              {activeTab === "wizard" &&
                "Create your professional CV step-by-step"}
              {activeTab === "editor" && "Edit and refine your CV"}
              {activeTab === "cover-letter" &&
                "Generate personalized cover letters"}
              {activeTab === "interview" && "Prepare for interviews with AI"}
              {activeTab === "ats" && "Optimize your CV for ATS systems"}
              {activeTab === "export" && "Export your CV in multiple formats"}
              {activeTab === "tracker" && "Track your job applications"}
            </p>
          </div>
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Menu className="w-6 h-6 text-slate-600" />
            </button>
          )}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Job Match Section - Shows when toggled */}
          {showJobMatch && hasCV && (
            <div className="mb-6">
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                    <Search className="w-6 h-6 text-sky-600" />
                    Job Matches for Your CV
                  </h2>
                  <button
                    onClick={() => setShowJobMatch(false)}
                    className="text-slate-500 hover:text-slate-700"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-slate-600 mb-6">
                  Find jobs matching your CV from RemoteOK, Arbeitnow,
                  Freelancer.com, and Adzuna
                </p>
                <JobList
                  keywords={extractKeywordsFromCV(cvData)}
                  jobTitles={extractJobTitlesFromCV(cvData)}
                  location={null}
                  limit={50}
                  userId={user?.id}
                />
              </div>
            </div>
          )}

          {/* Main Tab Content */}
          {/* Only show job match when Job Match button is clicked, don't blur other content */}
          {!showJobMatch && renderTabContent()}

          {/* Global Job Opportunities (only show when CV exists and not in job match mode) */}
          {hasCV && !showJobMatch && activeTab !== "wizard" && (
            <div className="mt-12">
              <div className="card p-6">
                <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <Sparkles className="w-6 h-6 text-sky-600" />
                  Global Job Opportunities
                </h2>
                <p className="text-slate-600 mb-6">
                  Find jobs matching your CV from Adzuna, Jooble, Google Jobs,
                  and remote job boards
                </p>
                <JobList
                  keywords={extractKeywordsFromCV(cvData)}
                  jobTitles={extractJobTitlesFromCV(cvData)}
                  location={null}
                  limit={50}
                  userId={user?.id}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
    </div>
  );
}
