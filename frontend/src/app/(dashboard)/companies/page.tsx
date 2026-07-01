"use client";

import React, { useEffect, useState } from "react";
import { 
  Building2, 
  Globe, 
  MapPin, 
  Users, 
  Star, 
  TrendingUp, 
  Cpu, 
  Database, 
  Activity,
  ArrowUpRight,
  Search,
  X,
  Layers
} from "lucide-react";

interface Company {
  id: string;
  name: string;
  website: string | null;
  industry: string | null;
  size_range: string | null;
  headquarters: string | null;
  glassdoor_rating: number | null;
  ai_hiring_score: number | null;
  tech_stack?: string | null;
  ats_provider?: string | null;
  hiring_trends_summary?: string | null;
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/companies");
      if (res.ok) {
        const data = await res.json();
        setCompanies(data);
      }
    } catch (e) {
      console.error("Error fetching companies:", e);
      // Fallback fallback data for UI preview
      setCompanies([
        {
          id: "1",
          name: "NeuralFlow Solutions",
          website: "https://neuralflow.ai",
          industry: "Artificial Intelligence",
          size_range: "51-200 employees",
          headquarters: "San Francisco, CA",
          glassdoor_rating: 4.6,
          ai_hiring_score: 92
        },
        {
          id: "2",
          name: "CloudScale Systems",
          website: "https://cloudscale.io",
          industry: "Cloud Infrastructure",
          size_range: "501-1000 employees",
          headquarters: "Austin, TX",
          glassdoor_rating: 4.1,
          ai_hiring_score: 84
        },
        {
          id: "3",
          name: "FinIntel Corp",
          website: "https://finintel.com",
          industry: "Financial Services",
          size_range: "1000+ employees",
          headquarters: "New York, NY",
          glassdoor_rating: 3.9,
          ai_hiring_score: 76
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();

    const interval = setInterval(() => {
      const fetchCompaniesSilent = async () => {
        try {
          const res = await fetch("http://localhost:8000/api/companies");
          if (res.ok) {
            const data = await res.json();
            setCompanies(data);
          }
        } catch (e) {
          console.error("Silent companies polling error:", e);
        }
      };
      fetchCompaniesSilent();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleSelectCompany = async (company: Company) => {
    setActiveCompany(company);
    setDetailsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/companies/${company.id}`);
      if (res.ok) {
        const data = await res.json();
        setActiveCompany(data);
      }
    } catch (e) {
      console.error("Error fetching company details:", e);
      // Inject mock detail fields if API fails
      setActiveCompany({
        ...company,
        tech_stack: company.id === "1" 
          ? "PyTorch, FastAPI, Qdrant, React, Kubernetes, AWS" 
          : "Docker, Kubernetes, Redis, Celery, Terraform, Python",
        ats_provider: company.id === "1" ? "Greenhouse" : "Workday",
        hiring_trends_summary: company.id === "1"
          ? "Highly active recruiting for generative AI roles. Compensation is in the top 10% percentile."
          : "Steady hiring for cloud architecture and infrastructure pipelines."
      });
    } finally {
      setDetailsLoading(false);
    }
  };

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    (c.industry && c.industry.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-8 animate-fadeIn relative">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Company Intelligence Hub</h1>
        <p className="text-slate-400 text-sm mt-1">
          Explore enriched profiles, technology stacks, ATS systems, and AI Hiring trends for prospective employers.
        </p>
      </div>

      {/* Filter panel */}
      <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
            <Search className="h-4 w-4" />
          </span>
          <input
            type="text"
            placeholder="Search companies by name or industry sector..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
        </div>
      </div>

      {/* Main Grid content */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredCompanies.length === 0 ? (
        <div className="text-center py-16 glass-panel rounded-2xl border border-white/5">
          <p className="text-slate-400 font-medium">No company records matching your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCompanies.map((c) => (
            <div 
              key={c.id} 
              className="glass-panel glass-panel-hover p-6 rounded-2xl border border-white/5 flex flex-col justify-between cursor-pointer"
              onClick={() => handleSelectCompany(c)}
            >
              <div>
                <div className="flex justify-between items-start gap-4 mb-4">
                  <div className="h-10 w-10 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-slate-300">
                    <Building2 className="h-5 w-5" />
                  </div>
                  {c.ai_hiring_score && (
                    <div className="bg-brand-500/10 border border-brand-500/20 text-brand-400 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                      <Cpu className="h-3 w-3 active-pulse" />
                      <span>Hiring Score: {c.ai_hiring_score}</span>
                    </div>
                  )}
                </div>

                <h3 className="text-lg font-bold text-white mb-1 group-hover:text-brand-400">{c.name}</h3>
                <p className="text-xs text-brand-400 font-semibold mb-4">{c.industry || "General Industry"}</p>

                <div className="space-y-2 text-xs text-slate-300">
                  {c.headquarters && (
                    <div className="flex items-center gap-2">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" />
                      <span>{c.headquarters}</span>
                    </div>
                  )}
                  {c.size_range && (
                    <div className="flex items-center gap-2">
                      <Users className="h-3.5 w-3.5 text-slate-400" />
                      <span>{c.size_range}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="border-t border-white/5 pt-4 mt-6 flex justify-between items-center text-xs">
                <span className="flex items-center gap-1 text-amber-400">
                  <Star className="h-3.5 w-3.5 fill-amber-400" />
                  <span className="font-semibold">{c.glassdoor_rating || "N/A"} Rating</span>
                </span>
                <span className="text-brand-400 font-semibold flex items-center gap-0.5">
                  Full Analytics <ArrowUpRight className="h-3.5 w-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Slide-out Drawer Details */}
      {activeCompany && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex justify-end z-50 animate-fadeIn">
          <div className="w-full max-w-xl bg-slate-900 border-l border-white/10 h-full flex flex-col justify-between overflow-y-auto animate-slideLeft">
            
            {/* Drawer Header */}
            <div className="p-6 border-b border-white/5 bg-slate-950 flex items-center justify-between sticky top-0 z-10">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-brand-400">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-extrabold text-white">{activeCompany.name}</h2>
                  <span className="text-xs text-slate-400">{activeCompany.industry}</span>
                </div>
              </div>
              <button 
                onClick={() => setActiveCompany(null)}
                className="h-10 w-10 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white rounded-xl flex items-center justify-center transition-all cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-6 space-y-8 flex-1">
              
              {/* AI Hiring Score Banner */}
              <div className="bg-brand-500/5 border border-brand-500/10 p-5 rounded-2xl flex items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-brand-400 uppercase tracking-wider flex items-center gap-1">
                    <Cpu className="h-3.5 w-3.5" /> Recruiter Intel Score
                  </span>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Based on job posting volume, tech stacks, and career roadmap alignments.
                  </p>
                </div>
                <div className="h-16 w-16 bg-slate-950 rounded-xl flex flex-col items-center justify-center border border-white/10">
                  <span className="text-xl font-extrabold text-white">{activeCompany.ai_hiring_score || 70}</span>
                  <span className="text-[9px] text-brand-400 font-bold uppercase">Score</span>
                </div>
              </div>

              {detailsLoading ? (
                <div className="flex justify-center items-center h-48">
                  <div className="h-6 w-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <>
                  {/* Technology Stacks */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-1.5">
                      <Database className="h-4 w-4 text-brand-400" /> Technology Stack
                    </h4>
                    <div className="bg-slate-950/40 border border-white/5 rounded-2xl p-4 flex flex-wrap gap-2">
                      {activeCompany.tech_stack ? (
                        activeCompany.tech_stack.split(",").map((tech, idx) => (
                          <span 
                            key={idx} 
                            className="bg-slate-900 border border-white/5 text-slate-300 px-3 py-1.5 rounded-lg text-xs font-semibold"
                          >
                            {tech.trim()}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-500 italic">No specific tech stack indexed.</span>
                      )}
                    </div>
                  </div>

                  {/* ATS Provider */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-1.5">
                      <Layers className="h-4 w-4 text-brand-400" /> Applicant Tracking System (ATS)
                    </h4>
                    <div className="bg-slate-950/40 border border-white/5 rounded-2xl p-4 text-sm text-slate-300">
                      <span className="font-semibold text-white bg-slate-900 border border-white/5 px-3 py-1.5 rounded-lg text-xs">
                        {activeCompany.ats_provider || "Unidentified ATS"}
                      </span>
                    </div>
                  </div>

                  {/* Hiring Trends */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-1.5">
                      <Activity className="h-4 w-4 text-brand-400" /> AI Hiring Trends
                    </h4>
                    <div className="bg-slate-950/40 border border-white/5 rounded-2xl p-5 text-sm text-slate-300 leading-relaxed">
                      {activeCompany.hiring_trends_summary || "No active recruiting trends indexed."}
                    </div>
                  </div>
                </>
              )}

            </div>

            {/* Drawer Footer */}
            <div className="p-6 border-t border-white/5 bg-slate-950/60 sticky bottom-0 z-10 flex">
              {activeCompany.website && (
                <a
                  href={activeCompany.website}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full bg-brand-600 hover:bg-brand-500 text-white rounded-xl py-3 px-4 font-semibold text-sm text-center flex items-center justify-center gap-2 border border-brand-500/20 cursor-pointer"
                >
                  <Globe className="h-4 w-4" />
                  <span>Visit Company Website</span>
                </a>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
