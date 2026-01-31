/**
 * CV Preview Component
 * Full formatted, print-ready CV preview
 */
import { useState } from "react";
import {
  Eye,
  EyeOff,
  User,
  Briefcase,
  GraduationCap,
  Award,
  Mail,
  Phone,
  MapPin,
  Download,
  Printer,
} from "lucide-react";
import toast from "react-hot-toast";

// Helper function to strip markdown formatting
const stripMarkdown = (text) => {
  if (!text) return "";
  return text
    .replace(/\*\*(.*?)\*\*/g, "$1") // Bold
    .replace(/\*(.*?)\*/g, "$1") // Italic
    .replace(/__(.*?)__/g, "$1") // Bold alt
    .replace(/_(.*?)_/g, "$1") // Italic alt
    .replace(/`(.*?)`/g, "$1") // Code
    .replace(/#{1,6}\s/g, "") // Headers
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1") // Links
    .replace(/^\s*[-*+]\s+/gm, "") // List markers
    .replace(/^\s*\d+\.\s+/gm, "") // Numbered lists
    .trim();
};

export default function CVPreview({ cvData }) {
  const [expanded, setExpanded] = useState(false);
  const [viewMode, setViewMode] = useState("original"); // "original" or "optimized"

  if (!cvData) return null;

  // Extract PDF URL - check multiple locations (ALWAYS prefer original)
  const originalPdfUrl =
    cvData.original_file_url ||
    cvData.original_pdf_url ||
    cvData.pdf_url ||
    cvData.json_content?.original_file_url ||
    cvData.json_content?.original_pdf_url ||
    cvData.json_content?.pdf_url ||
    (cvData.json_content &&
      typeof cvData.json_content === "object" &&
      cvData.json_content.pdf_url);

  // Get API URL for PDF
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
  const fullPdfUrl = originalPdfUrl
    ? originalPdfUrl.startsWith("http")
      ? originalPdfUrl
      : `${apiUrl}${originalPdfUrl}`
    : null;

  // Check if optimized CV exists
  const hasOptimizedCV =
    cvData.is_optimized || cvData.json_content?.is_optimized || false;

  // Default to showing original PDF if available
  const [showPDF, setShowPDF] = useState(!!fullPdfUrl);

  // Debug logging
  if (process.env.NODE_ENV === "development") {
    console.log("CVPreview - PDF URL check:", {
      originalPdfUrl,
      fullPdfUrl,
      showPDF,
      hasPdfUrl: !!fullPdfUrl,
      viewMode,
      hasOptimizedCV,
      cvDataKeys: Object.keys(cvData || {}),
      jsonContentKeys: cvData.json_content
        ? Object.keys(cvData.json_content)
        : [],
    });
  }

  // Extract data from cvData - use optimized version if in optimized mode, otherwise use original
  const dataSource =
    viewMode === "optimized" && hasOptimizedCV
      ? cvData.json_content || cvData
      : cvData.original_cv_data ||
        cvData.json_content?.original_cv_data ||
        cvData.json_content ||
        cvData;

  const personalInfo = dataSource.personal_info || {};
  const education = dataSource.education || [];
  const workExperience = dataSource.work_experience || [];
  const experience = dataSource.experience || workExperience || [];
  const skills = dataSource.personal_skills || dataSource.skills || {};
  const summary = stripMarkdown(dataSource.summary || "");

  // Get name
  const fullName =
    personalInfo.full_name ||
    `${personalInfo.first_name || ""} ${personalInfo.surname || ""}`.trim() ||
    "Your Name";

  const email = personalInfo.email || "";
  const phone = personalInfo.phone || personalInfo.mobile || "";
  const location = personalInfo.location || personalInfo.address || "";

  // Extract skills - handle different formats
  const jobSkills =
    skills.job_related_skills ||
    skills.technical_skills ||
    skills.technical ||
    [];
  const computerSkills =
    skills.computer_skills || skills.programming_skills || [];
  const languages = skills.languages || [];
  const softSkills = skills.soft || [];

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="border-t border-gray-200 mt-4 pt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-2 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
      >
        <div className="flex items-center gap-2">
          {expanded ? (
            <EyeOff className="w-4 h-4" />
          ) : (
            <Eye className="w-4 h-4" />
          )}
          <span>CV Preview</span>
        </div>
        <span className="text-xs text-gray-500">
          {expanded ? "Hide" : "Show"}
        </span>
      </button>

      {expanded && (
        <div className="mt-3 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-lg">
          {/* Version Toggle: Original vs ATS-Optimized */}
          <div className="bg-gray-50 border-b border-gray-200 p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">
                  CV Version:
                </span>
                <button
                  onClick={() => {
                    setViewMode("original");
                    setShowPDF(!!fullPdfUrl); // Show PDF if available for original
                  }}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewMode === "original"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }`}
                >
                  Original CV
                </button>
                {hasOptimizedCV && (
                  <button
                    onClick={() => {
                      setViewMode("optimized");
                      setShowPDF(false); // Show formatted view for optimized
                    }}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      viewMode === "optimized"
                        ? "bg-green-600 text-white"
                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                    }`}
                  >
                    ATS-Optimized CV
                  </button>
                )}
              </div>
              {fullPdfUrl && viewMode === "original" && (
                <a
                  href={fullPdfUrl}
                  download
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Download Original PDF
                </a>
              )}
            </div>
            {/* Display Mode Toggle (only for original) */}
            {viewMode === "original" && fullPdfUrl && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-gray-600">Display:</span>
                <button
                  onClick={() => setShowPDF(true)}
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                    showPDF
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }`}
                >
                  PDF View
                </button>
                <button
                  onClick={() => setShowPDF(false)}
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                    !showPDF
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }`}
                >
                  Formatted View
                </button>
              </div>
            )}
          </div>

          {/* PDF Preview in iframe - Show original PDF when in original mode */}
          {viewMode === "original" && fullPdfUrl && showPDF ? (
            <div
              className="w-full bg-gray-100"
              style={{
                height: "1200px",
                minHeight: "1200px",
                position: "relative",
              }}
            >
              {/* Primary: Use iframe for PDF display */}
              <iframe
                src={`${fullPdfUrl}#toolbar=0&navpanes=0&scrollbar=0`}
                className="w-full h-full border-0"
                title="CV PDF Preview"
                style={{ minHeight: "1200px", width: "100%", border: "none" }}
                onLoad={() => {
                  console.log("PDF iframe loaded successfully");
                }}
                onError={(e) => {
                  console.error("PDF iframe error, trying embed fallback:", e);
                  // Show embed as fallback
                  const embedElement =
                    document.getElementById("pdf-embed-fallback");
                  if (embedElement) {
                    embedElement.style.display = "block";
                  }
                }}
              />
              {/* Fallback: Use embed if iframe doesn't work */}
              <embed
                src={fullPdfUrl}
                type="application/pdf"
                className="w-full"
                style={{
                  height: "1200px",
                  minHeight: "1200px",
                  display: "none",
                }}
                id="pdf-embed-fallback"
              />
              {/* Alternative: Direct link if both fail */}
              <div className="absolute bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
                <a
                  href={fullPdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white hover:underline"
                >
                  Open PDF in New Tab
                </a>
              </div>
            </div>
          ) : (
            /* Print-ready CV Document - Full Template (Original or Optimized) */
            <div
              className="cv-document bg-white"
              style={{ minHeight: "1000px" }}
            >
              {/* Show indicator if viewing optimized version */}
              {viewMode === "optimized" && (
                <div className="bg-green-50 border-b-2 border-green-500 p-3 text-center">
                  <p className="text-sm font-semibold text-green-800">
                    📊 ATS-Optimized Version - This CV has been enhanced for
                    Applicant Tracking Systems
                  </p>
                </div>
              )}
              {/* Professional Header with Photo */}
              <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-8">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h1 className="text-4xl font-bold mb-3">{fullName}</h1>
                    <div className="flex flex-wrap gap-6 text-blue-100 text-sm">
                      {email && (
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4" />
                          <span>{email}</span>
                        </div>
                      )}
                      {phone && (
                        <div className="flex items-center gap-2">
                          <Phone className="w-4 h-4" />
                          <span>{phone}</span>
                        </div>
                      )}
                      {location && (
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4" />
                          <span>{location}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  {(cvData.photo_url || cvData.json_content?.photo_url) && (
                    <img
                      src={cvData.photo_url || cvData.json_content?.photo_url}
                      alt="Profile"
                      className="w-32 h-32 rounded-full border-4 border-white object-cover shadow-lg"
                    />
                  )}
                </div>
              </div>

              <div className="p-8">
                {/* Professional Summary */}
                {summary && (
                  <section className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4 border-b-2 border-blue-600 pb-2">
                      PROFESSIONAL SUMMARY
                    </h2>
                    <p className="text-gray-700 leading-relaxed text-base">
                      {summary}
                    </p>
                  </section>
                )}

                {/* Work Experience */}
                {experience && experience.length > 0 && (
                  <section className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-5 border-b-2 border-blue-600 pb-2">
                      WORK EXPERIENCE
                    </h2>
                    <div className="space-y-6">
                      {experience.map((exp, idx) => (
                        <div
                          key={idx}
                          className="border-l-4 border-blue-500 pl-5 pb-4"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                              <h3 className="font-bold text-gray-900 text-lg mb-1">
                                {exp.job_title || exp.position || "Position"}
                              </h3>
                              <p className="text-blue-700 font-semibold text-base mb-1">
                                {exp.company || exp.employer || "Company"}
                                {exp.location && ` • ${exp.location}`}
                              </p>
                            </div>
                            <div className="text-gray-600 text-sm font-medium whitespace-nowrap ml-4">
                              {exp.start_date || ""} -{" "}
                              {exp.end_date || "Present"}
                            </div>
                          </div>
                          {exp.description && (
                            <div className="text-gray-700 text-sm leading-relaxed mt-3 whitespace-pre-line">
                              {stripMarkdown(exp.description)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Education */}
                {education && education.length > 0 && (
                  <section className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-5 border-b-2 border-blue-600 pb-2">
                      EDUCATION
                    </h2>
                    <div className="space-y-5">
                      {education.map((edu, idx) => (
                        <div
                          key={idx}
                          className="border-l-4 border-green-500 pl-5"
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <h3 className="font-bold text-gray-900 text-lg mb-1">
                                {edu.degree || edu.qualification || "Degree"}
                              </h3>
                              <p className="text-gray-700 font-semibold text-base mb-1">
                                {edu.institution || edu.school || "Institution"}
                                {edu.field_of_study &&
                                  ` • ${edu.field_of_study}`}
                              </p>
                              {edu.grade && (
                                <p className="text-gray-600 text-sm mt-1">
                                  Grade: {edu.grade}
                                </p>
                              )}
                            </div>
                            {(edu.graduation_year || edu.end_date) && (
                              <div className="text-gray-600 text-sm font-medium whitespace-nowrap ml-4">
                                {edu.graduation_year || edu.end_date}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Skills */}
                {(jobSkills.length > 0 ||
                  computerSkills.length > 0 ||
                  languages.length > 0 ||
                  softSkills.length > 0) && (
                  <section className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-5 border-b-2 border-blue-600 pb-2">
                      SKILLS & COMPETENCIES
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {jobSkills.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-gray-800 mb-3 text-base flex items-center gap-2">
                            <Award className="w-5 h-5 text-blue-600" />
                            Technical Skills
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {jobSkills.map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-3 py-1.5 bg-blue-50 text-blue-800 rounded-md text-sm font-medium border border-blue-200"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {computerSkills.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-gray-800 mb-3 text-base flex items-center gap-2">
                            <Briefcase className="w-5 h-5 text-green-600" />
                            Programming & Tools
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {computerSkills.map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-3 py-1.5 bg-green-50 text-green-800 rounded-md text-sm font-medium border border-green-200"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {softSkills.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-gray-800 mb-3 text-base flex items-center gap-2">
                            <User className="w-5 h-5 text-purple-600" />
                            Soft Skills
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {softSkills.map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-3 py-1.5 bg-purple-50 text-purple-800 rounded-md text-sm font-medium border border-purple-200"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {languages.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-gray-800 mb-3 text-base flex items-center gap-2">
                            <GraduationCap className="w-5 h-5 text-orange-600" />
                            Languages
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {languages.map((lang, idx) => (
                              <span
                                key={idx}
                                className="px-3 py-1.5 bg-orange-50 text-orange-800 rounded-md text-sm font-medium border border-orange-200"
                              >
                                {lang}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </section>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="bg-gray-50 p-4 border-t border-gray-200 flex gap-2 flex-wrap">
            <button
              onClick={handlePrint}
              className="flex-1 min-w-[150px] flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Printer className="w-4 h-4" />
              Print CV
            </button>
            {fullPdfUrl && viewMode === "original" && (
              <button
                onClick={() => {
                  const link = document.createElement("a");
                  link.href = fullPdfUrl;
                  link.download = `Original-CV-${fullName.replace(
                    /\s+/g,
                    "-"
                  )}.pdf`;
                  link.target = "_blank";
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                  toast.success("Original PDF downloaded!");
                }}
                className="flex-1 min-w-[150px] flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
              >
                <Download className="w-4 h-4" />
                Download Original PDF
              </button>
            )}
            {viewMode === "optimized" && hasOptimizedCV && (
              <>
                <button
                  onClick={async () => {
                    try {
                      const apiUrl =
                        process.env.NEXT_PUBLIC_API_URL ||
                        "http://192.168.100.93:8000";
                      const optimizedData = cvData.json_content || cvData;
                      const response = await fetch(
                        `${apiUrl}/api/cv/export-pdf`,
                        {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ cv_data: optimizedData }),
                        }
                      );

                      if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `ATS-Optimized-CV-${fullName.replace(
                          /\s+/g,
                          "-"
                        )}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                        toast.success(
                          "ATS-Optimized CV downloaded successfully!"
                        );
                      } else {
                        toast.error("Failed to download optimized CV");
                      }
                    } catch (error) {
                      console.error("Download error:", error);
                      toast.error("Error downloading optimized CV");
                    }
                  }}
                  className="flex-1 min-w-[150px] flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download PDF
                </button>
                <button
                  onClick={async () => {
                    try {
                      const apiUrl =
                        process.env.NEXT_PUBLIC_API_URL ||
                        "http://192.168.100.93:8000";
                      const optimizedData = cvData.json_content || cvData;
                      const response = await fetch(
                        `${apiUrl}/api/cv/export-docx`,
                        {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ cv_data: optimizedData }),
                        }
                      );

                      if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `ATS-Optimized-CV-${fullName.replace(
                          /\s+/g,
                          "-"
                        )}.docx`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                        toast.success(
                          "ATS-Optimized CV (DOCX) downloaded successfully!"
                        );
                      } else {
                        toast.error("Failed to download optimized CV");
                      }
                    } catch (error) {
                      console.error("Download error:", error);
                      toast.error("Error downloading optimized CV");
                    }
                  }}
                  className="flex-1 min-w-[150px] flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download DOCX
                </button>
              </>
            )}
            {viewMode === "original" && !showPDF && (
              <>
                <button
                  onClick={async () => {
                    try {
                      const apiUrl =
                        process.env.NEXT_PUBLIC_API_URL ||
                        "http://192.168.100.93:8000";
                      const originalData =
                        cvData.original_cv_data ||
                        cvData.json_content?.original_cv_data ||
                        cvData.json_content ||
                        cvData;
                      const response = await fetch(
                        `${apiUrl}/api/cv/export-pdf`,
                        {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ cv_data: originalData }),
                        }
                      );

                      if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `Formatted-CV-${fullName.replace(
                          /\s+/g,
                          "-"
                        )}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                        toast.success("Formatted CV downloaded successfully!");
                      } else {
                        toast.error("Failed to download CV");
                      }
                    } catch (error) {
                      console.error("Download error:", error);
                      toast.error("Error downloading CV");
                    }
                  }}
                  className="flex-1 min-w-[150px] flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download PDF
                </button>
                <button
                  onClick={async () => {
                    try {
                      const apiUrl =
                        process.env.NEXT_PUBLIC_API_URL ||
                        "http://192.168.100.93:8000";
                      const originalData =
                        cvData.original_cv_data ||
                        cvData.json_content?.original_cv_data ||
                        cvData.json_content ||
                        cvData;
                      const response = await fetch(
                        `${apiUrl}/api/cv/export-docx`,
                        {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ cv_data: originalData }),
                        }
                      );

                      if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `Formatted-CV-${fullName.replace(
                          /\s+/g,
                          "-"
                        )}.docx`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                        toast.success("Formatted CV (DOCX) downloaded successfully!");
                      } else {
                        toast.error("Failed to download CV");
                      }
                    } catch (error) {
                      console.error("Download error:", error);
                      toast.error("Error downloading CV");
                    }
                  }}
                  className="flex-1 min-w-[150px] flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download DOCX
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
