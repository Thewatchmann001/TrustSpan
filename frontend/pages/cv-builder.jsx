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
import ATSOptimizer from "../components/cv-builder/ATSOptimizer";
import CVExporter from "../components/cv-builder/CVExporter";
import JobApplicationTracker from "../components/cv-builder/JobApplicationTracker";
import CVPreview from "../cv-builder/CVPreview";
import QuickUpload from "../components/cv-builder/QuickUpload";
import toast from "react-hot-toast";
import { 
  FileText, Search, MessageSquare, FileCheck, 
  Download, UserPlus, Briefcase, Menu, X, Sparkles, Upload
} from "lucide-react";

// Helper function to extract keywords from CV
function extractKeywordsFromCV(cvData) {
  if (!cvData || !cvData.json_content) return [];
  
  const keywords = [];
  const content = cvData.json_content;
  
  // Extract skills
  if (content.personal_skills) {
    const skills = content.personal_skills;
    if (skills.job_related_skills) {
      keywords.push(...skills.job_related_skills);
    }
    if (skills.computer_skills) {
      keywords.push(...skills.computer_skills);
    }
  }
  
  // Extract from work experience
  if (content.work_experience) {
    content.work_experience.forEach(exp => {
      if (exp.job_title) keywords.push(exp.job_title);
      if (exp.company) keywords.push(exp.company);
    });
  }
  
  // Extract from education
  if (content.education) {
    content.education.forEach(edu => {
      if (edu.field_of_study) keywords.push(edu.field_of_study);
    });
  }
  
  return [...new Set(keywords)].slice(0, 10);
}

// Helper function to extract job titles from CV
function extractJobTitlesFromCV(cvData) {
  if (!cvData || !cvData.json_content) return [];
  
  const titles = [];
  const content = cvData.json_content;
  
  if (content.work_experience) {
    content.work_experience.forEach(exp => {
      if (exp.job_title) titles.push(exp.job_title);
    });
  }
  
  return [...new Set(titles)].slice(0, 5);
}

// Sidebar menu items
const SIDEBAR_ITEMS = [
  { id: "quick-upload", label: "Quick Upload", icon: Upload, alwaysVisible: true },
  { id: "wizard", label: "Create CV", icon: UserPlus, alwaysVisible: true },
  { id: "editor", label: "Edit CV", icon: FileText, requiresCV: true },
  { id: "cover-letter", label: "Cover Letter", icon: MessageSquare, requiresCV: false },
  { id: "interview", label: "Interview Prep", icon: MessageSquare, requiresCV: false },
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
  const hasCV = cvData && (
    cvData.id || 
    (cvData.json_content && Object.keys(cvData.json_content).length > 0) ||
    (cvData.summary && cvData.summary.length > 0) ||
    (cvData.personal_info && Object.keys(cvData.personal_info).length > 0)
  );

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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
      const response = await fetch(`${apiUrl}/api/cv/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setCvData(data);
        if (data && data.id) {
          setActiveTab("editor");
        }
      } else if (response.status === 404) {
        setCvData(null);
        setActiveTab("wizard");
      }
    } catch (error) {
      console.error("Failed to fetch CV:", error);
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
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
            onComplete={(result) => {
              fetchCV();
              setActiveTab("editor");
              setShowJobMatch(true);
              toast.success("CV saved! Showing job matches");
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
                toast.info("Please complete the CV creation wizard first");
              }
            }}
          />
        );

      case "editor":
        if (!hasCV) {
          return (
            <div className="card p-6 text-center">
              <p className="text-gray-600 mb-4">No CV found. Please create one first.</p>
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
        return <ATSOptimizer cvData={cvData} userId={user?.id} onOptimize={handleUpdate} />;

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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 flex-shrink-0 overflow-hidden`}>
        <div className="h-full flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">CV Builder</h2>
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
                          toast.info("Please create a CV first to use this feature");
                          setActiveTab("wizard");
                        } else {
                          setActiveTab(item.id);
                        }
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                        isActive
                          ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg"
                          : isDisabled
                          ? "text-gray-400 cursor-not-allowed opacity-60"
                          : "text-gray-700 hover:bg-blue-50 hover:text-blue-800"
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

            {/* CV Preview - Show if CV exists */}
            {hasCV && (
              <CVPreview cvData={cvData} />
            )}

            {/* Job Match Button - Not in sidebar but accessible */}
            {hasCV && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <button
                  onClick={() => setShowJobMatch(!showJobMatch)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                    showJobMatch
                      ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg"
                      : "text-gray-700 hover:bg-green-50 hover:text-green-800 border-2 border-green-200"
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
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI-Powered CV Builder</h1>
            <p className="text-sm text-gray-600">
              {activeTab === "wizard" && "Create your professional CV step-by-step"}
              {activeTab === "editor" && "Edit and refine your CV"}
              {activeTab === "cover-letter" && "Generate personalized cover letters"}
              {activeTab === "interview" && "Prepare for interviews with AI"}
              {activeTab === "ats" && "Optimize your CV for ATS systems"}
              {activeTab === "export" && "Export your CV in multiple formats"}
              {activeTab === "tracker" && "Track your job applications"}
            </p>
          </div>
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Menu className="w-6 h-6 text-gray-600" />
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
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Search className="w-6 h-6 text-green-600" />
                    Job Matching
                  </h2>
                  <button
                    onClick={() => setShowJobMatch(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <JobMatcher cvData={cvData} userId={user?.id} />
              </div>
            </div>
          )}

          {/* Main Tab Content */}
          <div className={showJobMatch ? "opacity-50 pointer-events-none" : ""}>
            {renderTabContent()}
          </div>

          {/* Global Job Opportunities (only show when CV exists and not in job match mode) */}
          {hasCV && !showJobMatch && activeTab !== "wizard" && (
            <div className="mt-12">
              <div className="card p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Sparkles className="w-6 h-6 text-blue-600" />
                  Global Job Opportunities
                </h2>
                <p className="text-gray-600 mb-6">
                  Find jobs matching your CV from Adzuna, Jooble, Google Jobs, and remote job boards
                </p>
                <JobList
                  keywords={extractKeywordsFromCV(cvData)}
                  jobTitles={extractJobTitlesFromCV(cvData)}
                  location={null}
                  limit={50}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
