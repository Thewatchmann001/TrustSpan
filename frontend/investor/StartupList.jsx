/**
 * Startup List Component
 * Displays list of verified startups available for investment
 */
import { useState, useEffect } from "react";
import { Search, Filter, TrendingUp, Shield } from "lucide-react";
import StartupCard from "../components/StartupCard";
import toast from "react-hot-toast";

export default function StartupList({ onStartupSelect }) {
  const [startups, setStartups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSector, setFilterSector] = useState("all");
  const [minCredibility, setMinCredibility] = useState(0);

  useEffect(() => {
    fetchStartups();
  }, [filterSector, minCredibility]);

  const fetchStartups = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        skip: "0",
        limit: "100",
        min_credibility: minCredibility.toString(),
      });
      if (filterSector !== "all") {
        params.append("sector", filterSector);
      }
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/startups/list?${params}`);
      const data = await response.json();
      setStartups(data.startups || []);
    } catch (error) {
      toast.error("Failed to fetch startups");
    } finally {
      setLoading(false);
    }
  };

  const filteredStartups = startups.filter((startup) =>
    startup.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    startup.sector.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="startup-list">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Verified Startups</h2>
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-green-600" />
          <span className="text-sm text-gray-600">Blockchain Verified</span>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search startups..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
          />
        </div>
        <select
          value={filterSector}
          onChange={(e) => setFilterSector(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">All Sectors</option>
          <option value="Technology">Technology</option>
          <option value="Healthcare">Healthcare</option>
          <option value="Agriculture">Agriculture</option>
          <option value="Education">Education</option>
          <option value="Finance">Finance</option>
        </select>
        <input
          type="range"
          min="0"
          max="100"
          value={minCredibility}
          onChange={(e) => setMinCredibility(Number(e.target.value))}
          className="w-32"
        />
        <span className="text-sm text-gray-600">Min: {minCredibility}%</span>
      </div>

      {/* Startup Grid */}
      {loading ? (
        <p>Loading startups...</p>
      ) : filteredStartups.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredStartups.map((startup) => (
            <div
              key={startup.id}
              onClick={() => onStartupSelect && onStartupSelect(startup)}
              className="cursor-pointer"
            >
              <StartupCard startup={startup} />
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500">No startups found</p>
      )}
    </div>
  );
}

