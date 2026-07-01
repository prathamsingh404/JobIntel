"use client";

import React, { useEffect, useState, useRef } from "react";
import { 
  Briefcase, 
  Sparkles, 
  Terminal as TermIcon, 
  Play, 
  Database,
  BarChart3,
  CheckCircle,
  TrendingUp,
  FileDown,
  Loader2,
  Activity,
  Clock,
  AlertTriangle,
  Cpu
} from "lucide-react";

interface DashboardStats {
  total_raw: number;
  total_cleaned: number;
  total_classified: number;
  avg_relevance: number;
  scrapers_running: number;
  roles_distribution: Record<string, number>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_raw: 0,
    total_cleaned: 0,
    total_classified: 0,
    avg_relevance: 0.0,
    scrapers_running: 0,
    roles_distribution: {},
  });
  const [logs, setLogs] = useState<string[]>([]);
  const [targetRole, setTargetRole] = useState("ML Engineer");
  const [progress, setProgress] = useState<any>(null);
  const [triggering, setTriggering] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportResults, setExportResults] = useState<Record<string, string> | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const fetchStats = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/stats");
      if (res.ok) {
        const data = await res.json();
        setStats({
          total_raw: data.counts?.raw ?? 0,
          total_cleaned: data.counts?.cleaned ?? 0,
          total_classified: data.counts?.classified ?? 0,
          avg_relevance: data.avg_relevance_score ?? 0.0,
          scrapers_running: data.is_running ? 1 : 0,
          roles_distribution: data.distributions?.roles ?? {},
        });
      }
    } catch (e) {
      console.error("Error fetching stats:", e);
      // Fallback stats for local preview
      setStats({
        total_raw: 142,
        total_cleaned: 125,
        total_classified: 114,
        avg_relevance: 0.82,
        scrapers_running: 0,
        roles_distribution: { "AI Engineer": 42, "Data Scientist": 28, "DevOps": 15 },
      });
    } finally {
      setLoadingStats(false);
    }
  };

  const fetchProgress = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/scraper/progress");
      if (res.ok) {
        const data = await res.json();
        setProgress(data);
        return data;
      }
    } catch (e) {
      console.error("Error fetching progress:", e);
    }
    return null;
  };

  useEffect(() => {
    fetchStats();
    fetchProgress();
    const statsInterval = setInterval(fetchStats, 10000);

    let wasRunning = false;
    const progressInterval = setInterval(async () => {
      const prog = await fetchProgress();
      if (prog) {
        if (prog.is_running) {
          fetchStats(); // Update stats cards in real-time while running
        } else if (wasRunning && !prog.is_running) {
          fetchStats(); // finished, refresh stats
        }
        wasRunning = prog.is_running;
      }
    }, 1500);

    // WebSocket Logger
    const ws = new WebSocket("ws://localhost:8000/api/logs/ws");
    ws.onmessage = (event) => {
      setLogs((prev) => {
        const next = [...prev, event.data];
        return next.slice(-100); // limit to last 100 entries
      });
    };

    return () => {
      clearInterval(statsInterval);
      clearInterval(progressInterval);
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const handleTriggerIngestion = async () => {
    setTriggering(true);
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [TRIGGER] Ingestion requested for target role '${targetRole}'...`]);
    try {
      const res = await fetch("http://localhost:8000/api/trigger", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ role: targetRole }),
      });
      const data = await res.json();
      if (res.ok) {
        setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [SYSTEM] Ingestion started: ${data.message}`]);
        // Trigger immediate progress refresh
        setTimeout(fetchProgress, 500);
      } else {
        setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [ERROR] Start failed: ${data.message || "Conflict"}`]);
      }
    } catch (e: any) {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [ERROR] API unavailable: ${e.message}`]);
    } finally {
      setTriggering(false);
      fetchStats();
    }
  };

  const handleStopIngestion = async () => {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [TRIGGER] Requesting pipeline shutdown...`]);
    try {
      const res = await fetch("http://localhost:8000/api/stop", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [SYSTEM] Ingestion stopping: ${data.message}`]);
        setTimeout(fetchProgress, 500);
      } else {
        setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [ERROR] Stop failed: ${data.message}`]);
      }
    } catch (e: any) {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [ERROR] API unavailable: ${e.message}`]);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    setExportResults(null);
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [TRIGGER] Export job triggered...`]);
    try {
      const res = await fetch("http://localhost:8000/api/export", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setExportResults(data.exports);
        setLogs((prev) => [
          ...prev, 
          `[${new Date().toLocaleTimeString()}] [SYSTEM] ML Datasets exported successfully.`,
          ...Object.entries(data.exports).map(([k, v]) => `   - ${k}: ${v}`)
        ]);
      } else {
        setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [ERROR] Export failed: ${data.message}`]);
      }
    } catch (e: any) {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] [ERROR] Export service unavailable: ${e.message}`]);
    } finally {
      setExporting(false);
    }
  };

  const renderProgressCockpit = () => {
    if (!progress || (!progress.is_running && !progress.current_role)) return null;

    const {
      current_role,
      is_running,
      started_at,
      collectors,
      processing_total,
      processing_current,
      processed_cleaned,
      processed_rejected,
      completed_at,
      error_message
    } = progress;

    const totalScraped = Object.values(collectors || {}).reduce(
      (sum: number, col: any) => sum + (col.total || col.count || 0),
      0
    ) as number;

    const batchNumber = progress.batch_number || 1;

    const hasProcessingStarted = processing_total > 0;
    const processingPercent = hasProcessingStarted
      ? Math.min(100, Math.round((processing_current / processing_total) * 100))
      : 0;

    return (
      <div className="glass-panel border border-white/5 p-6 rounded-2xl space-y-6 shadow-2xl relative overflow-hidden animate-fadeIn">
        {/* Background Glowing Orb */}
        <div className={`absolute top-0 right-0 w-64 h-64 rounded-full filter blur-[85px] pointer-events-none -z-10 transition-all duration-1000 ${
          is_running 
            ? "bg-brand-600/10" 
            : error_message 
            ? "bg-red-500/10" 
            : "bg-emerald-500/10"
        }`} />

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-white/5 pb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-slate-900 border border-white/5 rounded-xl flex items-center justify-center">
              {is_running ? (
                <Activity className="h-5 w-5 text-brand-400 animate-pulse" />
              ) : error_message ? (
                <AlertTriangle className="h-5 w-5 text-red-400" />
              ) : (
                <CheckCircle className="h-5 w-5 text-emerald-400" />
              )}
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                Active Ingestion Pipeline
                {is_running ? (
                  <span className="text-[10px] bg-brand-500/20 text-brand-300 px-2 py-0.5 rounded-full border border-brand-500/30 font-bold uppercase tracking-wider active-pulse">
                    Live
                  </span>
                ) : error_message ? (
                  <span className="text-[10px] bg-red-500/20 text-red-300 px-2 py-0.5 rounded-full border border-red-500/30 font-bold uppercase tracking-wider">
                    Failed
                  </span>
                ) : (
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/30 font-bold uppercase tracking-wider">
                    Completed
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Target Keyword: <span className="font-semibold text-slate-200">"{current_role}"</span>
                {started_at && ` • Started: ${new Date(started_at).toLocaleTimeString()}`}
                {is_running && ` • Batch #${batchNumber}`}
              </p>
            </div>
          </div>
          
          <div className="text-left md:text-right">
            <p className="text-xs text-slate-400">Total Scraped Raw Jobs</p>
            <p className="text-xl font-black text-white">{totalScraped} jobs</p>
          </div>
        </div>

        {/* Error message */}
        {error_message && (
          <div className="bg-red-950/20 border border-red-500/20 rounded-xl p-4 flex gap-3 text-xs text-red-400">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <div>
              <span className="font-bold">Pipeline Error:</span> {error_message}
            </div>
          </div>
        )}

        {/* Phase 1: Collector Hub */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-400" />
            Phase 1: Multi-Source Scraping Hub
          </h3>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            {Object.entries(collectors || {}).map(([name, data]: [string, any]) => {
              const statusColors = {
                pending: "bg-slate-900 border-white/5 text-slate-500",
                scraping: "bg-amber-500/10 border-amber-500/30 text-amber-300 active-pulse",
                completed: "bg-emerald-500/10 border-emerald-500/30 text-emerald-300",
                failed: "bg-red-500/10 border-red-500/30 text-red-300"
              }[data.status as "pending" | "scraping" | "completed" | "failed"] || "bg-slate-900 border-white/5 text-slate-500";

              return (
                <div 
                  key={name} 
                  className={`border p-3 rounded-xl flex flex-col justify-between transition-all duration-300 ${statusColors}`}
                >
                  <span className="text-[11px] font-bold capitalize truncate">{name.replace("_", " ")}</span>
                  <div className="mt-2 flex flex-col gap-1">
                    <div className="flex justify-between items-baseline">
                      <span className="text-[9px] uppercase font-bold tracking-wider opacity-80">
                        {data.status}
                      </span>
                      {(data.total > 0 || data.count > 0) && (
                        <span className="text-xs font-black">{data.total || data.count}</span>
                      )}
                    </div>
                    {data.count > 0 && data.total > data.count && (
                      <span className="text-[9px] text-slate-500">+{data.count} this batch</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Phase 2: AI Processing */}
        <div className="space-y-4 pt-2">
          <div className="flex justify-between items-center">
            <h3 className="text-xs font-bold font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-purple-400" />
              Phase 2: AI Classification & Filtering
            </h3>
            {hasProcessingStarted ? (
              <span className="text-xs font-bold font-mono text-purple-400">
                {processing_current} / {processing_total} processed ({processingPercent}%)
              </span>
            ) : (
              <span className="text-xs text-slate-500 font-mono italic">Waiting for scraping to complete...</span>
            )}
          </div>

          <div className="space-y-2">
            {/* Progress Bar Container */}
            <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden border border-white/5">
              <div 
                className="h-full bg-gradient-to-r from-brand-500 via-indigo-500 to-purple-500 rounded-full transition-all duration-500 ease-out" 
                style={{ width: `${processingPercent}%` }}
              />
            </div>

            {/* AI Counts stats */}
            {hasProcessingStarted && (
              <div className="flex flex-wrap gap-4 text-xs font-mono pt-1">
                <div className="flex items-center gap-1.5 bg-emerald-950/20 border border-emerald-500/20 px-3 py-1.5 rounded-lg text-emerald-400">
                  <CheckCircle className="h-3.5 w-3.5" />
                  <span>Validated & Cleaned: <strong className="text-white">{processed_cleaned}</strong></span>
                </div>
                <div className="flex items-center gap-1.5 bg-red-950/20 border border-red-500/20 px-3 py-1.5 rounded-lg text-red-400">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span>Filtered & Rejected: <strong className="text-white">{processed_rejected}</strong></span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const dashboardCards = [
    {
      title: "Raw Jobs Scraped",
      value: stats.total_raw,
      icon: Database,
      color: "from-blue-500/10 to-blue-500/20 text-blue-400 border-blue-500/20",
      description: "Aggregated from multi-source collector hubs"
    },
    {
      title: "Cleaned & Normalised",
      value: stats.total_cleaned,
      icon: CheckCircle,
      color: "from-emerald-500/10 to-emerald-500/20 text-emerald-400 border-emerald-500/20",
      description: "Successfully deduplicated & validated"
    },
    {
      title: "AI Classified Profiled",
      value: stats.total_classified,
      icon: Sparkles,
      color: "from-purple-500/10 to-purple-500/20 text-purple-400 border-purple-500/20",
      description: "Structured role, rank, and skills extraction"
    },
    {
      title: "Avg Relevance Fit",
      value: `${Math.round(stats.avg_relevance * 100)}%`,
      icon: TrendingUp,
      color: "from-amber-500/10 to-amber-500/20 text-amber-400 border-amber-500/20",
      description: "Candidate skill mapping match average"
    }
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Ingestion Control Room</h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time monitoring, AI pipelines orchestration, and export generators.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {/* Keyword role selector input */}
          <div className="flex items-center bg-slate-900 border border-slate-700/60 rounded-xl px-3 py-2 focus-within:border-brand-500 transition-all">
            <span className="text-xs text-slate-400 font-bold mr-2 uppercase tracking-wider">Scrape Target:</span>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. ML Engineer"
              className="bg-transparent border-none text-white text-sm font-semibold outline-none focus:ring-0 w-36 md:w-44 placeholder-slate-600"
            />
          </div>

          <button
            onClick={handleExportData}
            disabled={exporting}
            className="flex items-center gap-2 bg-slate-900 border border-slate-700/60 hover:bg-slate-800 disabled:opacity-50 text-slate-200 font-semibold px-4 py-2.5 rounded-xl text-sm transition-all cursor-pointer"
          >
            {exporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileDown className="h-4 w-4" />
            )}
            <span>Export ML Datasets</span>
          </button>
          
          {progress && progress.is_running ? (
            <button
              onClick={handleStopIngestion}
              className="flex items-center gap-2 bg-red-600 border border-red-500/30 hover:bg-red-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm shadow-lg shadow-red-600/10 transition-all cursor-pointer animate-pulse"
            >
              <Activity className="h-4 w-4" />
              <span>Stop Ingestion Pipeline</span>
            </button>
          ) : (
            <button
              onClick={handleTriggerIngestion}
              disabled={triggering}
              className="flex items-center gap-2 bg-brand-600 border border-brand-500/30 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-xl text-sm shadow-lg shadow-brand-600/10 transition-all cursor-pointer"
            >
              {triggering ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              <span>Trigger Ingestion Pipeline</span>
            </button>
          )}
        </div>
      </div>

      {/* Grid of stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div 
              key={idx} 
              className={`glass-panel border p-6 rounded-2xl flex flex-col justify-between relative overflow-hidden`}
            >
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-semibold text-slate-400 uppercase tracking-wider">{card.title}</span>
                <div className={`h-10 w-10 bg-gradient-to-br ${card.color} rounded-xl flex items-center justify-center border`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <div>
                <p className="text-3xl font-extrabold text-white tracking-tight mb-1">
                  {loadingStats ? <Loader2 className="h-6 w-6 animate-spin text-slate-500" /> : card.value}
                </p>
                <p className="text-xs text-slate-400">{card.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live progress section */}
      {renderProgressCockpit()}

      {/* Export results box */}
      {exportResults && (
        <div className="glass-panel p-6 rounded-2xl border border-emerald-500/20 bg-emerald-950/10 animate-fadeIn">
          <h3 className="text-emerald-400 font-semibold text-sm mb-3 flex items-center gap-2">
            <CheckCircle className="h-4 w-4" /> ML Dataset Export Completed
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono text-slate-300">
            {Object.entries(exportResults).map(([format, path]) => (
              <div key={format} className="flex justify-between bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
                <span className="uppercase text-slate-400 font-bold">{format}</span>
                <span className="truncate max-w-[250px] text-slate-300 select-all" title={path}>{path.split(/[\\/]/).pop()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logging Terminal */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-white/5 shadow-2xl flex flex-col h-[400px]">
        {/* Terminal Header */}
        <div className="bg-slate-950/90 px-6 py-3 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TermIcon className="h-4 w-4 text-brand-400 active-pulse" />
            <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">Asynchronous Job Workers Terminal</span>
          </div>
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-red-500/50" />
            <div className="h-3 w-3 rounded-full bg-amber-500/50" />
            <div className="h-3 w-3 rounded-full bg-emerald-500/50" />
          </div>
        </div>

        {/* Terminal Console */}
        <div className="flex-1 bg-slate-950/70 p-6 overflow-y-auto font-mono text-xs text-brand-300/90 space-y-2 selection:bg-brand-500/30">
          {logs.length === 0 ? (
            <div className="text-slate-500 italic">No logs received. Launch a scraper execution or wait for polling updates...</div>
          ) : (
            logs.map((log, i) => (
              <div 
                key={i} 
                className={`leading-relaxed border-l-2 pl-3 ${
                  log.includes("[ERROR]") 
                    ? "border-red-500 text-red-400" 
                    : log.includes("[TRIGGER]") 
                    ? "border-brand-500 text-brand-400" 
                    : log.includes("[SYSTEM]")
                    ? "border-emerald-500 text-emerald-300"
                    : "border-slate-800 text-slate-400"
                }`}
              >
                {log}
              </div>
            ))
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
