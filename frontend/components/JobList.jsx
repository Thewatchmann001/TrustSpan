/**
 * JobList Component
 * Displays job listings from multiple sources with Apply buttons
 */
import { useState, useEffect } from 'react';
import { Briefcase, MapPin, Building2, ExternalLink, Loader, Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { cvAPI } from '../lib/api';
import toast from 'react-hot-toast';

export default function JobList({ keywords = [], jobTitles = [], location = null, limit = 50 }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchLocation, setSearchLocation] = useState(location || '');

  useEffect(() => {
    if (keywords && keywords.length > 0) {
      fetchJobs();
    }
  }, [keywords, jobTitles, location]);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await cvAPI.searchJobs(
        keywords,
        jobTitles.length > 0 ? jobTitles : null,
        searchLocation || null,
        limit
      );

      if (response.status === 200) {
        const data = response.data;
        const jobsList = data.jobs || data || [];
        setJobs(Array.isArray(jobsList) ? jobsList : []);
        if (jobsList.length === 0) {
          toast.info('No jobs found. Try different keywords or location.');
        } else {
          toast.success(`Found ${jobsList.length} jobs!`);
        }
      } else {
        throw new Error('Failed to fetch jobs');
      }
    } catch (err) {
      console.error('Error fetching jobs:', err);
      setError(err.response?.data?.detail || 'Failed to fetch jobs. Please try again.');
      toast.error('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = (applyUrl) => {
    if (applyUrl) {
      window.open(applyUrl, '_blank', 'noopener,noreferrer');
    } else {
      toast.error('Apply URL not available');
    }
  };

  if (loading) {
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
      {jobs.length > 0 && (
        <div className="mb-4 text-gray-600">
          <p className="text-sm">
            Found <span className="font-semibold text-blue-600">{jobs.length}</span> jobs matching your CV
          </p>
        </div>
      )}

      {/* Jobs Grid */}
      {jobs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job, index) => (
            <motion.div
              key={`${job.title}-${job.company}-${index}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white/70 backdrop-blur-sm rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-200 border border-gray-200"
            >
              {/* Job Title */}
              <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                {job.title || 'Job Title'}
              </h3>

              {/* Company */}
              <div className="flex items-center gap-2 mb-3">
                <Building2 className="w-4 h-4 text-gray-500" />
                <span className="text-gray-700 font-medium">{job.company || 'Unknown Company'}</span>
              </div>

              {/* Location */}
              <div className="flex items-center gap-2 mb-3">
                <MapPin className="w-4 h-4 text-gray-500" />
                <span className="text-gray-600 text-sm">{job.location || 'Location not specified'}</span>
              </div>

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
                {job.description || 'No description available'}
              </p>

              {/* Apply Button */}
              <button
                onClick={() => handleApply(job.applyUrl)}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-semibold flex items-center justify-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                Apply Now
              </button>
            </motion.div>
          ))}
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

