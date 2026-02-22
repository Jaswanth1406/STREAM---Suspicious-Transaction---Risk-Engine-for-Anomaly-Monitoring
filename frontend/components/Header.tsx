"use client";

import { signOut } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { useStreamStore } from "@/lib/store";
import { Menu, MessageSquare, Bell, LogOut, User } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { KPIData } from "@/lib/types";

interface HeaderProps {
  user: { name?: string | null; email?: string | null };
}

export default function Header({ user }: HeaderProps) {
  const router = useRouter();
  const { toggleChat, isChatOpen, toggleSidebar } = useStreamStore();
  const [kpis, setKpis] = useState<KPIData | null>(null);

  useEffect(() => {
    api.kpis().then(setKpis).catch(() => {});
  }, []);

  const handleSignOut = async () => {
    await signOut();
    router.push("/");
  };

  return (
    <header className="h-16 border-b border-border bg-surface/60 header-blur sticky top-0 z-40 flex items-center px-4 md:px-6 justify-between">
      {/* Left */}
      <div className="flex items-center gap-3">
        <button onClick={toggleSidebar} className="lg:hidden text-muted hover:text-text p-1">
          <Menu size={20} />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 flex items-center justify-center">
            <svg viewBox="0 0 40 40" className="w-8 h-8">
              <defs>
                <linearGradient id="logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00b876" />
                  <stop offset="100%" stopColor="#3570e8" />
                </linearGradient>
              </defs>
              <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="url(#logo-grad)" opacity="0.9" />
              <text x="20" y="24" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">S</text>
            </svg>
          </div>
          <span className="font-[var(--font-syne)] text-xl font-extrabold tracking-wider text-text hidden sm:inline">
            STREAM
          </span>
        </div>

        {/* Desktop KPI strip */}
        {kpis && (
          <div className="hidden md:flex items-center gap-6 ml-8">
            <HeaderStat value={(kpis.active_flags ?? 0).toLocaleString()} label="Active Flags" color="text-accent-green" />
            <HeaderStat value={`₹${(kpis.at_risk_value_cr ?? 0).toLocaleString()}Cr`} label="At Risk Value" color="text-accent-red" />
            <HeaderStat value={(kpis.vendors_tracked ?? 0).toLocaleString()} label="Vendors Tracked" color="text-accent-blue" />
            <HeaderStat value={`${kpis.precision_rate ?? 0}%`} label="Precision Rate" color="text-accent-yellow" />
          </div>
        )}
      </div>

      {/* Right */}
      <div className="flex items-center gap-2 md:gap-3">
        <motion.div
          animate={{ opacity: [1, 0.7, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="hidden sm:flex items-center gap-2 bg-accent-green/10 border border-accent-green/30 rounded-full px-3 py-1.5 cursor-pointer"
        >
          <div className="w-2 h-2 rounded-full bg-accent-green pulse-live" />
          <span className="text-accent-green text-xs font-[var(--font-syne)] font-bold tracking-wider">LIVE MONITORING</span>
        </motion.div>

        <button 
          onClick={() => router.push('/dashboard')}
          className="relative text-muted hover:text-text p-2 transition-colors"
          title="View alerts"
        >
          <Bell size={18} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-accent-red rounded-full" />
        </button>

        <button
          onClick={toggleChat}
          className={`p-2 rounded-lg transition-all ${isChatOpen ? 'bg-accent-blue/20 text-accent-blue' : 'text-muted hover:text-text'}`}
        >
          <MessageSquare size={18} />
        </button>

        <div className="flex items-center gap-2 ml-1">
          <div className="hidden md:block text-right">
            <p className="text-xs text-text font-[var(--font-syne)] font-semibold">{user.name || 'Investigator'}</p>
            <p className="text-[10px] text-accent-blue font-[var(--font-space-mono)]">INVESTIGATOR</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center">
            <User size={14} className="text-accent-blue" />
          </div>
        </div>

        <button onClick={handleSignOut} className="text-muted hover:text-accent-red p-2 transition-colors" title="Sign out">
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}

function HeaderStat({ value, label, color }: { value: string; label: string; color: string }) {
  return (
    <div className="text-center">
      <p className={`font-[var(--font-space-mono)] text-sm font-bold ${color}`}>{value}</p>
      <p className="text-muted text-[10px] uppercase tracking-wider">{label}</p>
    </div>
  );
}
