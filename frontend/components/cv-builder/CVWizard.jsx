/**
 * Guided CV Creation Wizard
 * Step-by-step questionnaire to gather CV information
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  User, GraduationCap, Briefcase, Award, 
  MapPin, DollarSign, Link as LinkIcon,
  ChevronRight, ChevronLeft, Check
} from "lucide-react";
import toast from "react-hot-toast";

const STEPS = [
  { id: 1, title: "Role & Industry", icon: User },
  { id: 2, title: "Experience", icon: Briefcase },
  { id: 3, title: "Skills", icon: Award },
  { id: 4, title: "Education", icon: GraduationCap },
  { id: 5, title: "Location & Salary", icon: MapPin },
  { id: 6, title: "Portfolio & Links", icon: LinkIcon },
];

export default function CVWizard({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [answers, setAnswers] = useState({
    role: "",
    industry: "",
    experience_level: "",
    years_experience: "",
    achievements: "",
    skills: [],
    education: "",
    location: "",
    desired_salary: "",
    portfolio_links: "",
    full_name: "",
    email: "",
  });
  const [loading, setLoading] = useState(false);

  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      // Call API to generate CV
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000"}/api/cv/generate-from-questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(answers),
      });

      const result = await response.json();
      
      if (result.success) {
        toast.success("CV generated successfully!");
        onComplete(result.cv_data);
      } else {
        toast.error("Failed to generate CV");
      }
    } catch (error) {
      toast.error("Error generating CV");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const updateAnswer = (field, value) => {
    setAnswers(prev => ({ ...prev, [field]: value }));
  };

  const addSkill = (skill) => {
    if (skill && !answers.skills.includes(skill)) {
      setAnswers(prev => ({
        ...prev,
        skills: [...prev.skills, skill]
      }));
    }
  };

  const removeSkill = (skill) => {
    setAnswers(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s !== skill)
    }));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                What role are you applying for?
              </label>
              <input
                type="text"
                value={answers.role}
                onChange={(e) => updateAnswer("role", e.target.value)}
                className="input-field"
                placeholder="e.g., Software Engineer, Product Manager"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Industry
              </label>
              <select
                value={answers.industry}
                onChange={(e) => updateAnswer("industry", e.target.value)}
                className="input-field"
              >
                <option value="">Select industry</option>
                <option value="Technology">Technology</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Finance">Finance</option>
                <option value="Education">Education</option>
                <option value="Agriculture">Agriculture</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={answers.full_name}
                onChange={(e) => updateAnswer("full_name", e.target.value)}
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
                value={answers.email}
                onChange={(e) => updateAnswer("email", e.target.value)}
                className="input-field"
                placeholder="john.doe@email.com"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Experience Level
              </label>
              <select
                value={answers.experience_level}
                onChange={(e) => updateAnswer("experience_level", e.target.value)}
                className="input-field"
              >
                <option value="">Select level</option>
                <option value="Entry Level">Entry Level (0-2 years)</option>
                <option value="Mid Level">Mid Level (3-5 years)</option>
                <option value="Senior Level">Senior Level (6-10 years)</option>
                <option value="Executive">Executive (10+ years)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Years of Experience
              </label>
              <input
                type="number"
                value={answers.years_experience}
                onChange={(e) => updateAnswer("years_experience", e.target.value)}
                className="input-field"
                placeholder="5"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Key Achievements (comma-separated)
              </label>
              <textarea
                value={answers.achievements}
                onChange={(e) => updateAnswer("achievements", e.target.value)}
                className="input-field min-h-[120px]"
                placeholder="e.g., Increased sales by 30%, Led team of 5 developers, Launched 3 products"
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Add Skills
              </label>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      addSkill(e.target.value);
                      e.target.value = "";
                    }
                  }}
                  className="input-field flex-1"
                  placeholder="Type skill and press Enter"
                />
                <button
                  onClick={() => {
                    const input = document.querySelector('input[placeholder="Type skill and press Enter"]');
                    if (input?.value) {
                      addSkill(input.value);
                      input.value = "";
                    }
                  }}
                  className="btn-primary"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {answers.skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                  >
                    {skill}
                    <button
                      onClick={() => removeSkill(skill)}
                      className="text-blue-600 hover:text-red-600"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Education
              </label>
              <textarea
                value={answers.education}
                onChange={(e) => updateAnswer("education", e.target.value)}
                className="input-field min-h-[120px]"
                placeholder="e.g., Bachelor of Science in Computer Science, University Name, 2020"
              />
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Location
              </label>
              <input
                type="text"
                value={answers.location}
                onChange={(e) => updateAnswer("location", e.target.value)}
                className="input-field"
                placeholder="e.g., San Francisco, CA or Remote"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Desired Salary (Optional)
              </label>
              <input
                type="text"
                value={answers.desired_salary}
                onChange={(e) => updateAnswer("desired_salary", e.target.value)}
                className="input-field"
                placeholder="e.g., $80,000 - $100,000"
              />
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Portfolio Links (comma-separated)
              </label>
              <textarea
                value={answers.portfolio_links}
                onChange={(e) => updateAnswer("portfolio_links", e.target.value)}
                className="input-field min-h-[120px]"
                placeholder="e.g., https://github.com/username, https://portfolio.com"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="card max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            
            return (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                      isActive
                        ? "bg-blue-600 text-white"
                        : isCompleted
                        ? "bg-green-500 text-white"
                        : "bg-gray-200 text-gray-600"
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-6 h-6" />
                    ) : (
                      <Icon className="w-6 h-6" />
                    )}
                  </div>
                  <span className="text-xs mt-2 text-center hidden md:block">
                    {step.title}
                  </span>
                </div>
                {idx < STEPS.length - 1 && (
                  <div
                    className={`h-1 flex-1 mx-2 ${
                      isCompleted ? "bg-green-500" : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {STEPS[currentStep - 1].title}
          </h2>
          {renderStepContent()}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
        <button
          onClick={handleBack}
          disabled={currentStep === 1}
          className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={handleNext}
          disabled={loading}
          className="btn-primary flex items-center gap-2"
        >
          {currentStep === STEPS.length ? (
            <>
              {loading ? "Generating..." : "Generate CV"}
              <Check className="w-4 h-4" />
            </>
          ) : (
            <>
              Next
              <ChevronRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}

