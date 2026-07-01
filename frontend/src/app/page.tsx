"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Cpu } from "lucide-react";

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen bg-[#090d16] flex flex-col items-center justify-center text-slate-400 gap-4">
      <Cpu className="h-8 w-8 text-brand-500 animate-spin" />
      <span className="text-sm font-semibold tracking-wider font-mono">Bypassing credentials, accessing JobIntel V2 Dashboard...</span>
    </div>
  );
}
