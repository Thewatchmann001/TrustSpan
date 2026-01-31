/**
 * Jobs Context - Global State Management for Job Matches
 * 
 * PURPOSE: Persist matched jobs across navigation to prevent re-fetching
 * when user moves from Quick Upload → CV Editor → Job List
 * 
 * WHY: Previously, jobs were re-fetched on every navigation, causing:
 * - Delays and loading states
 * - Potential inconsistency (different jobs on different pages)
 * - Unnecessary API calls
 * 
 * SOLUTION: Store jobs in global context once fetched, reuse across components
 */
import { createContext, useContext, useState, useCallback } from 'react';

const JobsContext = createContext(null);

export function JobsProvider({ children }) {
  // Store matched jobs - persisted across navigation
  const [matchedJobs, setMatchedJobs] = useState([]);
  
  // Store loading state for learning resources per job
  // Format: { jobId: { skill: loadingState } }
  const [resourceLoadingStates, setResourceLoadingStates] = useState({});
  
  // Store loaded learning resources per job
  // Format: { jobId: { skill: resources[] } }
  const [loadedResources, setLoadedResources] = useState({});

  /**
   * Set matched jobs (called after CV upload/Quick Upload)
   * This replaces any existing jobs - used when new CV is uploaded
   */
  const setJobs = useCallback((jobs) => {
    console.log('[JobsContext] Setting jobs:', jobs?.length || 0);
    setMatchedJobs(Array.isArray(jobs) ? jobs : []);
    // Clear resource cache when new jobs are set
    setLoadedResources({});
    setResourceLoadingStates({});
  }, []);

  /**
   * Add or update a single job (for incremental updates)
   */
  const updateJob = useCallback((job) => {
    setMatchedJobs(prev => {
      const existing = prev.findIndex(j => 
        j.id === job.id || 
        (j.title === job.title && j.company === job.company && j.source === job.source)
      );
      
      if (existing >= 0) {
        // Update existing job
        const updated = [...prev];
        updated[existing] = { ...updated[existing], ...job };
        return updated;
      } else {
        // Add new job
        return [...prev, job];
      }
    });
  }, []);

  /**
   * Mark learning resources as loading for a specific job and skill
   */
  const setResourceLoading = useCallback((jobId, skill, loading) => {
    setResourceLoadingStates(prev => ({
      ...prev,
      [jobId]: {
        ...(prev[jobId] || {}),
        [skill]: loading
      }
    }));
  }, []);

  /**
   * Store loaded learning resources for a job and skill
   */
  const setJobResources = useCallback((jobId, skill, resources) => {
    setLoadedResources(prev => ({
      ...prev,
      [jobId]: {
        ...(prev[jobId] || {}),
        [skill]: resources
      }
    }));
  }, []);

  /**
   * Get learning resources for a job and skill (from cache)
   */
  const getJobResources = useCallback((jobId, skill) => {
    return loadedResources[jobId]?.[skill] || null;
  }, [loadedResources]);

  /**
   * Check if resources are loading for a job and skill
   */
  const isResourceLoading = useCallback((jobId, skill) => {
    return resourceLoadingStates[jobId]?.[skill] || false;
  }, [resourceLoadingStates]);

  /**
   * Clear all jobs (for logout or reset)
   */
  const clearJobs = useCallback(() => {
    setMatchedJobs([]);
    setLoadedResources({});
    setResourceLoadingStates({});
  }, []);

  const value = {
    matchedJobs,
    setJobs,
    updateJob,
    setResourceLoading,
    setJobResources,
    getJobResources,
    isResourceLoading,
    clearJobs
  };

  return (
    <JobsContext.Provider value={value}>
      {children}
    </JobsContext.Provider>
  );
}

export function useJobs() {
  const context = useContext(JobsContext);
  if (!context) {
    throw new Error('useJobs must be used within JobsProvider');
  }
  return context;
}
