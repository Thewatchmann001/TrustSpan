/**
 * Job Matches Component
 * Displays matched job opportunities from local and global sources
 */
import { useState, useEffect } from "react";
import { Briefcase, MapPin, TrendingUp, ExternalLink } from "lucide-react";
import toast from "react-hot-toast";

export default function JobMatches({ userId }) {
  const [matches, setMatches] = useState([]);
  const [globalJobs, setGlobalJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (userId) {
      fetchJobMatches();
      fetchGlobalJobs();
    }
  }, [userId]);

  const fetchJobMatches = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
      const response = await fetch(`${apiUrl}/api/jobs/match?user_id=${userId}&limit=10`);
      const data = await response.json();
      setMatches(data.matches || []);
    } catch (error) {
      toast.error("Failed to fetch job matches");
    } finally {
      setLoading(false);
    }
  };

  const fetchGlobalJobs = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
      const response = await fetch(`${apiUrl}/api/jobs/search-global?query=software engineer&limit=10`);
      const data = await response.json();
      setGlobalJobs(data.jobs || []);
    } catch (error) {
      console.error("Failed to fetch global jobs");
    }
  };

  return (
    <div className="job-matches">
      <h2 className="text-2xl font-bold mb-4">Job Matches</h2>
      
      {/* Local Job Matches */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Local Opportunities</h3>
        {loading ? (
          <p>Loading matches...</p>
        ) : matches.length > 0 ? (
          <div className="grid gap-4">
            {matches.map((job) => (
              <div key={job.job_id} className="border rounded-lg p-4 hover:shadow-md transition">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-lg">{job.job_title}</h4>
                    <p className="text-gray-600">{job.startup_name}</p>
                    <div className="flex items-center mt-2 text-sm text-gray-500">
                      <MapPin className="w-4 h-4 mr-1" />
                      {job.location}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center text-green-600">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      {Math.round(job.match_score * 100)}% match
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No matches found</p>
        )}
      </div>

      {/* Global Job Matches */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Global Opportunities</h3>
        {globalJobs.length > 0 ? (
          <div className="grid gap-4">
            {globalJobs.map((job) => (
              <div key={job.id} className="border rounded-lg p-4 hover:shadow-md transition">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-lg">{job.title}</h4>
                    <p className="text-gray-600">{job.company}</p>
                    <div className="flex items-center mt-2 text-sm text-gray-500">
                      <MapPin className="w-4 h-4 mr-1" />
                      {job.location}
                    </div>
                  </div>
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No global jobs found</p>
        )}
      </div>
    </div>
  );
}

