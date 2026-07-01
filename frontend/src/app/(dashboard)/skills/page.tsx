"use client";

import React, { useEffect, useState } from "react";
import { 
  Terminal as TermIcon, 
  Share2, 
  Flame, 
  Layers, 
  HelpCircle,
  Activity,
  ArrowRight,
  TrendingUp,
  Award
} from "lucide-react";

interface TopSkill {
  name: string;
  count: number;
}

interface KnowledgeEdge {
  source: string;
  target: string;
  type: string;
}

export default function SkillsAnalysisPage() {
  const [topSkills, setTopSkills] = useState<TopSkill[]>([]);
  const [graphEdges, setGraphEdges] = useState<KnowledgeEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"distribution" | "knowledge-graph">("distribution");

  const fetchSkills = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/skills");
      if (res.ok) {
        const data = await res.json();
        setTopSkills(data.top_skills);
        setGraphEdges(data.knowledge_graph);
      }
    } catch (e) {
      console.error("Error fetching skills:", e);
      // Fallback data
      setTopSkills([
        { name: "Python", count: 42 },
        { name: "PyTorch", count: 35 },
        { name: "LangChain", count: 28 },
        { name: "Kubernetes", count: 24 },
        { name: "SQL", count: 20 },
        { name: "Docker", count: 18 },
        { name: "TensorFlow", count: 15 },
        { name: "Qdrant", count: 12 },
        { name: "React", count: 10 }
      ]);
      setGraphEdges([
        { source: "Machine Learning", target: "Deep Learning", type: "parent" },
        { source: "Deep Learning", target: "PyTorch", type: "framework" },
        { source: "Deep Learning", target: "TensorFlow", type: "framework" },
        { source: "Generative AI", target: "LangChain", type: "framework" },
        { source: "Generative AI", target: "LlamaIndex", type: "framework" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();

    const interval = setInterval(() => {
      const fetchSkillsSilent = async () => {
        try {
          const res = await fetch("http://localhost:8000/api/skills");
          if (res.ok) {
            const data = await res.json();
            setTopSkills(data.top_skills);
            setGraphEdges(data.knowledge_graph);
          }
        } catch (e) {
          console.error("Silent skills polling error:", e);
        }
      };
      fetchSkillsSilent();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const maxCount = topSkills.length > 0 ? Math.max(...topSkills.map(s => s.count)) : 1;

  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Skills Intelligence & Knowledge Graph</h1>
        <p className="text-slate-400 text-sm mt-1">
          Review extracted keyword frequency indices and hierarchical skill association paths parsed by AI engines.
        </p>
      </div>

      {/* Tabs selection */}
      <div className="flex border-b border-white/5 space-x-6">
        <button
          onClick={() => setActiveTab("distribution")}
          className={`pb-4 text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === "distribution" 
              ? "border-b-2 border-brand-500 text-white" 
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Flame className="h-4 w-4" />
          <span>Top In-Demand Skills</span>
        </button>
        <button
          onClick={() => setActiveTab("knowledge-graph")}
          className={`pb-4 text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === "knowledge-graph" 
              ? "border-b-2 border-brand-500 text-white" 
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Share2 className="h-4 w-4" />
          <span>Hierarchical Skill Relations</span>
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : activeTab === "distribution" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main distribution list */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-white/5 space-y-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Award className="h-5 w-5 text-brand-400" />
              <span>Skill Frequency Metrics</span>
            </h3>

            <div className="space-y-4">
              {topSkills.map((skill, index) => {
                const percentage = Math.round((skill.count / maxCount) * 100);
                return (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-200">{skill.name}</span>
                      <span className="text-brand-400">{skill.count} job postings</span>
                    </div>
                    <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden border border-white/5">
                      <div 
                        className="h-full bg-gradient-to-r from-brand-600 to-brand-400 rounded-full transition-all duration-500 ease-out" 
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Intel card */}
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-4">
              <div className="h-10 w-10 bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-xl flex items-center justify-center">
                <TrendingUp className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Market Insights</h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Python and PyTorch remain the leading technologies demanded across AI recruiting pools, appearing in over 60% of open requisitions.
              </p>
              <p className="text-sm text-slate-300 leading-relaxed">
                LLM Framework wrappers (LangChain, LlamaIndex) are seeing a 45% quarter-on-quarter increase in postings.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Flow connections list */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-white/5">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <Share2 className="h-5 w-5 text-brand-400" />
              <span>Skill Hierarchy Links</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {graphEdges.map((edge, index) => (
                <div 
                  key={index}
                  className="bg-slate-950/50 border border-white/5 hover:border-brand-500/20 p-4 rounded-xl flex items-center justify-between text-xs transition-colors"
                >
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Source Skill</span>
                    <p className="font-bold text-white text-sm">{edge.source}</p>
                  </div>
                  <div className="flex flex-col items-center px-4">
                    <span className="text-[9px] bg-slate-900 border border-white/10 px-2 py-0.5 rounded text-brand-400 font-bold uppercase tracking-wider mb-1">
                      {edge.type}
                    </span>
                    <ArrowRight className="h-4 w-4 text-slate-500" />
                  </div>
                  <div className="space-y-1 text-right">
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Target Skill</span>
                    <p className="font-bold text-white text-sm">{edge.target}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Graph Legend Panel */}
          <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-4">
            <div className="h-10 w-10 bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-xl flex items-center justify-center">
              <Layers className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-white">Hierarchy Mapping</h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              The skill knowledge graph structures related concepts. An applicant matching a child node (e.g. `PyTorch`) automatically inherits association matching for the parent skill category (`Deep Learning`).
            </p>
            <div className="space-y-2 pt-3">
              <div className="flex items-center gap-2 text-xs">
                <span className="h-2 w-2 rounded-full bg-brand-500" />
                <span className="text-slate-300 font-medium">parent: General category linkage</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="text-slate-300 font-medium">framework: Concrete development package</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
