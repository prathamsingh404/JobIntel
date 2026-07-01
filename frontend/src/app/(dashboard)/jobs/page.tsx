"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { 
  Search, 
  Filter, 
  MapPin, 
  DollarSign, 
  Layers, 
  Calendar, 
  X, 
  Sparkles, 
  CheckCircle2, 
  Info,
  ChevronRight,
  TrendingUp,
  History,
  FileText,
  Briefcase
} from "lucide-react";

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  url: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  workplace_type: string | null;
  seniority: string | null;
  skills: string | null;
  relevance_score: number | null;
  relevance_explanation: string | null;
  rank: string | null;
  collected_at: string;
  versions?: Array<{
    version_number: number;
    updated_at: string;
    changes_payload: string;
  }>;
}

export default function JobExplorerPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [rank, setRank] = useState("");
  const [activeJob, setActiveJob] = useState<Job | null>(null);

  // Fetch jobs with filters
  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (role) params.append("role", role);
      if (rank) params.append("rank", rank);
      
      const res = await fetch(`http://localhost:8000/api/jobs?limit=50&${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (e) {
      console.error("Error fetching jobs:", e);
      // Fallback data for showcase
      setJobs([
        {
          id: "1",
          title: "Senior AI Engineer",
          company: "NeuralFlow Solutions",
          location: "San Francisco, CA (Hybrid)",
          description: "We are seeking a Senior AI Engineer to lead the optimization and deployment of our Large Language Model pipelines. You will design retrieval-augmented generation systems, build custom vector embedding graphs, and orchestrate server instances.",
          url: "https://example.com/job1",
          salary_min: 150000,
          salary_max: 190000,
          salary_currency: "USD",
          workplace_type: "hybrid",
          seniority: "senior",
          skills: "Python, PyTorch, LangChain, Qdrant, PostgreSQL, LLMs, Vector Embeddings",
          relevance_score: 0.94,
          relevance_explanation: "This role strongly aligns with candidate's proficiency in Large Language Models, PyTorch neural networks, and vector database structures.",
          rank: "senior",
          collected_at: "2026-07-01",
          versions: [
            { version_number: 1, updated_at: "2026-06-28 10:00", changes_payload: "Initial post." },
            { version_number: 2, updated_at: "2026-06-30 14:30", changes_payload: "Modified workplace mode to hybrid. Expanded salary range by $10k." }
          ]
        },
        {
          id: "2",
          title: "Lead DevOps Specialist",
          company: "CloudScale Systems",
          location: "Austin, TX (Remote)",
          description: "Responsible for managing multi-cluster Kubernetes installations, configuring secure ingress routes, running Redis task message brokers, and setting up Docker container builds.",
          url: "https://example.com/job2",
          salary_min: 160000,
          salary_max: 200000,
          salary_currency: "USD",
          workplace_type: "remote",
          seniority: "lead",
          skills: "Kubernetes, Docker, AWS, Redis, Celery, Terraform, CI/CD",
          relevance_score: 0.88,
          relevance_explanation: "Devops pipeline matches with candidate's infrastructure orchestration and automation capabilities.",
          rank: "lead",
          collected_at: "2026-07-01",
          versions: []
        },
        {
          id: "3",
          title: "Data Scientist - Analytics",
          company: "FinIntel Corp",
          location: "New York, NY",
          description: "Analyze market indicators, extract skill distributions, construct predictive datasets, and write clean SQL queries to aggregate multi-source recruiter indices.",
          url: "https://example.com/job3",
          salary_min: 120000,
          salary_max: 145000,
          salary_currency: "USD",
          workplace_type: "onsite",
          seniority: "mid",
          skills: "Python, SQL, Pandas, NumPy, Scikit-Learn, Tableau, Statistics",
          relevance_score: 0.72,
          relevance_explanation: "Directly matches requirements for data modeling and statistical exports, though lacks specific deep learning filters.",
          rank: "mid",
          collected_at: "2026-07-01",
          versions: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();

    const interval = setInterval(() => {
      const fetchJobsSilent = async () => {
        try {
          const params = new URLSearchParams();
          if (search) params.append("search", search);
          if (role) params.append("role", role);
          if (rank) params.append("rank", rank);
          
          const res = await fetch(`http://localhost:8000/api/jobs?limit=50&${params.toString()}`);
          if (res.ok) {
            const data = await res.json();
            setJobs(data);
          }
        } catch (e) {
          console.error("Silent jobs polling error:", e);
        }
      };
      fetchJobsSilent();
    }, 5000);

    return () => clearInterval(interval);
  }, [search, role, rank]);

  return (
    <div className="space-y-8 animate-fadeIn relative">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Job Intelligence Explorer</h1>
        <p className="text-slate-400 text-sm mt-1">
          Search, filter, and inspect structured job metadata, AI scoring breakdown, and historical tracking.
        </p>
      </div>

      {/* Filter panel */}
      <div className="glass-panel p-5 rounded-2xl border border-white/5 space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
              <Search className="h-4 w-4" />
            </span>
            <input
              type="text"
              placeholder="Search by keywords, skills, titles or companies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950/60 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>

          <div className="w-full md:w-48 relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
              <Briefcase className="h-4 w-4" />
            </span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full bg-slate-950/60 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-brand-500 transition-colors appearance-none cursor-pointer"
            >
              <option value="">All Roles</option>
              <option value="AI Engineer">AI Engineer</option>
              <option value="Data Scientist">Data Scientist</option>
              <option value="DevOps">DevOps</option>
              <option value="Backend">Backend</option>
              <option value="Frontend">Frontend</option>
            </select>
          </div>

          <div className="w-full md:w-48 relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
              <Layers className="h-4 w-4" />
            </span>
            <select
              value={rank}
              onChange={(e) => setRank(e.target.value)}
              className="w-full bg-slate-950/60 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-brand-500 transition-colors appearance-none cursor-pointer"
            >
              <option value="">All Seniorities</option>
              <option value="junior">Junior</option>
              <option value="mid">Mid-level</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
              <option value="executive">Executive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Grid items */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-slate-400">Querying database schema...</span>
          </div>
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16 glass-panel rounded-2xl border border-white/5">
          <Info className="h-10 w-10 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">No job postings found matching search criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {jobs.map((job) => {
            const relScore = Math.round((job.relevance_score || 0.5) * 100);
            return (
              <div 
                key={job.id} 
                className="glass-panel glass-panel-hover p-6 rounded-2xl flex flex-col justify-between border border-white/5 cursor-pointer"
                onClick={() => setActiveJob(job)}
              >
                <div>
                  <div className="flex justify-between items-start gap-4 mb-3">
                    <div>
                      <h3 className="font-bold text-lg text-white group-hover:text-brand-400 transition-colors">
                        {job.title}
                      </h3>
                      <p className="text-sm text-brand-400 font-semibold">{job.company}</p>
                    </div>
                    
                    {/* Relevance Badge */}
                    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${
                      relScore >= 85 
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                        : relScore >= 70 
                        ? "bg-brand-500/10 text-brand-400 border-brand-500/20" 
                        : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                    }`}>
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>{relScore}% Match</span>
                    </div>
                  </div>

                  <p className="text-sm text-slate-400 line-clamp-3 mb-4 leading-relaxed">
                    {job.description}
                  </p>
                </div>

                <div className="border-t border-white/5 pt-4 space-y-3">
                  {/* Metadata tags */}
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="flex items-center gap-1 bg-slate-900 px-2.5 py-1.5 rounded-lg border border-white/5 text-slate-300">
                      <MapPin className="h-3 w-3 text-slate-400" />
                      <span className="capitalize">{job.workplace_type || "Onsite"}</span>
                    </span>
                    <span className="flex items-center gap-1 bg-slate-900 px-2.5 py-1.5 rounded-lg border border-white/5 text-slate-300">
                      <Layers className="h-3 w-3 text-slate-400" />
                      <span className="capitalize">{job.seniority || "Mid"}</span>
                    </span>
                    {job.salary_max && (
                      <span className="flex items-center gap-1 bg-slate-900 px-2.5 py-1.5 rounded-lg border border-white/5 text-slate-300">
                        <DollarSign className="h-3 w-3 text-slate-400" />
                        <span>
                          {job.salary_min ? `${job.salary_min / 1000}k - ` : ""}
                          {job.salary_max / 1000}k {job.salary_currency || "USD"}
                        </span>
                      </span>
                    )}
                  </div>

                  {/* Date and details trigger */}
                  <div className="flex justify-between items-center text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>Scraped {job.collected_at.split("T")[0]}</span>
                    </span>
                    <span className="text-brand-400 font-semibold flex items-center hover:translate-x-1 transition-transform">
                      View Audit Drawer <ChevronRight className="h-4 w-4" />
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Slide-out Drawer Panel */}
      {activeJob && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex justify-end z-50 animate-fadeIn">
          <div className="w-full max-w-2xl bg-slate-900 border-l border-white/10 h-full flex flex-col justify-between overflow-y-auto animate-slideLeft">
            
            {/* Drawer Header */}
            <div className="p-6 border-b border-white/5 bg-slate-950 flex items-center justify-between sticky top-0 z-10">
              <div>
                <span className="text-xs font-bold text-brand-400 uppercase tracking-widest">{activeJob.company}</span>
                <h2 className="text-xl font-extrabold text-white mt-1">{activeJob.title}</h2>
              </div>
              <button 
                onClick={() => setActiveJob(null)}
                className="h-10 w-10 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white rounded-xl flex items-center justify-center transition-all cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-6 space-y-8 flex-1">
              
              {/* Relevance scoring */}
              <div className="bg-brand-500/5 border border-brand-500/10 p-5 rounded-2xl space-y-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-brand-400" />
                  <h4 className="font-bold text-white text-sm">AI Matching Intelligence Score</h4>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">{Math.round((activeJob.relevance_score || 0.5) * 100)}%</span>
                  <span className="text-slate-400 text-xs font-medium">Relevance Confidence Rate</span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {activeJob.relevance_explanation || "No explanation parsed by AI agent."}
                </p>
              </div>

              {/* Skills Extracted */}
              {activeJob.skills && (
                <div className="space-y-3">
                  <h4 className="font-bold text-slate-200 text-sm uppercase tracking-wider">Skills Extracted & Normalised</h4>
                  <div className="flex flex-wrap gap-2">
                    {activeJob.skills.split(",").map((skill, idx) => (
                      <span 
                        key={idx} 
                        className="bg-slate-950 border border-white/5 text-slate-300 px-3 py-1.5 rounded-lg text-xs font-medium"
                      >
                        {skill.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Description */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-200 text-sm uppercase tracking-wider">Job Description</h4>
                <div className="bg-slate-950/40 border border-white/5 rounded-2xl p-5 text-sm text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                  {activeJob.description}
                </div>
              </div>

              {/* Versions list */}
              <div className="space-y-4">
                <h4 className="font-bold text-slate-200 text-sm uppercase tracking-wider flex items-center gap-2">
                  <History className="h-4 w-4 text-brand-400" /> System Version Audit History
                </h4>
                {activeJob.versions && activeJob.versions.length > 0 ? (
                  <div className="relative border-l border-slate-800 ml-4 pl-6 space-y-6">
                    {activeJob.versions.map((ver, idx) => (
                      <div key={idx} className="relative">
                        {/* Timeline node dot */}
                        <div className="absolute -left-[31px] top-1.5 h-3.5 w-3.5 rounded-full bg-slate-900 border-2 border-brand-500 active-pulse" />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">Version #{ver.version_number}</span>
                            <span className="text-[10px] text-slate-500 font-semibold">{ver.updated_at}</span>
                          </div>
                          <p className="text-xs text-slate-400 mt-1">{ver.changes_payload}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-slate-950/20 border border-white/5 rounded-xl p-4 text-xs text-slate-500 italic">
                    This posting has remained unmodified since first collection. (Single version tracked)
                  </div>
                )}
              </div>

            </div>

            {/* Drawer Footer */}
            <div className="p-6 border-t border-white/5 bg-slate-950/60 sticky bottom-0 z-10 flex gap-4">
              <a
                href={activeJob.url}
                target="_blank"
                rel="noreferrer"
                className="flex-1 bg-slate-900 border border-slate-700/60 hover:bg-slate-800 text-white rounded-xl py-3 px-4 font-semibold text-sm text-center transition-all cursor-pointer"
              >
                View Source URL
              </a>
              <button 
                onClick={() => router.push(`/resume`)}
                className="flex-1 bg-brand-600 hover:bg-brand-500 text-white rounded-xl py-3 px-4 font-semibold text-sm transition-all border border-brand-500/20 cursor-pointer"
              >
                Match with Resume
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
