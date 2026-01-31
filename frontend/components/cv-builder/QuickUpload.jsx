/**
 * Quick Upload Component - LinkedIn PDF Upload
 * Allows users to upload LinkedIn CV PDF for instant AI parsing
 */
import { useState } from "react";
import { Upload, FileText, Sparkles, CheckCircle, AlertCircle, Loader, ExternalLink } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../../contexts/AuthContext";
import { useJobs } from "../../contexts/JobsContext";

// Debug logger helper
const logger = {
  debug: (...args) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('[QuickUpload]', ...args);
    }
  }
};

export default function QuickUpload({ onComplete, onCancel }) {
  const { user } = useAuth();
  const { setJobs } = useJobs(); // CRITICAL: Store jobs in global context for instant access in CV Editor
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [jobMatches, setJobMatches] = useState([]);
  const [atsScore, setAtsScore] = useState(null);
  const [showAllJobs, setShowAllJobs] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    // Validate file type
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      toast.error("Please upload a PDF file");
      return;
    }

    // Validate file size (10MB max)
    if (selectedFile.size > 10 * 1024 * 1024) {
      toast.error("File size must be less than 10MB");
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file || !user?.id) {
      toast.error("Please select a file and ensure you're logged in");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("pdf_file", file);
      formData.append("user_id", user.id.toString());

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
      const endpoint = apiUrl + "/api/cv/upload-linkedin-pdf";
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Upload failed");
      }

      if (result.success) {
        // Normalize the data structure to ensure all fields are accessible
        const normalizedData = {
          ...result.cv_data,
          // Ensure experience is accessible
          experience: result.cv_data.experience || result.cv_data.work_experience || [],
          work_experience: result.cv_data.work_experience || result.cv_data.experience || [],
          // Ensure skills are accessible
          skills: result.cv_data.skills || result.cv_data.personal_skills || { technical: [], soft: [], languages: [] },
          personal_skills: result.cv_data.personal_skills || result.cv_data.skills || { technical: [], soft: [], languages: [] },
          // Include PDF URL
          pdf_url: result.pdf_url || result.cv_data.pdf_url,
        };
        
        setExtractedData(normalizedData);
        const jobs = result.job_matches || [];
        setJobMatches(jobs);
        setAtsScore(result.ats_score || null);
        
        // CRITICAL: Store jobs in global context for instant access in CV Editor
        // This prevents re-fetching when user navigates to CV Editor
        // WHY: Jobs are already matched and stored on backend, no need to re-fetch
        setJobs(jobs);
        logger.debug('Stored jobs in global context:', jobs.length);
        
        toast.success(`CV improved and uploaded! ATS Score: ${result.ats_score || 'N/A'}% | Found ${result.match_count || 0} job matches`);
      } else {
        throw new Error(result.message || "Upload failed");
      }
    } catch (error) {
      console.error("Upload error:", error);
      toast.error(error.message || "Failed to upload CV");
    } finally {
      setUploading(false);
    }
  };

  if (extractedData) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-8">
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">CV Uploaded Successfully!</h2>
              <p className="text-gray-600">AI has extracted your information</p>
            </div>
          </div>

          {/* ATS Score & Improvements */}
          {atsScore !== null && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6 mb-6 border border-green-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-green-600" />
                  CV Improved with ATS Optimization
                </h3>
                <div className="text-right">
                  <div className="text-3xl font-bold text-green-600">{atsScore}%</div>
                  <div className="text-sm text-gray-600">ATS Score</div>
                </div>
              </div>
              <p className="text-sm text-gray-700">
                Your CV has been automatically improved using ATS optimization best practices. 
                It now scores highly on Applicant Tracking System compatibility.
              </p>
            </div>
          )}

          {/* Extracted Data Preview */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              Extracted & Improved Information
            </h3>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Name</p>
                <p className="font-medium text-gray-900">
                  {extractedData.personal_info?.first_name} {extractedData.personal_info?.surname}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Email</p>
                <p className="font-medium text-gray-900">{extractedData.personal_info?.email || "N/A"}</p>
              </div>
              <div>
                <p className="text-gray-600">Experience</p>
                <p className="font-medium text-gray-900">
                  {(() => {
                    const exp = extractedData.experience || extractedData.work_experience || [];
                    const count = Array.isArray(exp) ? exp.length : 0;
                    if (count === 0 && process.env.NODE_ENV === 'development') {
                      console.warn('No experience found in:', { 
                        hasExperience: !!extractedData.experience,
                        hasWorkExperience: !!extractedData.work_experience,
                        extractedDataKeys: Object.keys(extractedData)
                      });
                    }
                    return count;
                  })()} positions
                </p>
              </div>
              <div>
                <p className="text-gray-600">Education</p>
                <p className="font-medium text-gray-900">
                  {(() => {
                    const edu = extractedData.education || [];
                    const count = Array.isArray(edu) ? edu.length : 0;
                    if (count === 0 && process.env.NODE_ENV === 'development') {
                      console.warn('No education found in:', { 
                        hasEducation: !!extractedData.education,
                        extractedDataKeys: Object.keys(extractedData)
                      });
                    }
                    return count;
                  })()} degrees
                </p>
              </div>
              <div>
                <p className="text-gray-600">Skills</p>
                <p className="font-medium text-gray-900">
                  {(() => {
                    const skills = extractedData.skills || extractedData.personal_skills || {};
                    if (typeof skills !== 'object') return 0;
                    const technical = skills.technical || skills.job_related_skills || skills.technical_skills || [];
                    const soft = skills.soft || skills.social_skills || [];
                    const computer = skills.computer_skills || skills.programming_skills || [];
                    const total = technical.length + soft.length + computer.length;
                    if (total === 0 && process.env.NODE_ENV === 'development') {
                      console.warn('No skills found in:', { 
                        skillsType: typeof skills,
                        skillsKeys: Object.keys(skills),
                        extractedDataKeys: Object.keys(extractedData)
                      });
                    }
                    return total;
                  })()} skills
                </p>
              </div>
              <div>
                <p className="text-gray-600">Job Matches</p>
                <p className="font-medium text-green-600">{jobMatches.length} matches found</p>
              </div>
            </div>
          </div>

          {/* Job Matches Preview */}
          {jobMatches.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">
                  {showAllJobs ? `All Job Matches (${jobMatches.length})` : `Top Job Matches (${jobMatches.length})`}
                </h3>
                {jobMatches.length > 5 && (
                  <button
                    onClick={() => setShowAllJobs(!showAllJobs)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {showAllJobs ? "Show Less" : "View All Matches"}
                  </button>
                )}
              </div>
              <div className="space-y-3">
                {(() => {
                  // Ensure we show ALL jobs when showAllJobs is true, otherwise show first 5
                  const jobsToShow = showAllJobs ? jobMatches : jobMatches.slice(0, 5);
                  
                  if (process.env.NODE_ENV === 'development') {
                    console.log(`[QuickUpload] Showing ${jobsToShow.length} jobs out of ${jobMatches.length} total (showAllJobs: ${showAllJobs})`);
                  }
                  
                  if (jobsToShow.length === 0) {
                    return (
                      <div className="text-center py-8 text-gray-500">
                        <p>No jobs to display</p>
                      </div>
                    );
                  }
                  
                  return jobsToShow.map((job, idx) => {
                    // Create unique key based on title, company, source, and index
                    const jobKey = `${job.title || ''}-${job.company || job.company_name || ''}-${job.source || ''}-${idx}`;
                    
                    return (
                      <div key={jobKey} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900 flex-1">{job.title || job.job_title || 'Job Title'}</h4>
                          {/* Source Badge with distinct colors */}
                          {job.source && (
                            <span className={
                              "text-xs font-semibold px-2.5 py-1 rounded-full " +
                              (job.source === 'RemoteOK' 
                                ? 'bg-green-100 text-green-700' 
                                : job.source === 'Freelancer.com'
                                ? 'bg-purple-100 text-purple-700'
                                : job.source === 'Arbeitnow'
                                ? 'bg-orange-100 text-orange-700'
                                : job.source === 'Adzuna'
                                ? 'bg-cyan-100 text-cyan-700'
                                : 'bg-blue-100 text-blue-700')
                            }>
                              {job.source}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{job.company || job.company_name || 'Company'} • {job.location || 'Location not specified'}</p>
                        
                        {/* Job type and salary */}
                        <div className="flex flex-wrap gap-2 mb-2">
                          {job.type && (
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                              {job.type}
                            </span>
                          )}
                          {job.salary && (
                            <span className="text-xs bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded font-medium">
                              💰 {job.salary}
                            </span>
                          )}
                        </div>
                        
                        {/* Skills preview */}
                        {job.skills && job.skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-3">
                            {job.skills.slice(0, 4).map((skill, skillIdx) => (
                              <span key={skillIdx} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded">
                                {skill}
                              </span>
                            ))}
                            {job.skills.length > 4 && (
                              <span className="text-xs text-gray-400">+{job.skills.length - 4} more</span>
                            )}
                          </div>
                        )}
                        
                        {/* Apply Now Button */}
                        {(job.url || job.applyUrl || job.link) && (
                          <a
                            href={job.url || job.applyUrl || job.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block w-full mt-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-center px-4 py-2 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-semibold text-sm"
                          >
                            Apply Now →
                          </a>
                        )}
                      </div>
                    );
                  });
                })()}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={async () => {
                // Normalize data structure before passing to editor
                const normalizedData = {
                  ...extractedData,
                  // Ensure both experience formats exist
                  experience: extractedData.experience || extractedData.work_experience || [],
                  work_experience: extractedData.work_experience || extractedData.experience || [],
                  // Ensure both skills formats exist
                  skills: extractedData.skills || extractedData.personal_skills || { technical: [], soft: [], languages: [] },
                  personal_skills: extractedData.personal_skills || extractedData.skills || { technical: [], soft: [], languages: [] },
                  // Include PDF URL
                  pdf_url: extractedData.pdf_url,
                  // Include other metadata
                  job_matches: jobMatches,
                  match_count: jobMatches.length,
                  ats_score: atsScore
                };
                
                // Pass all data including job matches to the editor
                onComplete(normalizedData);
              }}
              className="btn-primary flex-1"
            >
              Continue to CV Editor
            </button>
            <button
              onClick={() => {
                setExtractedData(null);
                setFile(null);
                setJobMatches([]);
                setAtsScore(null);
                setShowAllJobs(false);
              }}
              className="btn-secondary"
            >
              Upload Another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card p-8">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full mb-4">
            <Upload className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Quick CV Upload</h2>
          <p className="text-gray-600">
            Upload your LinkedIn CV PDF and let AI do the magic ✨
          </p>
        </div>

        {/* Drag and Drop Zone */}
        <div
          className={
            "border-2 border-dashed rounded-lg p-12 text-center transition-all " +
            (dragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-blue-400 hover:bg-gray-50")
          }
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {file ? (
            <div className="flex flex-col items-center gap-3">
              <FileText className="w-12 h-12 text-blue-600" />
              <div>
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={() => setFile(null)}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
          ) : (
            <div>
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-700 font-medium mb-2">
                Drag and drop your LinkedIn CV PDF here
              </p>
              <p className="text-sm text-gray-500 mb-4">or</p>
              <label className="btn-primary cursor-pointer inline-block">
                Browse Files
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf"
                  onChange={handleChange}
                />
              </label>
              <p className="text-xs text-gray-500 mt-4">
                Maximum file size: 10MB • PDF only
              </p>
            </div>
          )}
        </div>

        {/* Upload Button */}
        {file && (
          <div className="mt-6 flex gap-3">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Processing with AI...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Upload & Extract
                </>
              )}
            </button>
            <button
              onClick={onCancel}
              className="btn-secondary"
              disabled={uploading}
            >
              Cancel
            </button>
          </div>
        )}

        {/* Info */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900">
              <p className="font-semibold mb-1">What happens next?</p>
              <ul className="space-y-1 text-blue-800">
                <li>• AI extracts your personal info, experience, education & skills</li>
                <li>• Automatically matches you to relevant jobs</li>
                <li>• Creates your TrustBridge profile instantly</li>
                <li>• Takes only 5-10 seconds!</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
