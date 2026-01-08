/**
 * Quick Upload Component - LinkedIn PDF Upload
 * Allows users to upload LinkedIn CV PDF for instant AI parsing
 */
import { useState } from "react";
import { Upload, FileText, Sparkles, CheckCircle, AlertCircle, Loader } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../../contexts/AuthContext";

export default function QuickUpload({ onComplete, onCancel }) {
  const { user } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [jobMatches, setJobMatches] = useState([]);

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

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000"}/api/cv/upload-linkedin-pdf", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Upload failed");
      }

      if (result.success) {
        setExtractedData(result.cv_data);
        setJobMatches(result.job_matches || []);
        toast.success(`CV uploaded! Found ${result.match_count} job matches`);
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

          {/* Extracted Data Preview */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              Extracted Information
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
                <p className="font-medium text-gray-900">{extractedData.experience?.length || 0} positions</p>
              </div>
              <div>
                <p className="text-gray-600">Education</p>
                <p className="font-medium text-gray-900">{extractedData.education?.length || 0} degrees</p>
              </div>
              <div>
                <p className="text-gray-600">Skills</p>
                <p className="font-medium text-gray-900">
                  {(extractedData.skills?.technical?.length || 0) + (extractedData.skills?.soft?.length || 0)} skills
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
              <h3 className="font-semibold text-gray-900 mb-3">Top Job Matches</h3>
              <div className="space-y-3">
                {jobMatches.slice(0, 5).map((job, idx) => (
                  <div key={idx} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900 flex-1">{job.title}</h4>
                      {/* Source Badge with distinct colors */}
                      {job.source && (
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                          job.source === 'RemoteOK' 
                            ? 'bg-green-100 text-green-700' 
                            : job.source === 'Freelancer.com'
                            ? 'bg-purple-100 text-purple-700'
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          {job.source}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{job.company} • {job.location}</p>
                    
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
                      <div className="flex flex-wrap gap-1">
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
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => onComplete(extractedData)}
              className="btn-primary flex-1"
            >
              View All Matches
            </button>
            <button
              onClick={() => {
                setExtractedData(null);
                setFile(null);
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
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
            dragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
          }`}
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
