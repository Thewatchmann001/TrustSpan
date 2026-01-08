/**
 * Enhanced Startup List Component
 * Features: Search, Filter by 7+ industries, Sort options, Glassmorphism design
 */
import { useState, useEffect, useMemo } from "react";
import { Search, Filter, TrendingUp, Shield, ArrowUpDown, DollarSign, Calendar } from "lucide-react";
import StartupCard from "../components/StartupCard";
import toast from "react-hot-toast";
import { motion } from "framer-motion";

const INDUSTRIES = [
  { value: "all", label: "All Industries" },
  { value: "Technology", label: "Technology" },
  { value: "Healthcare", label: "Healthcare" },
  { value: "Agriculture", label: "Agriculture" },
  { value: "Education", label: "Education" },
  { value: "Finance", label: "Finance" },
  { value: "Tourism", label: "Tourism" },
  { value: "Construction", label: "Construction" },
  { value: "other", label: "Other" },
];

const SORT_OPTIONS = [
  { value: "newest", label: "Newest First", icon: Calendar },
  { value: "most_funded", label: "Most Funded", icon: TrendingUp },
  { value: "largest_goal", label: "Largest Goal", icon: DollarSign },
  { value: "highest_credibility", label: "Highest Credibility", icon: Shield },
];

export default function StartupListEnhanced({ onStartupSelect }) {
  const [startups, setStartups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSector, setFilterSector] = useState("all");
  const [sortBy, setSortBy] = useState("newest");
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
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced search - searches name, description, and sector
  const filteredAndSortedStartups = useMemo(() => {
    let filtered = startups.filter((startup) => {
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch =
        startup.name?.toLowerCase().includes(searchLower) ||
        startup.description?.toLowerCase().includes(searchLower) ||
        startup.sector?.toLowerCase().includes(searchLower) ||
        startup.mission?.toLowerCase().includes(searchLower) ||
        startup.products_services?.toLowerCase().includes(searchLower);
      
      const matchesCredibility = (startup.credibility_score || 0) >= minCredibility;
      
      return matchesSearch && matchesCredibility;
    });

    // Sort startups
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "newest":
          return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        case "most_funded":
          const aFunded = a.total_investments || 0;
          const bFunded = b.total_investments || 0;
          return bFunded - aFunded;
        case "largest_goal":
          const aGoal = a.funding_goal || 0;
          const bGoal = b.funding_goal || 0;
          return bGoal - aGoal;
        case "highest_credibility":
          const aCred = a.credibility_score || 0;
          const bCred = b.credibility_score || 0;
          return bCred - aCred;
        default:
          return 0;
      }
    });

    return filtered;
  }, [startups, searchTerm, minCredibility, sortBy]);

  return (
    <div className="startup-list-enhanced">
      {/* Header with Glassmorphism */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 mb-6 shadow-xl"
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-3xl font-bold text-white">Verified Startups</h2>
          <div className="flex items-center gap-2 text-white/80">
            <Shield className="w-5 h-5 text-green-400" />
            <span className="text-sm">Blockchain Verified</span>
          </div>
        </div>

        {/* Enhanced Search Bar */}
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/60 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by name, description, or industry..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>
        </div>

        {/* Filters and Sort */}
        <div className="flex flex-wrap gap-4">
          {/* Industry Filter */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-white/80 mb-2">Industry</label>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60 w-4 h-4" />
              <select
                value={filterSector}
                onChange={(e) => setFilterSector(e.target.value)}
                className="w-full pl-10 pr-4 py-2 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                {INDUSTRIES.map((industry) => (
                  <option key={industry.value} value={industry.value} className="bg-gray-900">
                    {industry.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Sort Options */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-white/80 mb-2">Sort By</label>
            <div className="relative">
              <ArrowUpDown className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60 w-4 h-4" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full pl-10 pr-4 py-2 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value} className="bg-gray-900">
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Credibility Filter */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-white/80 mb-2">
              Min Credibility: {minCredibility}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={minCredibility}
              onChange={(e) => setMinCredibility(Number(e.target.value))}
              className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>

        {/* Results Count */}
        <div className="mt-4 text-sm text-white/60">
          Showing {filteredAndSortedStartups.length} of {startups.length} startups
        </div>
      </motion.div>

      {/* Startup Grid with Glassmorphism Cards */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl p-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="text-white/80 mt-4">Loading startups...</p>
          </div>
        </div>
      ) : filteredAndSortedStartups.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAndSortedStartups.map((startup, index) => (
            <motion.div
              key={startup.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => onStartupSelect && onStartupSelect(startup)}
              className="cursor-pointer"
            >
              <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 hover:bg-white/20 transition-all duration-300 hover:scale-105 hover:shadow-2xl">
                <StartupCard startup={startup} />
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-12 text-center">
          <p className="text-white/60 text-lg">No startups found matching your criteria</p>
          <button
            onClick={() => {
              setSearchTerm("");
              setFilterSector("all");
              setMinCredibility(0);
            }}
            className="mt-4 text-blue-400 hover:text-blue-300 underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}

