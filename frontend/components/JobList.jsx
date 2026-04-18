/**
 * JobList Component
 * Displays job listings from multiple sources with Apply buttons
 * 
 * DATA FLOW FIX: Uses global JobsContext to get pre-matched jobs instantly
 * WHY: Prevents re-fetching when navigating from Quick Upload → CV Editor
 * Only fetches if no jobs in context (fallback for direct navigation)
 */
import { useState, useEffect } from 'react';
import { Briefcase, MapPin, Building2, ExternalLink, Loader, Search, Sparkles, AlertCircle, ChevronDown, ChevronUp, CheckCircle2, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cvAPI } from '../utils/api';
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
  const [expandedJobId, setExpandedJobId] = useState(null);
  
  // Use context jobs if available, otherwise use local
  const displayJobs = matchedJobs.length > 0 ? matchedJobs : jobs;
  
  // Helper function to normalize match score (handles both decimal 0-1 and percentage 0-100)
  const formatMatchScore = (score) => {
    if (score === undefined || score === null) return null;
    // If score is less than 1, it's a decimal (0-1), convert to percentage
    if (score < 1) {
      return parseFloat((score * 100).toFixed(1));
    }
    // Otherwise it's already a percentage
    return parseFloat(score.toFixed(1));
  };

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

  const fetchJobs = async (useV2 = true) => {
    setLoading(true);
    setError(null);
    
    try {
      let jobsList = [];
      let metadata = {};
      
      // Try new v2 endpoint first if userId is available
      if (useV2 && userId) {
        try {
          const response = await cvAPI.matchJobsV2(
            userId,
            null, // cv_id (will be fetched from user_id)
            keywords && keywords.length > 0 ? keywords : null,
            searchLocation || null,
            limit
          );
          
          const data = response.data || response;
          if (data.success) {
            jobsList = data.jobs || [];
            metadata = data.metadata || {};
            console.log('[JobList] Using new v2 matching system:', {
              jobs: jobsList.length,
              providers: metadata.provider_metrics,
              duration: metadata.duration_seconds
            });
          } else {
            throw new Error(data.error || 'V2 matching failed');
          }
        } catch (v2Error) {
          console.warn('[JobList] V2 endpoint failed, falling back to v1:', v2Error);
          // Fallback to v1
          useV2 = false;
        }
      }
      
      // Fallback to v1 endpoint
      if (!useV2 || jobsList.length === 0) {
        const searchKeywords = (keywords && keywords.length > 0) 
          ? keywords 
          : (userId ? [] : ['software', 'developer', 'engineer', 'technology']);
        
        const response = await cvAPI.searchJobs(
          searchKeywords,
          jobTitles && jobTitles.length > 0 ? jobTitles : null,
          searchLocation || null,
          limit,
          userId
        );

        const data = response.data || response;
        jobsList = data.jobs || (Array.isArray(data) ? data : []);
      }
      
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
        const matchInfo = metadata.matched_jobs ? ` (${metadata.matched_jobs} matched)` : '';
        toast.success(`Found ${uniqueJobs.length} unique jobs${matchInfo}!`);
      }
    } catch (err) {
      console.error('Error fetching jobs:', err);
      
      let errorMessage = 'Failed to fetch jobs. Please try again.';
      
      if (err.response) {
        errorMessage = err.response.data?.detail || err.response.data?.message || err.response.statusText || errorMessage;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
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
            
            const matchScore = formatMatchScore(job.match_score);
            const isExpanded = expandedJobId === jobKey;

            return (
              <motion.div
                key={jobKey}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`bg-white/70 backdrop-blur-sm rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-200 border relative overflow-hidden ${
                  job.is_fallback ? 'border-amber-200' : 'border-gray-200'
                }`}
              >
                {/* Fallback Indicator */}
                {job.is_fallback && (
                  <div className="absolute top-0 left-0 right-0 bg-amber-100 text-amber-800 text-[10px] uppercase tracking-wider font-bold py-1 px-3 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    Relevant Match (Based on Industry)
                  </div>
                )}

                {/* Match Score Badge */}
                {matchScore !== null && (
                  <div className="absolute top-4 right-4 flex flex-col items-end">
                    <div className={`text-lg font-bold ${
                      matchScore >= 70 ? 'text-green-600' :
                      matchScore >= 40 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {matchScore}%
                    </div>
                    <div className="text-[10px] text-gray-400 font-medium uppercase">Match</div>
                  </div>
                )}

                {/* Job Title */}
                <h3 className={`text-xl font-bold text-gray-900 mb-2 line-clamp-2 ${job.is_fallback ? 'mt-4' : ''}`}>
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

                {/* Match Reasons */}
                {job.match_reasons && job.match_reasons.length > 0 && (
                  <div className="mb-4">
                    <div className="flex flex-wrap gap-2">
                      {job.match_reasons.map((reason, idx) => (
                        <div key={idx} className="flex items-center gap-1 text-xs text-blue-700 bg-blue-50 px-2 py-1 rounded-md border border-blue-100">
                          <Sparkles className="w-3 h-3" />
                          {reason}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Missing Skills and Learning Resources (ATS Score removed per user request) */}
                {(job.ats_missing_skills && job.ats_missing_skills.length > 0) && (
                  <div className="mb-3 p-3 bg-gradient-to-r from-amber-50 to-yellow-50 rounded-lg border border-amber-200">
                    {/* Missing Skills Display */}
                    <div className="mb-3">
                      <p className="text-xs font-semibold text-amber-700 mb-2 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        Missing Skills:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {job.ats_missing_skills.map((skill, idx) => (
                          <span 
                            key={idx} 
                            className="px-2 py-1 bg-amber-100 text-amber-800 rounded-md text-xs font-medium border border-amber-200"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                      <p className="text-xs text-amber-600 mt-2">
                        Consider learning these skills to improve your match
                      </p>
                    </div>
                    
                    {/* Learning Resources - Use backend-provided resources */}
                    {(job.skill_gaps && job.skill_gaps.length > 0) && (
                      <div className="pt-3 border-t border-green-200">
                        <p className="text-xs font-semibold text-green-700 mb-2 flex items-center gap-1">
                          <span className="text-green-600">📚</span>
                          Free Learning Resources:
                        </p>
                        <div className="space-y-2">
                          {job.skill_gaps.slice(0, 3).map((gap, idx) => (
                            <div key={idx} className="p-2 bg-green-50 border border-green-200 rounded">
                              <p className="text-xs font-semibold text-green-800 mb-2">
                                Learn {gap.skill}
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {gap.resources && gap.resources.length > 0 ? (
                                  gap.resources.map((resource, resIdx) => (
                                    <a
                                      key={resIdx}
                                      href={resource.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-green-600 hover:text-green-800 underline px-2 py-1 bg-white rounded border border-green-200"
                                    >
                                      {resource.platform}
                                    </a>
                                  ))
                                ) : (
                                  // Fallback to hardcoded URLs if backend didn't provide resources
                                  <>
                                    <a
                                      href={`https://www.youtube.com/results?search_query=learn+${encodeURIComponent(gap.skill)}+tutorial+free`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-green-600 hover:text-green-800 underline px-2 py-1 bg-white rounded border border-green-200"
                                    >
                                      YouTube
                                    </a>
                                    <a
                                      href={`https://www.coursera.org/search?query=${encodeURIComponent(gap.skill)}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-green-600 hover:text-green-800 underline px-2 py-1 bg-white rounded border border-green-200"
                                    >
                                      Coursera
                                    </a>
                                    <a
                                      href={`https://alison.com/courses?query=${encodeURIComponent(gap.skill)}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-green-600 hover:text-green-800 underline px-2 py-1 bg-white rounded border border-green-200"
                                    >
                                      Alison
                                    </a>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                        <p className="text-xs text-green-600 mt-2 italic">
                          Click to access free courses and tutorials
                        </p>
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

                {/* Detailed Feedback Expandable */}
                {job.detailed_feedback && (
                  <div className="mb-4">
                    <button
                      onClick={() => setExpandedJobId(isExpanded ? null : jobKey)}
                      className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 transition-colors"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="w-4 h-4" />
                          Hide Match Details
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4" />
                          View Match Details
                        </>
                      )}
                    </button>

                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
                            {job.detailed_feedback.summary && (
                              <div>
                                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">Analysis</h4>
                                <p className="text-sm text-gray-600 italic">"{job.detailed_feedback.summary}"</p>
                              </div>
                            )}

                            {job.detailed_feedback.strengths && job.detailed_feedback.strengths.length > 0 && (
                              <div>
                                <h4 className="text-xs font-bold text-green-700 uppercase tracking-wider mb-1 flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3" />
                                  Strengths
                                </h4>
                                <ul className="list-disc list-inside text-xs text-gray-600 space-y-0.5 ml-1">
                                  {job.detailed_feedback.strengths.map((strength, idx) => (
                                    <li key={idx}>{strength}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {job.detailed_feedback.improvement_areas && job.detailed_feedback.improvement_areas.length > 0 && (
                              <div>
                                <h4 className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-1 flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  How to Improve
                                </h4>
                                <div className="space-y-2">
                                  {job.detailed_feedback.improvement_areas.map((area, idx) => (
                                    <div key={idx} className="bg-white p-2 rounded border border-amber-100">
                                      <p className="text-xs font-semibold text-gray-800">{area.area}</p>
                                      <p className="text-[11px] text-gray-600 mb-1">{area.issue}</p>
                                      <p className="text-[11px] text-blue-600 font-medium">💡 {area.suggestion}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

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

