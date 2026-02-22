"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import Link from "next/link";
import { useRef } from "react";
import {
  Shield,
  Network,
  AlertTriangle,
  Eye,
  BarChart3,
  Brain,
  ArrowRight,
  ChevronDown,
  Lock,
  Scale,
  Building2,
  Target,
  Fingerprint,
  Globe,
  Zap,
  CheckCircle2,
  MousePointerClick,
  Activity,
  FileWarning,
  TrendingUp,
  Users,
} from "lucide-react";

/* ───── animation presets ───── */
const fadeUp = {
  initial: { opacity: 0, y: 30 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.7, ease: "easeOut" as const },
};
const stagger = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
};

/* ═══════════════════════════════════════════════════════
   INLINE SVG DASHBOARD MOCKUP COMPONENTS
   These replace real screenshots with animated CSS art
   ═══════════════════════════════════════════════════════ */

function DashboardMockup() {
  return (
    <div className="relative w-full max-w-4xl mx-auto">
      {/* Main dashboard card */}
      <motion.div
        initial={{ opacity: 0, y: 60, rotateX: 8 }}
        animate={{ opacity: 1, y: 0, rotateX: 0 }}
        transition={{ duration: 1.2, delay: 0.4, ease: "easeOut" }}
        className="relative rounded-2xl border border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm overflow-hidden shadow-2xl"
        style={{ perspective: 1200 }}
      >
        {/* Title bar */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[var(--border)] bg-[var(--surface)]">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[var(--accent-red)] opacity-70" />
            <div className="w-3 h-3 rounded-full bg-[var(--accent-yellow)] opacity-70" />
            <div className="w-3 h-3 rounded-full bg-[var(--accent-green)] opacity-70" />
          </div>
          <div className="flex-1 flex justify-center">
            <div className="bg-[var(--bg)]/80 rounded-md px-16 py-1 text-[10px] text-[var(--muted)] font-[var(--font-space-mono)]">
              stream-intel.gov.in/dashboard
            </div>
          </div>
        </div>

        {/* Dashboard content mockup */}
        <div className="p-4 grid grid-cols-12 gap-3" style={{ minHeight: 280 }}>
          {/* Sidebar mock */}
          <div className="col-span-3 hidden md:block space-y-2">
            <div className="h-8 rounded-lg bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 flex items-center px-2">
              <div className="w-3 h-3 rounded bg-[var(--accent-green)]/50 mr-2" />
              <div className="h-2 w-16 rounded bg-[var(--accent-green)]/30" />
            </div>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-7 rounded-lg bg-[var(--surface2)]/50 border border-[var(--border)]/50 flex items-center px-2">
                <div className="w-2.5 h-2.5 rounded bg-[var(--muted)]/20 mr-2" />
                <div className="h-1.5 rounded bg-[var(--muted)]/15" style={{ width: 40 + i * 12 }} />
              </div>
            ))}
            <div className="mt-3 pt-3 border-t border-[var(--border)]/30 space-y-2">
              {[
                "var(--accent-red)",
                "var(--accent-yellow)",
                "var(--accent-blue)",
                "var(--accent-green)",
              ].map((color, i) => (
                <div key={i} className="flex items-center gap-2 px-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: `var(${color.replace("var(", "").replace(")", "")})` }} />
                  <div className="h-1.5 w-12 rounded bg-[var(--muted)]/15" />
                </div>
              ))}
            </div>
          </div>

          {/* Center content */}
          <div className="col-span-12 md:col-span-6 space-y-3">
            {/* KPI row */}
            <div className="grid grid-cols-4 gap-2">
              {[
                { val: "47", color: "var(--accent-red)" },
                { val: "₹2.8K", color: "var(--accent-yellow)" },
                { val: "1,247", color: "var(--accent-blue)" },
                { val: "94.2%", color: "var(--accent-green)" },
              ].map((kpi, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 1.0 + i * 0.1 }}
                  className="bg-[var(--surface2)]/50 rounded-lg p-2 border border-[var(--border)]/50 text-center"
                >
                  <p className="font-[var(--font-space-mono)] text-sm font-bold" style={{ color: kpi.color }}>
                    {kpi.val}
                  </p>
                  <div className="h-1 w-10 mx-auto rounded bg-[var(--muted)]/10 mt-1" />
                </motion.div>
              ))}
            </div>

            {/* Alert cards mock */}
            {[
              { score: 92, color: "var(--accent-red)", w1: "70%", w2: "45%" },
              { score: 87, color: "var(--accent-red)", w1: "60%", w2: "55%" },
              { score: 74, color: "var(--accent-yellow)", w1: "80%", w2: "35%" },
            ].map((alert, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.3 + i * 0.15 }}
                className="bg-[var(--surface2)]/30 rounded-xl p-3 border border-[var(--border)]/40 flex items-center gap-3"
              >
                <div className="font-[var(--font-space-mono)] text-lg font-bold w-10 text-center" style={{ color: alert.color }}>
                  {alert.score}
                </div>
                <div className="flex-1 space-y-1.5">
                  <div className="h-2 rounded" style={{ width: alert.w1, background: "rgba(26,31,54,0.08)" }} />
                  <div className="h-1.5 rounded" style={{ width: alert.w2, background: "rgba(107,115,148,0.12)" }} />
                </div>
                <div className="h-8 w-1 rounded-full" style={{ background: alert.color, opacity: 0.5 }} />
              </motion.div>
            ))}
          </div>

          {/* Right panel mock */}
          <div className="col-span-3 hidden md:block space-y-3">
            {/* Animated risk ring */}
            <div className="flex justify-center">
              <motion.svg
                viewBox="0 0 80 80"
                className="w-16 h-16"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.5 }}
              >
                <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(216,220,232,0.8)" strokeWidth="5" />
                <motion.circle
                  cx="40"
                  cy="40"
                  r="32"
                  fill="none"
                  stroke="#e53e5c"
                  strokeWidth="5"
                  strokeLinecap="round"
                  strokeDasharray="201"
                  initial={{ strokeDashoffset: 201 }}
                  animate={{ strokeDashoffset: 30 }}
                  transition={{ delay: 1.8, duration: 1.5, ease: "easeOut" }}
                  transform="rotate(-90 40 40)"
                />
                <text x="40" y="44" textAnchor="middle" fill="#e53e5c" fontSize="14" fontWeight="bold" fontFamily="monospace">87</text>
              </motion.svg>
            </div>
            <div className="space-y-1.5">
              {[65, 82, 45, 71].map((val, i) => (
                <div key={i} className="px-2">
                  <div className="h-1.5 w-full rounded-full bg-[var(--border)]/30 overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: val >= 80 ? "#e53e5c" : val >= 60 ? "#d49a00" : "#3570e8" }}
                      initial={{ width: 0 }}
                      animate={{ width: `${val}%` }}
                      transition={{ delay: 2.0 + i * 0.1, duration: 0.8 }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="space-y-1.5 pt-2 border-t border-[var(--border)]/30">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-5 rounded bg-[var(--surface2)]/30 border border-[var(--border)]/30 mx-1" />
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Floating annotation badges */}
      <motion.div
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 2.0, duration: 0.6 }}
        className="absolute -left-4 top-24 hidden lg:flex items-center gap-2 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-full px-4 py-2 backdrop-blur-sm"
      >
        <AlertTriangle size={14} className="text-[var(--accent-red)]" />
        <span className="text-[var(--accent-red)] text-xs font-[var(--font-space-mono)]">Bid rigging detected</span>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 2.3, duration: 0.6 }}
        className="absolute -right-4 top-36 hidden lg:flex items-center gap-2 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-full px-4 py-2 backdrop-blur-sm"
      >
        <CheckCircle2 size={14} className="text-[var(--accent-green)]" />
        <span className="text-[var(--accent-green)] text-xs font-[var(--font-space-mono)]">ML confidence 94.2%</span>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2.6, duration: 0.6 }}
        className="absolute -bottom-4 left-1/3 hidden lg:flex items-center gap-2 bg-[var(--accent-yellow)]/10 border border-[var(--accent-yellow)]/30 rounded-full px-4 py-2 backdrop-blur-sm"
      >
        <Network size={14} className="text-[var(--accent-yellow)]" />
        <span className="text-[var(--accent-yellow)] text-xs font-[var(--font-space-mono)]">Shell network mapped</span>
      </motion.div>
    </div>
  );
}

function NetworkGraphMockup() {
  const nodes = [
    { cx: 200, cy: 120, r: 18, color: "#e53e5c", label: "VENDOR A" },
    { cx: 350, cy: 80, r: 14, color: "#d49a00", label: "SHELL CO" },
    { cx: 450, cy: 180, r: 16, color: "#e53e5c", label: "VENDOR B" },
    { cx: 130, cy: 240, r: 12, color: "#3570e8", label: "MINISTER" },
    { cx: 300, cy: 220, r: 15, color: "#d49a00", label: "HOLDING" },
    { cx: 500, cy: 290, r: 11, color: "#00b876", label: "CLEAN" },
    { cx: 80, cy: 140, r: 10, color: "#00b876", label: "CLEAN" },
    { cx: 420, cy: 320, r: 13, color: "#e53e5c", label: "CARTEL" },
  ];
  const edges = [
    [0, 1], [1, 2], [0, 3], [0, 4], [4, 2], [2, 5], [3, 4], [4, 7], [6, 0], [5, 7],
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8 }}
      className="relative bg-[var(--surface)]/60 border border-[var(--border)] rounded-2xl overflow-hidden"
    >
      <div className="absolute top-3 left-4 flex items-center gap-2">
        <Network size={14} className="text-[var(--accent-blue)]" />
        <span className="text-[10px] text-[var(--muted)] font-[var(--font-space-mono)] uppercase tracking-wider">
          Entity Relationship Graph
        </span>
      </div>
      <svg viewBox="0 0 580 380" className="w-full h-auto" style={{ minHeight: 300 }}>
        <defs>
          <filter id="glow-filter">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {/* Edges */}
        {edges.map(([a, b], i) => (
          <motion.line
            key={`e-${i}`}
            x1={nodes[a].cx}
            y1={nodes[a].cy}
            x2={nodes[b].cx}
            y2={nodes[b].cy}
            stroke="rgba(107,115,148,0.3)"
            strokeWidth="1.5"
            initial={{ pathLength: 0, opacity: 0 }}
            whileInView={{ pathLength: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 + i * 0.06, duration: 0.5 }}
          />
        ))}
        {/* Nodes */}
        {nodes.map((n, i) => (
          <motion.g key={`n-${i}`}>
            <motion.circle
              cx={n.cx}
              cy={n.cy}
              r={n.r + 6}
              fill="none"
              stroke={n.color}
              strokeWidth="1"
              opacity="0.2"
              initial={{ scale: 0, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 0.2 }}
              viewport={{ once: true }}
              transition={{ delay: 0.6 + i * 0.08, duration: 0.4 }}
            />
            <motion.circle
              cx={n.cx}
              cy={n.cy}
              r={n.r}
              fill={n.color}
              opacity="0.85"
              initial={{ scale: 0 }}
              whileInView={{ scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.6 + i * 0.08, duration: 0.4, type: "spring" }}
              filter="url(#glow-filter)"
            />
            <motion.text
              x={n.cx}
              y={n.cy + n.r + 14}
              textAnchor="middle"
              fill="#6b7394"
              fontSize="8"
              fontFamily="monospace"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.9 + i * 0.05 }}
            >
              {n.label}
            </motion.text>
          </motion.g>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-3 right-4 flex items-center gap-3">
        {[
          { color: "#e53e5c", label: "Cartel" },
          { color: "#d49a00", label: "Shell" },
          { color: "#3570e8", label: "Political" },
          { color: "#00b876", label: "Clean" },
        ].map((l, i) => (
          <div key={i} className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ background: l.color }} />
            <span className="text-[9px] text-[var(--muted)] font-[var(--font-space-mono)]">{l.label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function BidChartMockup() {
  const bars = [
    { vendor: "INFRATECH", value: 85, isWinner: true },
    { vendor: "ROADTECH", value: 72, isWinner: false },
    { vendor: "ALPHA", value: 70, isWinner: false },
    { vendor: "NEXGEN", value: 68, isWinner: false },
    { vendor: "BUILDSMART", value: 65, isWinner: false },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8 }}
      className="bg-[var(--surface)]/60 border border-[var(--border)] rounded-2xl p-6 overflow-hidden"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 size={14} className="text-[var(--accent-blue)]" />
          <span className="text-[10px] text-[var(--muted)] font-[var(--font-space-mono)] uppercase tracking-wider">
            Bid Comparison · Tender NH-47-2024
          </span>
        </div>
        <span className="text-[var(--accent-red)] text-xs font-[var(--font-space-mono)] font-bold">
          Suspicion: 89
        </span>
      </div>

      <div className="space-y-3">
        {bars.map((bar, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="text-[10px] text-[var(--muted)] font-[var(--font-space-mono)] w-20 text-right truncate">
              {bar.vendor}
            </span>
            <div className="flex-1 h-7 rounded-lg bg-[var(--border)]/20 overflow-hidden relative">
              <motion.div
                className="h-full rounded-lg flex items-center justify-end pr-2"
                style={{ background: bar.isWinner ? "rgba(0,184,118,0.15)" : "rgba(229,62,92,0.1)" }}
                initial={{ width: 0 }}
                whileInView={{ width: `${bar.value}%` }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 + i * 0.1, duration: 0.8, ease: "easeOut" }}
              >
                <span
                  className="text-[10px] font-[var(--font-space-mono)] font-bold"
                  style={{ color: bar.isWinner ? "var(--accent-green)" : "var(--accent-red)", opacity: bar.isWinner ? 1 : 0.7 }}
                >
                  ₹{(bar.value * 3.2).toFixed(0)}Cr
                </span>
              </motion.div>
            </div>
            {bar.isWinner && (
              <motion.span
                initial={{ opacity: 0, scale: 0 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 1.2 }}
                className="text-[8px] bg-[var(--accent-green)]/10 text-[var(--accent-green)] border border-[var(--accent-green)]/30 px-1.5 py-0.5 rounded font-[var(--font-space-mono)]"
              >
                WINNER
              </motion.span>
            )}
          </div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1.4 }}
        className="mt-4 pt-3 border-t border-[var(--border)]/30 flex items-center gap-2"
      >
        <AlertTriangle size={12} className="text-[var(--accent-red)]" />
        <span className="text-[10px] text-[var(--accent-red)] font-[var(--font-space-mono)]">
          Price clustering detected — 0.5% bid spread across 4 vendors
        </span>
      </motion.div>
    </motion.div>
  );
}

function TimelineMockup() {
  const events = [
    { time: "2h ago", color: "#e53e5c", text: "Bid rigging flagged — NH-47 tender" },
    { time: "5h ago", color: "#d49a00", text: "Shell company link discovered" },
    { time: "1d ago", color: "#3570e8", text: "Electoral bond correlation detected" },
    { time: "2d ago", color: "#e53e5c", text: "Cartel rotation pattern identified" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.7 }}
      className="bg-[var(--surface)]/60 border border-[var(--border)] rounded-2xl p-6"
    >
      <div className="flex items-center gap-2 mb-5">
        <Activity size={14} className="text-[var(--accent-green)]" />
        <span className="text-[10px] text-[var(--muted)] font-[var(--font-space-mono)] uppercase tracking-wider">
          Live Event Feed
        </span>
        <div className="w-2 h-2 rounded-full bg-[var(--accent-green)] pulse-live ml-auto" />
      </div>
      <div className="space-y-0 relative">
        <div className="absolute left-[15px] top-2 bottom-2 w-px bg-[var(--border)]/40" />
        {events.map((ev, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 + i * 0.12 }}
            className="flex items-center gap-3 py-2.5 relative"
          >
            <div
              className="w-[30px] h-[30px] rounded-full flex items-center justify-center flex-shrink-0 z-10"
              style={{
                background: `${ev.color}15`,
                border: `1px solid ${ev.color}40`,
              }}
            >
              <div className="w-2 h-2 rounded-full" style={{ background: ev.color }} />
            </div>
            <div className="flex-1">
              <p className="text-xs text-[var(--text)] font-[var(--font-syne)]">{ev.text}</p>
              <p className="text-[10px] text-[var(--muted)] opacity-50 font-[var(--font-space-mono)]">{ev.time}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN PAGE COMPONENT
   ═══════════════════════════════════════════════════════ */

export default function HomePage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 150]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  return (
    <div className="min-h-screen overflow-x-hidden">
      {/* ═══ NAVIGATION BAR ═══ */}
      <nav className="fixed top-0 left-0 right-0 z-50 header-blur border-b border-[var(--border)]/50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg viewBox="0 0 40 40" className="w-9 h-9">
              <defs>
                <linearGradient id="nav-logo" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00b876" />
                  <stop offset="100%" stopColor="#3570e8" />
                </linearGradient>
              </defs>
              <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="url(#nav-logo)" opacity="0.9" />
              <text x="20" y="24" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">S</text>
            </svg>
            <span className="font-[var(--font-syne)] text-xl font-extrabold tracking-wider text-[var(--text)]">
              STREAM
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-[var(--muted)] hover:text-[var(--text)] text-sm font-[var(--font-syne)] transition-colors">Features</a>
            <a href="#dashboard-preview" className="text-[var(--muted)] hover:text-[var(--text)] text-sm font-[var(--font-syne)] transition-colors">Dashboard</a>
            <a href="#how-it-works" className="text-[var(--muted)] hover:text-[var(--text)] text-sm font-[var(--font-syne)] transition-colors">How it Works</a>
            <a href="#capabilities" className="text-[var(--muted)] hover:text-[var(--text)] text-sm font-[var(--font-syne)] transition-colors">Capabilities</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="px-4 py-2 text-sm font-[var(--font-syne)] font-semibold text-[var(--muted)] hover:text-[var(--text)] transition-colors">
              Sign In
            </Link>
            <Link href="/signup" className="px-5 py-2.5 text-sm font-[var(--font-syne)] font-bold bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 text-[var(--accent-green)] rounded-xl hover:bg-[var(--accent-green)]/20 hover:border-[var(--accent-green)]/50 transition-all">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* ═══ HERO ═══ */}
      <section ref={heroRef} className="relative pt-28 pb-8 md:pt-40 md:pb-16 px-6 overflow-hidden min-h-screen flex flex-col justify-center">
        {/* Animated concentric rings */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute border rounded-full"
              style={{
                borderColor: i % 2 === 0 ? "rgba(0,184,118,0.12)" : "rgba(53,112,232,0.12)",
                width: 250 + i * 140,
                height: 250 + i * 140,
                top: "40%",
                left: "50%",
                transform: "translate(-50%, -50%)",
              }}
              animate={{ rotate: i % 2 === 0 ? 360 : -360 }}
              transition={{ duration: 40 + i * 8, repeat: Infinity, ease: "linear" }}
            />
          ))}
          {/* Floating particles */}
          {[...Array(15)].map((_, i) => (
            <motion.div
              key={`p-${i}`}
              className="absolute w-1 h-1 rounded-full"
              style={{ left: `${5 + (i * 7) % 90}%`, top: `${10 + (i * 11) % 80}%`, background: "rgba(0,184,118,0.25)" }}
              animate={{ y: [0, -40 - Math.random() * 60, 0], opacity: [0.2, 0.6, 0.2] }}
              transition={{ duration: 5 + Math.random() * 4, repeat: Infinity, delay: i * 0.4 }}
            />
          ))}
        </div>

        <motion.div style={{ y: heroY, opacity: heroOpacity }} className="max-w-6xl mx-auto text-center relative z-10">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--accent-green)]/5 border border-[var(--accent-green)]/20 rounded-full mb-8"
          >
            <div className="w-2 h-2 rounded-full bg-[var(--accent-green)] pulse-live" />
            <span className="text-[var(--accent-green)] text-xs font-[var(--font-space-mono)] uppercase tracking-wider">
              AI-Powered Anti-Corruption Engine
            </span>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.1 }}
            className="font-[var(--font-syne)] text-5xl md:text-7xl lg:text-8xl font-extrabold text-[var(--text)] leading-[0.95] mb-6"
          >
            <span className="gradient-text">STREAM</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25 }}
            className="font-[var(--font-syne)] text-lg md:text-xl text-[var(--muted)] max-w-2xl mx-auto mb-4 font-medium tracking-wide"
          >
            Suspicious Transaction Risk Engine for Anomaly Monitoring
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.35 }}
            className="text-[var(--muted)] opacity-70 text-sm md:text-base max-w-3xl mx-auto mb-10 leading-relaxed"
          >
            Detect bid-rigging, map shell-company networks, flag cartel behavior, and
            surface politically connected vendors — all in real time, while protecting
            due process and minimizing false positives.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Link
              href="/signup"
              className="group flex items-center gap-2 px-8 py-4 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 text-[var(--accent-green)] rounded-2xl font-[var(--font-syne)] font-bold text-base hover:bg-[var(--accent-green)]/20 hover:border-[var(--accent-green)]/50 transition-all"
            >
              <Shield size={18} />
              Create Account
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/login"
              className="flex items-center gap-2 px-8 py-4 bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] rounded-2xl font-[var(--font-syne)] font-bold text-base hover:border-[var(--accent-blue)]/30 transition-all"
            >
              <Lock size={18} />
              Sign In to Platform
            </Link>
          </motion.div>

          {/* Dashboard preview image */}
          <DashboardMockup />

          {/* Scroll indicator */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3.0 }} className="mt-12">
            <a href="#features" className="inline-flex flex-col items-center gap-1 text-[var(--muted)] opacity-40 hover:opacity-100 transition-opacity">
              <span className="text-[10px] font-[var(--font-space-mono)] uppercase tracking-widest">Explore features</span>
              <motion.div animate={{ y: [0, 6, 0] }} transition={{ duration: 2, repeat: Infinity }}>
                <ChevronDown size={16} />
              </motion.div>
            </a>
          </motion.div>
        </motion.div>
      </section>

      {/* ═══ STATS BAR ═══ */}
      <section className="border-y border-[var(--border)] bg-[var(--surface)]/30">
        <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: "47", label: "Active Flags", color: "var(--accent-red)", icon: <FileWarning size={16} /> },
            { value: "₹2,840Cr", label: "At-Risk Value", color: "var(--accent-yellow)", icon: <TrendingUp size={16} /> },
            { value: "1,247", label: "Vendors Tracked", color: "var(--accent-blue)", icon: <Users size={16} /> },
            { value: "94.2%", label: "False Positive Control", color: "var(--accent-green)", icon: <Target size={16} /> },
          ].map((stat, i) => (
            <motion.div key={i} {...stagger} transition={{ delay: i * 0.1, duration: 0.5 }} className="text-center">
              <div className="flex justify-center mb-2 opacity-40" style={{ color: stat.color }}>{stat.icon}</div>
              <p className="font-[var(--font-space-mono)] text-3xl md:text-4xl font-bold" style={{ color: stat.color }}>{stat.value}</p>
              <p className="text-[var(--muted)] text-xs font-[var(--font-syne)] font-semibold uppercase tracking-wider mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ═══ CORE DETECTION MODULES ═══ */}
      <section id="features" className="py-24 md:py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div {...fadeUp} className="text-center mb-16">
            <span className="text-[var(--accent-green)] text-[10px] font-[var(--font-space-mono)] uppercase tracking-[0.3em]">Detection Modules</span>
            <h2 className="font-[var(--font-syne)] text-3xl md:text-5xl font-extrabold text-[var(--text)] mt-3 mb-4">
              Procurement Fraud + Conflict of Interest + Cartel Detection
            </h2>
            <p className="text-[var(--muted)] max-w-2xl mx-auto">
              Four specialized AI engines working in concert to surface corruption patterns across public procurement data — without becoming an automated accusation machine.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                icon: <AlertTriangle size={24} />,
                title: "Bid Rigging Detection",
                subtitle: "Pattern Recognition Engine",
                description: "Identifies cover bidding, phantom bids, and price clustering using statistical anomaly detection. Analyzes bid timing, price spreads, and vendor rotation patterns.",
                color: "#e53e5c",
                stats: "12 active flags",
              },
              {
                icon: <Network size={24} />,
                title: "Shell Company Networks",
                subtitle: "Corporate Graph Analysis",
                description: "Maps corporate ownership using MCA filings, shared directors, registered addresses, and common auditors. Traces beneficial ownership through multi-layered entities.",
                color: "#d49a00",
                stats: "18 entities tracked",
              },
              {
                icon: <Fingerprint size={24} />,
                title: "Political Connection Flags",
                subtitle: "Electoral Bond Intelligence",
                description: "Correlates electoral bond disclosures, party donations, and government contracts. Maps vendor–politician relationships using temporal proximity analysis.",
                color: "#3570e8",
                stats: "9 correlations",
              },
              {
                icon: <Target size={24} />,
                title: "Cartel Behavior Detection",
                subtitle: "Market Collusion Engine",
                description: "Detects market-sharing, bid rotation, and price-fixing cartels. Uses game theory models to identify coordinated bidding deviating from competitive expectations.",
                color: "#e53e5c",
                stats: "8 groups",
              },
            ].map((mod, i) => (
              <motion.div
                key={i}
                {...stagger}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                className="group bg-[var(--surface)]/80 border border-[var(--border)] rounded-2xl p-7 hover:shadow-lg transition-all"
                style={{ ["--mod-color" as string]: mod.color }}
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform"
                  style={{ background: `${mod.color}15`, border: `1px solid ${mod.color}30`, color: mod.color }}
                >
                  {mod.icon}
                </div>
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="font-[var(--font-syne)] text-xl font-bold text-[var(--text)] group-hover:text-[var(--accent-green)] transition-colors">{mod.title}</h3>
                  <span
                    className="text-[10px] font-[var(--font-space-mono)] px-2 py-0.5 rounded"
                    style={{ color: mod.color, background: `${mod.color}15`, border: `1px solid ${mod.color}30` }}
                  >
                    {mod.stats}
                  </span>
                </div>
                <p className="text-xs text-[var(--muted)] opacity-60 font-[var(--font-space-mono)] uppercase tracking-wider mb-3">{mod.subtitle}</p>
                <p className="text-[var(--muted)] text-sm leading-relaxed">{mod.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ DASHBOARD PREVIEW — NETWORK + BID ═══ */}
      <section id="dashboard-preview" className="py-24 md:py-32 px-6 bg-[var(--surface)]/20 border-y border-[var(--border)]">
        <div className="max-w-6xl mx-auto">
          <motion.div {...fadeUp} className="text-center mb-14">
            <span className="text-[var(--accent-blue)] text-[10px] font-[var(--font-space-mono)] uppercase tracking-[0.3em]">Live Intelligence</span>
            <h2 className="font-[var(--font-syne)] text-3xl md:text-5xl font-extrabold text-[var(--text)] mt-3 mb-4">
              See the Dashboard in Action
            </h2>
            <p className="text-[var(--muted)] max-w-2xl mx-auto">
              Interactive network graphs, real-time bid analysis, and live event timelines — all surfacing anomalies as they happen.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <NetworkGraphMockup />
            <div className="space-y-6">
              <BidChartMockup />
              <TimelineMockup />
            </div>
          </div>

          {/* CTA under preview */}
          <motion.div {...fadeUp} className="text-center mt-12">
            <Link
              href="/signup"
              className="group inline-flex items-center gap-2 px-8 py-4 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 text-[var(--accent-green)] rounded-2xl font-[var(--font-syne)] font-bold text-base hover:bg-[var(--accent-green)]/20 hover:border-[var(--accent-green)]/50 transition-all"
            >
              <MousePointerClick size={18} />
              Try the Full Dashboard
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section id="how-it-works" className="py-24 md:py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div {...fadeUp} className="text-center mb-16">
            <span className="text-[var(--accent-blue)] text-[10px] font-[var(--font-space-mono)] uppercase tracking-[0.3em]">Architecture</span>
            <h2 className="font-[var(--font-syne)] text-3xl md:text-5xl font-extrabold text-[var(--text)] mt-3 mb-4">How STREAM Works</h2>
            <p className="text-[var(--muted)] max-w-2xl mx-auto">Three intelligence layers operating on public data, behavioral signals, and network topology.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Connecting line */}
            <div className="hidden md:block absolute top-28 left-[16.5%] right-[16.5%] h-px" style={{ background: "linear-gradient(to right, rgba(0,184,118,0.3), rgba(53,112,232,0.3), rgba(212,154,0,0.3))" }} />

            {[
              { step: "01", icon: <Globe size={28} />, title: "Public Ledger Analysis", description: "Ingests OCDS procurement data, MCA company filings, electoral bond disclosures, and GeM portal records. Standardizes 100K+ records across fiscal years.", color: "#00b876" },
              { step: "02", icon: <Network size={28} />, title: "Network Intelligence", description: "Builds corporate relationship graphs mapping shared directors, co-bidders, donation chains, and address clustering. Force-directed visualization reveals hidden networks.", color: "#3570e8" },
              { step: "03", icon: <Brain size={28} />, title: "Behavioral Anomaly Detection", description: "Isolation Forest ML + rule-based scoring engine identifies statistical outliers in bidding patterns, contract values, and timeline anomalies with confidence scores.", color: "#d49a00" },
            ].map((step, i) => (
              <motion.div key={i} {...stagger} transition={{ delay: i * 0.15, duration: 0.6 }} className="relative">
                <div className="text-[80px] font-[var(--font-space-mono)] font-bold absolute -top-6 -left-2 select-none" style={{ color: step.color, opacity: 0.05 }}>{step.step}</div>
                <div className="relative bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-7 hover:border-[var(--border)]/80 transition-all">
                  <div
                    className="w-14 h-14 rounded-xl flex items-center justify-center mb-5"
                    style={{ background: `${step.color}15`, border: `1px solid ${step.color}30`, color: step.color }}
                  >
                    {step.icon}
                  </div>
                  <h3 className="font-[var(--font-syne)] text-lg font-bold text-[var(--text)] mb-3">{step.title}</h3>
                  <p className="text-[var(--muted)] text-sm leading-relaxed">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ DUE PROCESS + FALSE POSITIVE ═══ */}
      <section className="py-24 md:py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div {...fadeUp} className="bg-[var(--surface)]/80 border border-[var(--accent-yellow)]/20 rounded-3xl p-8 md:p-12 relative overflow-hidden">
            {/* Background accent */}
            <div className="absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl pointer-events-none" style={{ background: "rgba(212,154,0,0.06)" }} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center relative z-10">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-yellow)]/10 border border-[var(--accent-yellow)]/20 rounded-full mb-6">
                  <Scale size={14} className="text-[var(--accent-yellow)]" />
                  <span className="text-[var(--accent-yellow)] text-[10px] font-[var(--font-space-mono)] uppercase tracking-wider">Due Process First</span>
                </div>
                <h2 className="font-[var(--font-syne)] text-2xl md:text-4xl font-extrabold text-[var(--text)] mb-4">
                  The Hard Part: Avoiding False Positives That Destroy Reputations
                </h2>
                <p className="text-[var(--muted)] leading-relaxed mb-6">
                  Every flag in STREAM is a probabilistic risk indicator — not an accusation. Confidence scores reflect pattern similarity, not guilt. Our engine detects corruption patterns without becoming an automated accusation machine.
                </p>
                <p className="text-[var(--muted)] opacity-70 text-sm leading-relaxed">
                  Public financial data is analyzed without violating due process. Each alert requires human review and independent investigation before any action. Risk thresholds are calibrated to minimize reputational damage.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  { icon: <CheckCircle2 size={18} />, title: "Probabilistic Scoring", desc: "Every flag includes confidence percentages and evidence trails — never binary guilt/innocence" },
                  { icon: <Eye size={18} />, title: "Human-in-the-Loop", desc: "Role-gated review workflow — Analyst, Auditor, and Approver tiers with audit logging" },
                  { icon: <Shield size={18} />, title: "Due Process Language", desc: "\"Pattern Detected\" not \"Fraud Confirmed\". Language preserves presumption of innocence" },
                  { icon: <BarChart3 size={18} />, title: "94.2% False Positive Control", desc: "ML + rule engine calibrated to suppress spurious flags while catching genuine anomalies" },
                ].map((item, i) => (
                  <motion.div key={i} {...stagger} transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }} className="flex items-start gap-4 p-4 bg-[var(--bg)]/50 rounded-xl border border-[var(--border)] hover:border-[var(--accent-green)]/20 transition-all">
                    <div className="text-[var(--accent-green)] mt-0.5">{item.icon}</div>
                    <div>
                      <h4 className="font-[var(--font-syne)] font-bold text-[var(--text)] text-sm mb-1">{item.title}</h4>
                      <p className="text-[var(--muted)] text-xs leading-relaxed">{item.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ═══ CAPABILITIES ═══ */}
      <section id="capabilities" className="py-24 md:py-32 px-6 bg-[var(--surface)]/20 border-y border-[var(--border)]">
        <div className="max-w-6xl mx-auto">
          <motion.div {...fadeUp} className="text-center mb-16">
            <span className="text-[var(--accent-green)] text-[10px] font-[var(--font-space-mono)] uppercase tracking-[0.3em]">Platform Capabilities</span>
            <h2 className="font-[var(--font-syne)] text-3xl md:text-5xl font-extrabold text-[var(--text)] mt-3 mb-4">Intelligence Dashboard</h2>
            <p className="text-[var(--muted)] max-w-2xl mx-auto">Real-time monitoring, network visualization, bid analysis, and AI-assisted investigation.</p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { icon: <AlertTriangle size={20} />, title: "Real-Time Fraud Alerts", desc: "Live anomaly detection across all procurement tenders with risk scoring and confidence percentages" },
              { icon: <Network size={20} />, title: "Network Graph Visualization", desc: "Interactive force-directed graphs mapping vendor relationships, ownership chains, and hidden connections" },
              { icon: <BarChart3 size={20} />, title: "Bid Pattern Analysis", desc: "Statistical analysis of bid submissions with cover-bid detection, price clustering, and spread analysis" },
              { icon: <Building2 size={20} />, title: "Vendor Intelligence Profiles", desc: "Comprehensive risk profiles with sub-scores, connection maps, and activity timeline tracking" },
              { icon: <Brain size={20} />, title: "AI Investigation Assistant", desc: "Natural language query interface for deep-diving into procurement patterns and vendor histories" },
              { icon: <Zap size={20} />, title: "ML Pipeline Integration", desc: "Isolation Forest + rule-based scoring with batch processing across fiscal years 2016–2021" },
            ].map((cap, i) => (
              <motion.div key={i} {...stagger} transition={{ delay: i * 0.08, duration: 0.5 }} className="flex items-start gap-4 bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 hover:border-[var(--accent-green)]/20 hover:shadow-lg transition-all group">
                <div className="text-[var(--accent-green)] mt-0.5 flex-shrink-0 group-hover:scale-110 transition-transform">{cap.icon}</div>
                <div>
                  <h4 className="font-[var(--font-syne)] font-bold text-[var(--text)] text-sm mb-1">{cap.title}</h4>
                  <p className="text-[var(--muted)] text-xs leading-relaxed">{cap.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ DATA SOURCES ═══ */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div {...fadeUp}>
            <span className="text-[var(--muted)] opacity-60 text-[10px] font-[var(--font-space-mono)] uppercase tracking-[0.3em]">Operating On</span>
            <h3 className="font-[var(--font-syne)] text-xl md:text-2xl font-bold text-[var(--text)] mt-3 mb-8">
              Public Ledgers · Network Analysis · Behavioral Anomaly Detection
            </h3>
            <div className="flex flex-wrap justify-center gap-3">
              {["OCDS Procurement Data", "MCA Company Filings", "Electoral Bond Disclosures", "GeM Portal Records", "Income Tax PAN Links"].map((source, i) => (
                <motion.span key={i} {...stagger} transition={{ delay: i * 0.08 }} className="text-xs font-[var(--font-space-mono)] text-[var(--muted)] bg-[var(--surface)] border border-[var(--border)] px-4 py-2.5 rounded-lg hover:border-[var(--accent-green)]/20 transition-all cursor-default">
                  {source}
                </motion.span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ═══ FINAL CTA ═══ */}
      <section className="py-24 md:py-32 px-6 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full blur-3xl" style={{ background: "rgba(0,184,118,0.08)" }} />
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div {...fadeUp}>
            <motion.div
              initial={{ scale: 0 }}
              whileInView={{ scale: 1 }}
              viewport={{ once: true }}
              transition={{ type: "spring", delay: 0.2 }}
              className="w-20 h-20 mx-auto mb-8 rounded-2xl bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 flex items-center justify-center"
            >
              <Shield size={36} className="text-[var(--accent-green)]" />
            </motion.div>
            <h2 className="font-[var(--font-syne)] text-3xl md:text-5xl font-extrabold text-[var(--text)] mb-4">
              Start Detecting Corruption Patterns
            </h2>
            <p className="text-[var(--muted)] max-w-xl mx-auto mb-10">
              Access the STREAM intelligence dashboard. Analyze procurement data, map vendor networks, and surface anomalies — all while preserving due process.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/signup" className="group flex items-center gap-2 px-10 py-5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 text-[var(--accent-green)] rounded-2xl font-[var(--font-syne)] font-bold text-lg hover:bg-[var(--accent-green)]/20 hover:border-[var(--accent-green)]/50 transition-all">
                <Shield size={20} />
                Create Account
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link href="/login" className="flex items-center gap-2 px-10 py-5 bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] rounded-2xl font-[var(--font-syne)] font-bold text-lg hover:border-[var(--accent-blue)]/30 transition-all">
                <Lock size={20} />
                Sign In
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-[var(--border)] bg-[var(--surface)]/30 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <svg viewBox="0 0 40 40" className="w-7 h-7">
              <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="url(#nav-logo)" opacity="0.6" />
              <text x="20" y="24" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">S</text>
            </svg>
            <span className="font-[var(--font-syne)] text-sm font-bold text-[var(--muted)]">STREAM</span>
            <span className="text-[var(--muted)] opacity-40 text-xs font-[var(--font-space-mono)]">· Anti-Corruption Intelligence Engine</span>
          </div>
          <p className="text-[var(--muted)] opacity-40 text-xs font-[var(--font-space-mono)] text-center">
            AES-256 Encrypted · Session Monitored · Audit Logged · AIA-26 Hackathon — Anna University
          </p>
        </div>
      </footer>
    </div>
  );
}

