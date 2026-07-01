"use client";

import React, { useState } from "react";
import { 
  FileText, 
  Upload, 
  Sparkles, 
  CheckCircle2, 
  TrendingUp, 
  Cpu, 
  AlertTriangle,
  Loader2,
  BookOpen,
  ArrowRight,
  ClipboardList
} from "lucide-react";
import confetti from "canvas-confetti";

interface MatchResult {
  job_id: string | number;
  title: string;
  company: string;
  location: string;
  match_score: number;
  missing_skills: string[];
  strengths: string[];
  roadmap: string[];
}

export default function ResumeMatcherPage() {
  const [resumeText, setResumeText] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<MatchResult[] | null>(null);
  const [fileName, setFileName] = useState("pasted_text.txt");
  const [error, setError] = useState("");

  const triggerConfetti = () => {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  };

  const handleComputeMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeText.trim()) {
      setError("Please paste or write your resume text first.");
      return;
    }

    setLoading(true);
    setError("");
    setResults(null);

    try {
      // Create a Blob from the resume text to send as a file
      const blob = new Blob([resumeText], { type: "text/plain" });
      const formData = new FormData();
      formData.append("file", blob, fileName);

      const res = await fetch("http://localhost:8000/api/resume/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Unable to analyze resume. Make sure backend is running.");
      }

      const data = await res.json();
      setResults(data.top_matches || []);
      triggerConfetti();
    } catch (e: any) {
      console.error(e);
      // Fallback mocks on connection issue
      setError("Backend connection timed out. Showing fallback analytics model.");
      setResults([
        {
          job_id: "1",
          title: "Senior AI Engineer",
          company: "NeuralFlow Solutions",
          location: "San Francisco, CA (Hybrid)",
          match_score: 92,
          strengths: [
            "Strong foundation in PyTorch and neural network design",
            "Extensive background operating Large Language Models and engineering prompts",
            "Proficient in REST architecture and Python backend design"
          ],
          missing_skills: [
            "Qdrant",
            "LangChain",
            "LlamaIndex"
          ],
          roadmap: [
            "Complete a course or tutorial on vector indexing concepts using Qdrant.",
            "Build a prototype Retrieval-Augmented Generation agent with LangChain.",
            "Deploy a custom container pipeline orchestrating both libraries."
          ]
        },
        {
          job_id: "2",
          title: "Data Scientist",
          company: "FinIntel Corp",
          location: "New York, NY",
          match_score: 74,
          strengths: [
            "Solid experience manipulating data with Pandas and Numpy",
            "Familiarity with Scikit-learn predictive frameworks"
          ],
          missing_skills: [
            "SQL",
            "Tableau",
            "Distributed Computing"
          ],
          roadmap: [
            "Improve relational database skills by learning window functions and recursive CTEs.",
            "Practice creating visual business dashboards using Tableau or PowerBI."
          ]
        }
      ]);
      triggerConfetti();
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (event) => {
        setResumeText(event.target?.result as string || "");
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Semantic Resume Matcher</h1>
        <p className="text-slate-400 text-sm mt-1">
          Upload or paste candidate profiles to calculate match percentages against open requisitions and output personalized roadmaps.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left input container */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-5">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-brand-400" /> Input Workspace
            </h3>

            {error && (
              <div className="bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs rounded-xl p-3">
                {error}
              </div>
            )}

            <form onSubmit={handleComputeMatch} className="space-y-4">
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Resume text content
                </label>
                <textarea
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  placeholder="Paste raw text contents of the resume here..."
                  className="w-full h-80 bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors resize-none font-mono"
                />
              </div>

              {/* File upload connector */}
              <div className="border border-dashed border-slate-800 rounded-xl p-4 text-center hover:bg-slate-950/30 transition-colors relative cursor-pointer">
                <input
                  type="file"
                  accept=".txt,.md"
                  onChange={handleFileUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <Upload className="h-5 w-5 text-slate-500 mx-auto mb-2" />
                <p className="text-xs text-slate-400 font-medium">Or click to upload .txt profile</p>
                <span className="text-[10px] text-slate-500 truncate block mt-1">{fileName}</span>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-xl py-3 px-4 font-semibold text-sm transition-all border border-brand-500/20 flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Compute Match Fit</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Right results display */}
        <div className="lg:col-span-2 space-y-6">
          {!results ? (
            <div className="h-full min-h-[400px] border border-dashed border-slate-800 rounded-2xl flex flex-col justify-center items-center text-center p-8 bg-slate-950/10">
              <FileText className="h-12 w-12 text-slate-600 mb-3" />
              <h4 className="text-slate-400 font-bold">Awaiting Input Profile</h4>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Enter your work history, skills, and projects in the text workspace to calculate alignment scoring.
              </p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-16 glass-panel rounded-2xl border border-white/5">
              <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-3" />
              <p className="text-slate-400 font-medium">No matching jobs indexed in the platform database.</p>
            </div>
          ) : (
            <div className="space-y-6">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 active-pulse" /> Top Requisition Matches
              </h3>

              {results.map((match, idx) => {
                const score = match.match_score;
                return (
                  <div key={idx} className="glass-panel p-6 rounded-2xl border border-white/5 space-y-6">
                    {/* Header */}
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <h4 className="text-lg font-bold text-white">{match.title}</h4>
                        <p className="text-xs font-semibold text-brand-400">{match.company} • {match.location}</p>
                      </div>
                      
                      {/* Circular Match Dial */}
                      <div className={`h-16 w-16 rounded-2xl flex flex-col items-center justify-center border ${
                        score >= 80 
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" 
                          : "bg-brand-500/10 border-brand-500/20 text-brand-400"
                      }`}>
                        <span className="text-lg font-extrabold">{score}%</span>
                        <span className="text-[8px] uppercase font-bold">Match</span>
                      </div>
                    </div>

                    {/* Breakdown grids */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/5 text-xs">
                      
                      {/* Strengths */}
                      <div className="space-y-3">
                        <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                          <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Candidate Strengths
                        </span>
                        <ul className="space-y-2 text-slate-300">
                          {match.strengths.map((str, i) => (
                            <li key={i} className="flex gap-2 bg-slate-950/30 p-2.5 rounded-lg border border-white/5">
                              <span className="text-emerald-400 font-bold">•</span>
                              <span>{str}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Gaps / Missing skills */}
                      <div className="space-y-3">
                        <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                          <AlertTriangle className="h-4 w-4 text-amber-400" /> Missing Requisition Skills
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {match.missing_skills.length > 0 ? (
                            match.missing_skills.map((skill, i) => (
                              <span 
                                key={i}
                                className="bg-amber-500/10 border border-amber-500/20 text-amber-400 px-2.5 py-1.5 rounded-lg font-semibold"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-slate-500 italic text-xs">All required skills matched!</span>
                          )}
                        </div>
                      </div>

                    </div>

                    {/* Upskilling Career Roadmap */}
                    <div className="pt-4 border-t border-white/5 space-y-3">
                      <span className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-1.5">
                        <BookOpen className="h-4 w-4 text-brand-400" /> Structured Upskilling Career Roadmap
                      </span>
                      <div className="space-y-2">
                        {match.roadmap.map((step, i) => (
                          <div 
                            key={i} 
                            className="flex items-center gap-3 bg-slate-950/40 p-3 rounded-xl border border-white/5"
                          >
                            <div className="h-6 w-6 rounded-lg bg-brand-500/10 border border-brand-500/20 text-brand-400 font-bold flex items-center justify-center text-[10px] shrink-0">
                              0{i + 1}
                            </div>
                            <p className="text-xs text-slate-300 leading-relaxed">{step}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
