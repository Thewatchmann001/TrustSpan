/**
 * Europass-Style CV Wizard with AI Guidance
 * Step-by-step CV creation with AI providing 10+ suggestions at each step
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  User, GraduationCap, Briefcase, Award, 
  Sparkles, Check,
  ChevronRight, ChevronLeft, Lightbulb, Copy, Upload, Image as ImageIcon
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../../contexts/AuthContext";

const STEPS = [
  { id: 1, title: "Personal Information", icon: User, section: "personal_info" },
  { id: 2, title: "Professional Summary", icon: User, section: "summary" },
  { id: 3, title: "Work Experience", icon: Briefcase, section: "experience" },
  { id: 4, title: "Education & Training", icon: GraduationCap, section: "education" },
  { id: 5, title: "Skills & Competences", icon: Award, section: "skills" },
];

export default function EuropassCVWizard({ onComplete, onCancel }) {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState({});
  const [loadingSuggestions, setLoadingSuggestions] = useState({});
  const [skillSuggestions, setSkillSuggestions] = useState({ technical: [], soft: [] });
  const [loadingSkillSuggestions, setLoadingSkillSuggestions] = useState(false);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const debounceTimerRef = useRef({});
  const initializedRef = useRef(false); // Track if we've initialized the form

  // Initialize cvData state - use a function to ensure it only runs once
  const [cvData, setCvData] = useState(() => ({
    personal_info: {
      first_name: user?.full_name?.split(" ")[0] || "",
      surname: user?.full_name?.split(" ").slice(1).join(" ") || "",
      email: user?.email || "",
      phone: "",
      address: "",
      date_of_birth: "",
      nationality: "",
      driving_license: "",
    },
    summary: "",
    experience: [],
    education: [],
    skills: {
      technical: [],
      soft: [],
      languages: [],
    },
    additional: {
      certifications: [],
      projects: [],
      publications: [],
      portfolio_links: "",
    }
  }));

  // Cleanup debounce timers on unmount
  useEffect(() => {
    return () => {
      Object.values(debounceTimerRef.current).forEach(timer => {
        if (timer) clearTimeout(timer);
      });
    };
  }, []);

  // Proactive skill suggestions based on experience and education
  const fetchSkillSuggestions = useCallback(async (cvDataToAnalyze = null) => {
    const data = cvDataToAnalyze || cvData;
    if (!data || (!data.experience?.length && !data.education?.length)) {
      return;
    }

    setLoadingSkillSuggestions(true);
    try {
      // Extract context from experience and education
      const experienceText = data.experience
        ?.map(exp => `${exp.job_title || ""} ${exp.description || ""}`)
        .join(" ") || "";
      const educationText = data.education
        ?.map(edu => `${edu.degree || ""} ${edu.field_of_study || ""}`)
        .join(" ") || "";
      
      const context = `${experienceText} ${educationText}`.trim();
      
      if (context.length < 10) return;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
      const response = await fetch(`${apiUrl}/api/cv/extract-skills`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cv_data: data,
          context: context,
        }),
      });

      const result = await response.json();
      if (result.success && result.skills) {
        setSkillSuggestions({
          technical: result.skills.technical || result.skills.hard_skills || [],
          soft: result.skills.soft || result.skills.soft_skills || [],
        });
      }
    } catch (error) {
      console.error("Error fetching skill suggestions:", error);
    } finally {
      setLoadingSkillSuggestions(false);
    }
  }, [cvData]);

  // Auto-fetch skill suggestions when experience/education is added
  useEffect(() => {
    if (cvData && (cvData.experience?.length > 0 || cvData.education?.length > 0)) {
      const timer = setTimeout(() => {
        fetchSkillSuggestions();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [cvData?.experience?.length, cvData?.education?.length, fetchSkillSuggestions]);

  // Debounced fetch suggestions - now works even with empty values for proactive suggestions
  const fetchSuggestions = useCallback(async (field, currentValue = "", context = {}, forceFetch = false) => {
    // Allow fetching even with empty values if forceFetch is true (for proactive suggestions)
    if (!forceFetch && (!currentValue || currentValue.length < 3)) {
      // Don't clear suggestions if we're just waiting for more input
      if (currentValue.length === 0) {
        return; // Don't fetch or clear for empty values unless forced
      }
      setSuggestions(prev => ({ ...prev, [field]: [] }));
      setLoadingSuggestions(prev => ({ ...prev, [field]: false }));
      return;
    }

    // Clear existing timer for this field
    if (debounceTimerRef.current[field]) {
      clearTimeout(debounceTimerRef.current[field]);
    }

    // Set loading state immediately
    setLoadingSuggestions(prev => ({ ...prev, [field]: true }));

    // Debounce the API call
    debounceTimerRef.current[field] = setTimeout(async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
        const response = await fetch(`${apiUrl}/api/cv/field-suggestions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            field,
            current_value: currentValue,
            context: {
              ...context,
              step: currentStep,
              section: STEPS[currentStep - 1]?.section,
            },
          }),
        });

        const result = await response.json();
        console.log("AI Suggestions Response:", { field, result });
        if (result.success && result.suggestions && Array.isArray(result.suggestions) && result.suggestions.length > 0) {
          setSuggestions(prev => ({ ...prev, [field]: result.suggestions }));
          console.log("✅ Suggestions set for field:", field, "Count:", result.suggestions.length);
        } else {
          console.warn("⚠️ No suggestions received for field:", field, result);
          setSuggestions(prev => ({ ...prev, [field]: [] }));
        }
      } catch (error) {
        console.error("Error fetching suggestions:", error);
        setSuggestions(prev => ({ ...prev, [field]: [] }));
      } finally {
        setLoadingSuggestions(prev => ({ ...prev, [field]: false }));
      }
    }, 800); // 800ms debounce
  }, [currentStep, cvData]);

  // Proactive suggestions when step changes - fetch initial suggestions for empty fields
  useEffect(() => {
    const currentSection = STEPS[currentStep - 1]?.section;
    if (!currentSection) return;

    // Fetch initial suggestions for the current step's main field after a short delay
    const timer = setTimeout(() => {
      if (currentSection === "summary" && (!cvData.summary || cvData.summary.length < 10)) {
        // Fetch proactive suggestions for summary even if empty
        fetchSuggestions("summary", cvData.summary || "", { 
          cvData, 
          step: currentStep,
          proactive: true 
        }, true);
      } else if (currentSection === "personal_info" && !cvData.personal_info.address) {
        // Fetch suggestions for address field
        fetchSuggestions("personal_info.address", "", { 
          cvData, 
          step: currentStep,
          proactive: true 
        }, true);
      }
    }, 1000); // Wait 1 second after step change

    return () => clearTimeout(timer);
  }, [currentStep, fetchSuggestions]);

  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSaveAndComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSaveAndComplete = async () => {
    if (!user?.id) {
      toast.error("Please log in to save your CV");
      return;
    }

    setLoading(true);
    try {
      // Prepare data for AI generation
      const wizardAnswers = {
        full_name: `${cvData.personal_info.first_name} ${cvData.personal_info.surname}`,
        email: cvData.personal_info.email,
        role: cvData.personal_info.first_name, // Will be enhanced by AI
        industry: "",
        experience_level: cvData.experience.length > 0 ? "Mid Level" : "Entry Level",
        years_experience: cvData.experience.length.toString(),
        achievements: cvData.experience.map(e => e.description).join(", "),
        skills: [
          ...cvData.skills.technical,
          ...cvData.skills.soft,
          ...cvData.skills.languages,
        ],
        education: cvData.education.map(e => `${e.degree} - ${e.institution}`).join(", "),
        location: cvData.personal_info.address,
        desired_salary: "",
        portfolio_links: "",
      };

      // Generate CV with AI (optional - can skip if user wants to save directly)
      let generatedCvData = null;
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
        const generateResponse = await fetch(`${apiUrl}/api/cv/generate-from-questions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(wizardAnswers),
        });

        const generateResult = await generateResponse.json();
        
        if (generateResult.success && generateResult.cv_data) {
          generatedCvData = generateResult.cv_data;
          // Merge AI-generated data with user input
          if (generatedCvData.personal_info) {
            cvData.personal_info = { ...cvData.personal_info, ...generatedCvData.personal_info };
          }
          if (generatedCvData.summary && !cvData.summary) {
            cvData.summary = generatedCvData.summary;
          }
        }
      } catch (error) {
        console.warn("AI generation failed, saving user input directly:", error);
      }

      // Upload photo if provided
      let photoUrl = null;
      if (photoFile) {
        const photoFormData = new FormData();
        photoFormData.append("photo", photoFile);
        photoFormData.append("user_id", user.id.toString());
        
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
        const photoResponse = await fetch(`${apiUrl}/api/cv/upload-photo`, {
          method: "POST",
          body: photoFormData,
        });
        
        if (photoResponse.ok) {
          const photoResult = await photoResponse.json();
          photoUrl = photoResult.photo_url;
        }
      }

      // Save to database
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
      const saveResponse = await fetch(`${apiUrl}/api/cv/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          personal_info: {
            first_name: cvData.personal_info.first_name,
            surname: cvData.personal_info.surname,
            email: cvData.personal_info.email,
            phone: cvData.personal_info.phone,
            address: cvData.personal_info.address,
            date_of_birth: cvData.personal_info.date_of_birth,
            nationality: cvData.personal_info.nationality,
            ...cvData.personal_info,
          },
          experience: cvData.experience,
          education: cvData.education,
          skills: cvData.skills,
          awards: cvData.additional.certifications || [],
          publications: cvData.additional.publications || [],
          projects: cvData.additional.projects || [],
          memberships: [],
          photo_url: photoUrl,
        }),
      });

      if (!saveResponse.ok) {
        const errorData = await saveResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save CV");
      }

      const savedCv = await saveResponse.json();
      
      toast.success("CV created and saved successfully!");
      onComplete(savedCv);
    } catch (error) {
      toast.error("Error saving CV: " + error.message);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const updateField = (section, field, value) => {
    setCvData(prev => {
      const updated = { ...prev };
      
      // Handle top-level fields (like summary)
      if (section === "summary" || section === "personal_info") {
        if (section === "summary") {
          updated.summary = value;
        } else {
          updated[section] = {
            ...prev[section],
            [field]: value
          };
        }
      } else {
        updated[section] = {
          ...prev[section],
          [field]: value
        };
      }
      
      return updated;
    });

    // Auto-fetch suggestions - now triggers even with shorter input
    if (field !== "experience" && field !== "education") {
      const fieldPath = section === "summary" ? "summary" : `${section}.${field}`;
      // Fetch suggestions if user has typed at least 3 characters, or if field is empty (proactive)
      if (value.length >= 3 || value.length === 0) {
        fetchSuggestions(fieldPath, value, { cvData, step: currentStep }, value.length === 0);
      }
    }
  };

  const addExperience = () => {
    setCvData(prev => ({
      ...prev,
      experience: [...prev.experience, {
        job_title: "",
        company: "",
        start_date: "",
        end_date: "",
        description: "",
        location: "",
      }]
    }));
  };

  const updateExperience = (index, field, value) => {
    setCvData(prev => {
      const updated = {
        ...prev,
        experience: prev.experience.map((exp, i) => 
          i === index ? { ...exp, [field]: value } : exp
        )
      };

      // Fetch suggestions after state update
      if (field === "description" && value.length > 10) {
        const currentExp = updated.experience[index];
        setTimeout(() => {
          fetchSuggestions(`experience.${index}.description`, value, {
            job_title: currentExp.job_title,
            company: currentExp.company,
          });
        }, 0);
      }

      // Proactive skill suggestions when job title or description changes
      if ((field === "job_title" || field === "description") && value.length > 3) {
        fetchSkillSuggestions(updated);
      }

      return updated;
    });
  };

  const addEducation = () => {
    setCvData(prev => ({
      ...prev,
      education: [...prev.education, {
        degree: "",
        institution: "",
        field_of_study: "",
        start_date: "",
        end_date: "",
        grade: "",
      }]
    }));
  };

  const updateEducation = (index, field, value) => {
    setCvData(prev => ({
      ...prev,
      education: prev.education.map((edu, i) => 
        i === index ? { ...edu, [field]: value } : edu
      )
    }));
  };

  const addSkill = (category, skill) => {
    if (skill && !cvData.skills[category].includes(skill)) {
      setCvData(prev => ({
        ...prev,
        skills: {
          ...prev.skills,
          [category]: [...prev.skills[category], skill]
        }
      }));
    }
  };

  const removeSkill = (category, skill) => {
    setCvData(prev => ({
      ...prev,
      skills: {
        ...prev.skills,
        [category]: prev.skills[category].filter(s => s !== skill)
      }
    }));
  };

  const applySuggestion = (field, suggestion) => {
    const [section, ...fieldParts] = field.split(".");
    const fieldName = fieldParts.join(".");
    
    if (section === "experience") {
      const index = parseInt(fieldParts[0]);
      updateExperience(index, "description", suggestion);
    } else if (section === "education") {
      // Handle education suggestions
    } else {
      updateField(section, fieldName, suggestion);
    }
    
    toast.success("Suggestion applied!");
  };

  const renderStepContent = () => {
    const currentSuggestions = suggestions[Object.keys(suggestions).find(k => k.includes(STEPS[currentStep - 1]?.section))] || [];

    switch (currentStep) {
      case 1: // Personal Information
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-blue-900 mb-1">AI Tip</p>
                  <p className="text-sm text-blue-700">
                    Fill in your personal details. The AI will help you format them professionally and suggest improvements as you type.
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={cvData.personal_info.first_name}
                  onChange={(e) => updateField("personal_info", "first_name", e.target.value)}
                  className="input-field"
                  placeholder="John"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Surname *
                </label>
                <input
                  type="text"
                  value={cvData.personal_info.surname}
                  onChange={(e) => updateField("personal_info", "surname", e.target.value)}
                  className="input-field"
                  placeholder="Doe"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Email *
                </label>
                <input
                  type="email"
                  value={cvData.personal_info.email}
                  onChange={(e) => updateField("personal_info", "email", e.target.value)}
                  className="input-field"
                  placeholder="john.doe@email.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={cvData.personal_info.phone}
                  onChange={(e) => updateField("personal_info", "phone", e.target.value)}
                  className="input-field"
                  placeholder="+1 234 567 8900"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Address
                </label>
                <input
                  type="text"
                  value={cvData.personal_info.address}
                  onChange={(e) => updateField("personal_info", "address", e.target.value)}
                  className="input-field"
                  placeholder="Street, City, Country"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={cvData.personal_info.date_of_birth}
                  onChange={(e) => updateField("personal_info", "date_of_birth", e.target.value)}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-blue-900 mb-2">
                  Nationality
                </label>
                <input
                  type="text"
                  value={cvData.personal_info.nationality}
                  onChange={(e) => updateField("personal_info", "nationality", e.target.value)}
                  className="input-field"
                  placeholder="e.g., American, British"
                />
              </div>
            </div>

            {/* Photo Upload */}
            <div className="md:col-span-2">
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Profile Photo (Optional)
              </label>
              <div className="flex items-center gap-4">
                {photoPreview ? (
                  <div className="relative">
                    <img
                      src={photoPreview}
                      alt="Profile preview"
                      className="w-32 h-32 rounded-full object-cover border-4 border-blue-200"
                    />
                    <button
                      onClick={() => {
                        setPhotoFile(null);
                        setPhotoPreview(null);
                      }}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <div className="w-32 h-32 rounded-full bg-gray-100 border-4 border-dashed border-gray-300 flex items-center justify-center">
                    <ImageIcon className="w-8 h-8 text-gray-400" />
                  </div>
                )}
                <div className="flex-1">
                  <label className="btn-secondary cursor-pointer inline-flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    {photoFile ? "Change Photo" : "Upload Photo"}
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) {
                          if (file.size > 5 * 1024 * 1024) {
                            toast.error("Photo must be less than 5MB");
                            return;
                          }
                          setPhotoFile(file);
                          const reader = new FileReader();
                          reader.onloadend = () => {
                            setPhotoPreview(reader.result);
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                    />
                  </label>
                  <p className="text-xs text-gray-500 mt-2">
                    Recommended: Square image, max 5MB (JPG, PNG)
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 2: // Professional Summary
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-blue-900 mb-1">AI Tip</p>
                  <p className="text-sm text-blue-700">
                    Write 2-3 sentences about your professional background. The AI will provide 10+ suggestions to make it more impactful and ATS-friendly.
                  </p>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Professional Summary *
              </label>
              <textarea
                value={cvData.summary}
                onFocus={() => {
                  // Fetch proactive suggestions when field is focused, even if empty
                  if (!cvData.summary || cvData.summary.length < 10) {
                    fetchSuggestions("summary", cvData.summary || "", {
                      cvData,
                      step: currentStep,
                      proactive: true
                    }, true);
                  }
                }}
                onChange={(e) => {
                  const value = e.target.value;
                  setCvData(prev => ({ ...prev, summary: value }));
                  // Fetch suggestions as user types (reduced threshold from 10 to 3)
                  if (value.length >= 3) {
                    fetchSuggestions("summary", value, {
                      cvData,
                      step: currentStep,
                      role: cvData.personal_info.first_name,
                      experience: cvData.experience.length,
                    });
                  }
                }}
                className="input-field min-h-[150px]"
                placeholder="e.g., Experienced software engineer with 5+ years in full-stack development..."
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                {cvData.summary.length} characters
              </p>
            </div>

            {/* AI Suggestions */}
            {loadingSuggestions["summary"] && (
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
                  <span className="text-purple-700 font-medium">AI is analyzing your text and generating suggestions...</span>
                </div>
              </div>
            )}
            {!loadingSuggestions["summary"] && suggestions && suggestions["summary"] && Array.isArray(suggestions["summary"]) && suggestions["summary"].length > 0 && (
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h4 className="font-semibold text-gray-900">
                    AI Suggestions ({suggestions["summary"].length})
                  </h4>
                </div>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {suggestions["summary"].slice(0, 15).map((suggestion, idx) => (
                    <div
                      key={idx}
                      className="bg-white border border-purple-200 rounded p-3 hover:border-purple-400 transition-colors"
                    >
                      <p className="text-sm text-gray-800 mb-2">{suggestion}</p>
                      <button
                        onClick={() => applySuggestion("summary", suggestion)}
                        className="btn-secondary text-xs flex items-center gap-1"
                      >
                        <Copy className="w-3 h-3" />
                        Use This
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 3: // Work Experience
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-blue-900 mb-1">AI Tip</p>
                  <p className="text-sm text-blue-700">
                    Add your work experience. For each role, describe your achievements with numbers and metrics. AI will suggest 10+ powerful bullet points.
                  </p>
                </div>
              </div>
            </div>

            {cvData.experience.length === 0 && (
              <button
                onClick={addExperience}
                className="btn-primary w-full"
              >
                + Add Work Experience
              </button>
            )}

            {cvData.experience.map((exp, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-6 bg-white">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900">Experience #{idx + 1}</h4>
                  <button
                    onClick={() => {
                      setCvData(prev => ({
                        ...prev,
                        experience: prev.experience.filter((_, i) => i !== idx)
                      }));
                    }}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Job Title *
                    </label>
                    <input
                      type="text"
                      value={exp.job_title}
                      onChange={(e) => updateExperience(idx, "job_title", e.target.value)}
                      className="input-field"
                      placeholder="Software Engineer"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Company *
                    </label>
                    <input
                      type="text"
                      value={exp.company}
                      onChange={(e) => updateExperience(idx, "company", e.target.value)}
                      className="input-field"
                      placeholder="Google"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Start Date
                    </label>
                    <input
                      type="month"
                      value={exp.start_date}
                      onChange={(e) => updateExperience(idx, "start_date", e.target.value)}
                      className="input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      End Date (leave empty if current)
                    </label>
                    <input
                      type="month"
                      value={exp.end_date}
                      onChange={(e) => updateExperience(idx, "end_date", e.target.value)}
                      className="input-field"
                      placeholder="Present"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold text-blue-900 mb-2">
                    Description & Achievements *
                  </label>
                  <textarea
                    value={exp.description}
                    onChange={(e) => {
                      updateExperience(idx, "description", e.target.value);
                      if (e.target.value.length > 20) {
                        fetchSuggestions(`experience.${idx}.description`, e.target.value, {
                          job_title: exp.job_title,
                          company: exp.company,
                        });
                      }
                    }}
                    className="input-field min-h-[120px]"
                    placeholder="Describe your responsibilities and achievements. Use numbers and metrics when possible..."
                    required
                  />
                </div>

                {/* AI Suggestions for this experience */}
                {loadingSuggestions[`experience.${idx}.description`] && (
                  <div className="mt-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
                      <span className="text-purple-700 font-medium">AI is analyzing your description...</span>
                    </div>
                  </div>
                )}
                {!loadingSuggestions[`experience.${idx}.description`] && suggestions[`experience.${idx}.description`] && suggestions[`experience.${idx}.description`].length > 0 && (
                  <div className="mt-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles className="w-5 h-5 text-purple-600" />
                      <h4 className="font-semibold text-gray-900">
                        AI Suggestions ({suggestions[`experience.${idx}.description`].length})
                      </h4>
                    </div>
                    <div className="space-y-2 max-h-[250px] overflow-y-auto">
                      {suggestions[`experience.${idx}.description`].slice(0, 12).map((suggestion, sIdx) => (
                        <div
                          key={sIdx}
                          className="bg-white border border-purple-200 rounded p-3 hover:border-purple-400 transition-colors"
                        >
                          <p className="text-sm text-gray-800 mb-2">{suggestion}</p>
                          <button
                            onClick={() => applySuggestion(`experience.${idx}.description`, suggestion)}
                            className="btn-secondary text-xs flex items-center gap-1"
                          >
                            <Copy className="w-3 h-3" />
                            Use This
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            <button
              onClick={addExperience}
              className="btn-secondary w-full"
            >
              + Add Another Experience
            </button>
          </div>
        );

      case 4: // Education
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-blue-900 mb-1">AI Tip</p>
                  <p className="text-sm text-blue-700">
                    Add your educational background. Include degrees, institutions, and relevant coursework.
                  </p>
                </div>
              </div>
            </div>

            {cvData.education.length === 0 && (
              <button
                onClick={addEducation}
                className="btn-primary w-full"
              >
                + Add Education
              </button>
            )}

            {cvData.education.map((edu, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-6 bg-white">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900">Education #{idx + 1}</h4>
                  <button
                    onClick={() => {
                      setCvData(prev => ({
                        ...prev,
                        education: prev.education.filter((_, i) => i !== idx)
                      }));
                    }}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Degree/Qualification *
                    </label>
                    <input
                      type="text"
                      value={edu.degree}
                      onChange={(e) => updateEducation(idx, "degree", e.target.value)}
                      className="input-field"
                      placeholder="Bachelor of Science"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Institution *
                    </label>
                    <input
                      type="text"
                      value={edu.institution}
                      onChange={(e) => updateEducation(idx, "institution", e.target.value)}
                      className="input-field"
                      placeholder="University Name"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Field of Study
                    </label>
                    <input
                      type="text"
                      value={edu.field_of_study}
                      onChange={(e) => updateEducation(idx, "field_of_study", e.target.value)}
                      className="input-field"
                      placeholder="Computer Science"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Grade/GPA
                    </label>
                    <input
                      type="text"
                      value={edu.grade}
                      onChange={(e) => updateEducation(idx, "grade", e.target.value)}
                      className="input-field"
                      placeholder="3.8/4.0 or First Class"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      Start Date
                    </label>
                    <input
                      type="month"
                      value={edu.start_date}
                      onChange={(e) => updateEducation(idx, "start_date", e.target.value)}
                      className="input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">
                      End Date
                    </label>
                    <input
                      type="month"
                      value={edu.end_date}
                      onChange={(e) => updateEducation(idx, "end_date", e.target.value)}
                      className="input-field"
                    />
                  </div>
                </div>
              </div>
            ))}

            <button
              onClick={addEducation}
              className="btn-secondary w-full"
            >
              + Add Another Education
            </button>
          </div>
        );

      case 5: // Skills
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-blue-900 mb-1">AI Tip</p>
                  <p className="text-sm text-blue-700">
                    Add your skills. The AI will suggest relevant skills based on your experience and industry trends.
                  </p>
                </div>
              </div>
            </div>

            {/* Technical Skills */}
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Technical Skills
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      addSkill("technical", e.target.value);
                      e.target.value = "";
                    }
                  }}
                  className="input-field flex-1"
                  placeholder="Type skill and press Enter (e.g., Python, React, AWS)"
                />
                <button
                  onClick={(e) => {
                    const input = e.target.previousElementSibling;
                    if (input?.value) {
                      addSkill("technical", input.value);
                      input.value = "";
                    }
                  }}
                  className="btn-primary"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {cvData.skills.technical.map((skill, idx) => (
                  <span
                    key={idx}
                    className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                  >
                    {skill}
                    <button
                      onClick={() => removeSkill("technical", skill)}
                      className="text-blue-600 hover:text-red-600"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Soft Skills */}
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Soft Skills
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      addSkill("soft", e.target.value);
                      e.target.value = "";
                    }
                  }}
                  className="input-field flex-1"
                  placeholder="Type skill and press Enter (e.g., Leadership, Communication)"
                />
                <button
                  onClick={(e) => {
                    const input = e.target.previousElementSibling;
                    if (input?.value) {
                      addSkill("soft", input.value);
                      input.value = "";
                    }
                  }}
                  className="btn-primary"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {cvData.skills.soft.map((skill, idx) => (
                  <span
                    key={idx}
                    className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                  >
                    {skill}
                    <button
                      onClick={() => removeSkill("soft", skill)}
                      className="text-green-600 hover:text-red-600"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Languages */}
            <div>
              <label className="block text-sm font-bold text-blue-900 mb-2">
                Languages
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      addSkill("languages", e.target.value);
                      e.target.value = "";
                    }
                  }}
                  className="input-field flex-1"
                  placeholder="Type language and press Enter (e.g., English - Native, Spanish - Fluent)"
                />
                <button
                  onClick={(e) => {
                    const input = e.target.previousElementSibling;
                    if (input?.value) {
                      addSkill("languages", input.value);
                      input.value = "";
                    }
                  }}
                  className="btn-primary"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {cvData.skills.languages.map((skill, idx) => (
                  <span
                    key={idx}
                    className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                  >
                    {skill}
                    <button
                      onClick={() => removeSkill("languages", skill)}
                      className="text-purple-600 hover:text-red-600"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="card max-w-4xl mx-auto">
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
                        ? "bg-blue-600 text-white shadow-lg"
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
                  <span className="text-xs mt-2 text-center hidden md:block font-medium">
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
              {loading ? "Saving..." : "Save & Complete"}
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

