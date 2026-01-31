/**
 * JobList Component
 * Displays job listings from multiple sources with Apply buttons
 * 
 * DATA FLOW FIX: Uses global JobsContext to get pre-matched jobs instantly
 * WHY: Prevents re-fetching when navigating from Quick Upload → CV Editor
 * Only fetches if no jobs in context (fallback for direct navigation)
 */
import { useState, useEffect } from 'react';
import { Briefcase, MapPin, Building2, ExternalLink, Loader, Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { cvAPI } from '../lib/api';
import toast from 'react-hot-toast';
import { useJobs } from '../contexts/JobsContext';

export default function JobList({ keywords = [], jobTitles = [], location = null, limit = 50, userId = null }) {
  const { matchedJobs, setJobs, setResourceLoading, setJobResources, getJobResources, isResourceLoading } = useJobs();
  
  // Use jobs from context FIRST (instant, no loading)
  // Only use local state if context is empty (fallback)
  const [jobs, setLocalJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchLocation, setSearchLocation] = useState(location || '');
  
  // Use context jobs if available, otherwise use local
  const displayJobs = matchedJobs.length > 0 ? matchedJobs : jobs;

  useEffect(() => {
    // CRITICAL FIX: Only fetch if no jobs in context
    // If jobs exist in context (from Quick Upload), use them instantly (NO FETCH)
    // WHY: Prevents unnecessary API calls and ensures instant display
    if (matchedJobs.length > 0) {
      console.log('[JobList] Using jobs from context (instant, no fetch):', matchedJobs.length);
      return; // Use context jobs, no fetch needed
    }
    
    // Fallback: Fetch jobs if context is empty (direct navigation to CV Editor)
    console.log('[JobList] No jobs in context, fetching...');
    fetchJobs();
  }, [keywords, jobTitles, location, userId, matchedJobs.length]); // Added matchedJobs.length to detect context updates

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // CRITICAL: If userId is provided, backend will return stored matches from Quick Upload
      // Don't use default keywords if userId is available - let backend use stored matches
      // Only use default keywords as fallback if userId is not available
      const searchKeywords = (keywords && keywords.length > 0) 
        ? keywords 
        : (userId ? [] : ['software', 'developer', 'engineer', 'technology']); // Empty keywords if userId available (backend will use stored matches)
      
      const response = await cvAPI.searchJobs(
        searchKeywords,
        jobTitles && jobTitles.length > 0 ? jobTitles : null,
        searchLocation || null,
        limit,
        userId  // CRITICAL: Must pass userId to get stored matches from Quick Upload
      );

      // Axios returns response.data directly for successful requests
      // Check if response is an axios response object or direct data
      const data = response.data || response;
      const jobsList = data.jobs || (Array.isArray(data) ? data : []);
      
      // Remove duplicates based on title, company, AND source
      const seen = new Set();
      const uniqueJobs = [];
      for (const job of jobsList) {
        if (!job || typeof job !== 'object') continue;
        
        const key = `${job.title || job.job_title || ''}-${job.company || job.company_name || ''}-${job.source || 'Unknown'}`;
        if (key && key !== '--Unknown' && !seen.has(key)) {
          seen.add(key);
          uniqueJobs.push(job);
        }
      }
      
      setLocalJobs(uniqueJobs);
      // Also store in context for future navigation
      setJobs(uniqueJobs);
      
      if (uniqueJobs.length === 0) {
        toast('No jobs found. Try different keywords or location.', { icon: 'ℹ️' });
      } else {
        toast.success(`Found ${uniqueJobs.length} unique jobs!`);
      }
    } catch (err) {
      console.error('Error fetching jobs:', err);
      
      // Better error message extraction
      let errorMessage = 'Failed to fetch jobs. Please try again.';
      
      if (err.response) {
        // Axios error with response
        errorMessage = err.response.data?.detail || err.response.data?.message || err.response.statusText || errorMessage;
      } else if (err.message) {
        // General error message
        errorMessage = err.message;
      }
      
      // Log full error for debugging
      console.error('Full error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        config: err.config
      });
      
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = (applyUrl) => {
    if (applyUrl) {
      window.open(applyUrl, '_blank', 'noopener,noreferrer');
    } else {
      toast.error('Apply URL not available for this job');
    }
  };

  // CRITICAL FIX: Only show loading if no jobs in context AND fetching
  // If jobs exist in context, show them instantly (no loading state)
  if (loading && matchedJobs.length === 0 && jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader className="w-10 h-10 animate-spin text-blue-600 mb-4" />
        <p className="text-gray-600">Searching for jobs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchJobs}
          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="job-list-container">
      {/* Search Location Filter */}
      <div className="mb-6 flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location (optional)
          </label>
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              placeholder="e.g., Remote, New York, London"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 bg-white/70 backdrop-blur-sm"
            />
          </div>
        </div>
        <button
          onClick={fetchJobs}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Search className="w-5 h-5" />
          Search
        </button>
      </div>

      {/* Jobs Count */}
      {displayJobs.length > 0 && (
        <div className="mb-4 text-gray-600">
          <p className="text-sm">
            Found <span className="font-semibold text-blue-600">{displayJobs.length}</span> jobs matching your CV
          </p>
        </div>
      )}

      {/* Jobs Grid */}
      {displayJobs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayJobs.map((job, index) => {
            // Create unique key based on title, company, and index
            const jobKey = `${job.title || job.job_title || ''}-${job.company || job.company_name || ''}-${index}`;
            const applyUrl = job.applyUrl || job.url || job.link || job.apply_url;
            
            return (
              <motion.div
                key={jobKey}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white/70 backdrop-blur-sm rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-200 border border-gray-200"
              >
                {/* Job Title */}
                <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                  {job.title || job.job_title || 'Job Title'}
                </h3>

                {/* Company */}
                <div className="flex items-center gap-2 mb-3">
                  <Building2 className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-700 font-medium">{job.company || job.company_name || 'Unknown Company'}</span>
                </div>

                {/* Location */}
                <div className="flex items-center gap-2 mb-3">
                  <MapPin className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-600 text-sm">{job.location || 'Location not specified'}</span>
                </div>

                {/* ATS Score Display */}
                {job.ats_score !== undefined && (
                  <div className="mb-3 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-gray-700">CV Match Score</span>
                      <span className={`text-lg font-bold ${
                        job.ats_score >= 80 ? 'text-green-600' :
                        job.ats_score >= 60 ? 'text-blue-600' :
                        job.ats_score >= 40 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {job.ats_score}/100
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        job.ats_grade === 'A+' || job.ats_grade === 'A' ? 'bg-green-100 text-green-800' :
                        job.ats_grade === 'B' ? 'bg-blue-100 text-blue-800' :
                        job.ats_grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        Grade: {job.ats_grade || 'N/A'}
                      </span>
                      {job.ats_relevance !== null && job.ats_relevance !== undefined && (
                        <span className="text-xs text-gray-600">
                          Relevance: {(job.ats_relevance * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    {job.ats_keyword_overlap_percentage !== undefined && (
                      <div className="mt-2 text-xs text-gray-600">
                        <span className="font-medium">Keywords matched: </span>
                        {job.ats_keyword_overlap || 0} / {job.ats_matched_keywords?.length || 0} ({job.ats_keyword_overlap_percentage.toFixed(0)}%)
                      </div>
                    )}
                    {/* Skill Gaps with Learning Resources */}
                    {job.skill_gaps && job.skill_gaps.length > 0 && (
                      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <div className="flex items-start gap-2 mb-2">
                          <span className="text-xs font-semibold text-amber-800">
                            ⚠️ Skill Gap Detected
                          </span>
                        </div>
                        <p className="text-xs text-amber-700 mb-2">
                          You lack some required skills, but we've linked free resources to help you learn them.
                        </p>
                        <div className="space-y-2">
                          {job.skill_gaps.slice(0, 2).map((gap, gapIdx) => (
                            <div key={gapIdx} className="bg-white rounded p-2 border border-amber-100">
                              <div className="text-xs font-semibold text-gray-800 mb-1">
                                Missing: {gap.skill}
                              </div>
                              {gap.resources && gap.resources.length > 0 && (
                                <div className="space-y-1">
                                  {gap.resources.slice(0, 2).map((resource, resIdx) => (
                                    <a
                                      key={resIdx}
                                      href={resource.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="block text-xs text-blue-600 hover:text-blue-800 hover:underline"
                                    >
                                      📚 {resource.platform}: {resource.title}
                                    </a>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {/* Fallback: Show missing skills if skill_gaps not available */}
                    {(!job.skill_gaps || job.skill_gaps.length === 0) && job.ats_missing_skills && job.ats_missing_skills.length > 0 && (
                      <div className="mt-2 text-xs">
                        <span className="font-medium text-gray-700">Missing skills: </span>
                        <span className="text-red-600">{job.ats_missing_skills.slice(0, 3).join(', ')}</span>
                        {job.ats_missing_skills.length > 3 && (
                          <span className="text-gray-500"> +{job.ats_missing_skills.length - 3} more</span>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Source Badge & Type */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {job.source && (
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                      job.source === 'RemoteOK' 
                        ? 'bg-green-100 text-green-700' 
                        : job.source === 'Freelancer.com'
                        ? 'bg-purple-100 text-purple-700'
                        : job.source === 'Arbeitnow'
                        ? 'bg-orange-100 text-orange-700'
                        : job.source === 'Adzuna'
                        ? 'bg-cyan-100 text-cyan-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {job.source}
                    </span>
                  )}
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

                {/* Description */}
                <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                  {job.description || job.summary || 'No description available'}
                </p>

                {/* Apply Button */}
                {applyUrl ? (
                  <a
                    href={applyUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-center px-4 py-2 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-semibold flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Apply Now
                  </a>
                ) : (
                  <button
                    disabled
                    className="w-full bg-gray-400 text-white px-4 py-2 rounded-lg cursor-not-allowed font-semibold flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Apply URL Not Available
                  </button>
                )}
              </motion.div>
            );
          })}
        </div>
      ) : (
        !loading && (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <Briefcase className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 text-lg mb-2">No jobs found</p>
            <p className="text-gray-500 text-sm">
              Try adjusting your keywords or location, or check back later for new opportunities.
            </p>
          </div>
        )
      )}
    </div>
  );
}

