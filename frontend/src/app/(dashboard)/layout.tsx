"use client";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { 
  LayoutDashboard, 
  Briefcase, 
  Building2, 
  Terminal, 
  FileText, 
  LogOut, 
  User, 
  Wifi, 
  WifiOff,
  Cpu
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setEmail(localStorage.getItem("jobintel_email") || "admin@jobintel.io");
    setRole(localStorage.getItem("jobintel_role") || "Senior Recruiter");

    // Initialize checking websocket status or generic connection heartbeat
    const ws = new WebSocket("ws://localhost:8000/api/logs/ws");
    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => setWsStatus("disconnected");
    ws.onerror = () => setWsStatus("disconnected");

    return () => {
      ws.close();
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("jobintel_token");
    localStorage.removeItem("jobintel_email");
    localStorage.removeItem("jobintel_role");
    router.push("/");
  };

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Job Explorer", href: "/jobs", icon: Briefcase },
    { name: "Companies", href: "/companies", icon: Building2 },
    { name: "Skills Analysis", href: "/skills", icon: Terminal },
    { name: "Resume Matching", href: "/resume", icon: FileText },
  ];

  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#090d16] flex items-center justify-center">
        <Cpu className="h-8 w-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 overflow-hidden">
      {/* Navigation Sidebar */}
      <aside className="w-64 bg-slate-950/70 border-r border-white/5 flex flex-col justify-between z-20">
        <div>
          {/* Brand Logo */}
          <div className="h-16 flex items-center gap-3 px-6 border-b border-white/5">
            <div className="h-8 w-8 bg-brand-500/20 text-brand-400 rounded-lg flex items-center justify-center border border-brand-500/30">
              <Cpu className="h-4 w-4 active-pulse" />
            </div>
            <span className="font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-brand-400">
              JobIntel V2
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? "bg-brand-600 text-white shadow-lg shadow-brand-600/10 border border-brand-500/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Info / Logout */}
        <div className="p-4 border-t border-white/5 space-y-4">
          <div className="flex items-center gap-3 px-2">
            <div className="h-10 w-10 bg-slate-800 rounded-full flex items-center justify-center border border-slate-700 text-slate-300">
              <User className="h-5 w-5" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-white truncate">{email}</p>
              <p className="text-xs text-slate-400 capitalize">{role}</p>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs px-2 py-1 bg-slate-900/40 rounded-lg border border-white/5">
            <span className="text-slate-400">Server API</span>
            <div className="flex items-center gap-1.5 font-medium">
              {wsStatus === "connected" ? (
                <>
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 active-pulse" />
                  <span className="text-emerald-400 flex items-center gap-1">
                    <Wifi className="h-3 w-3" /> Online
                  </span>
                </>
              ) : (
                <>
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                  <span className="text-red-400 flex items-center gap-1">
                    <WifiOff className="h-3 w-3" /> Offline
                  </span>
                </>
              )}
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white rounded-xl py-2.5 px-4 text-xs font-semibold border border-white/5 hover:border-white/10 transition-all duration-200 cursor-pointer"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Viewport */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto relative grid-bg">
        <div className="absolute inset-0 radial-glow pointer-events-none -z-10" />
        <div className="p-8 max-w-7xl w-full mx-auto space-y-8">
          {children}
        </div>
      </main>
    </div>
  );
}
