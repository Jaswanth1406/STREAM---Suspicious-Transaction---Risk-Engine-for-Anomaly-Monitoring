"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Clock,
  Users,
  Banknote,
  Building2,
  FileText,
  Tag,
  TrendingUp,
  Brain,
  Flag,
  ChevronRight,
} from "lucide-react";
import { api } from "@/lib/api";
import type { BidAnalysisTender } from "@/lib/types";
import Link from "next/link";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, Cell, CartesianGrid,
} from "recharts";

function getRiskColor(score: number): string {
  if (score >= 60) return "#e53e5c";
  if (score >= 30) return "#d49a00";
  return "#00b876";
}

function getRiskLabel(score: number): string {
  if (score >= 60) return "High Risk";
  if (score >= 30) return "Medium Risk";
  return "Low Risk";
}

function formatCurrency(value: number): string {
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(2)}Cr`;
  if (value >= 1e5) return `₹${(value / 1e5).toFixed(2)}L`;
  return `₹${value.toLocaleString()}`;
}

interface FlagInfo {
  key: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  severity: "critical" | "high" | "medium" | "low";
}

const FLAG_DEFINITIONS: FlagInfo[] = [
  { key: "flag_single_bidder", label: "Single Bidder", description: "Only one tender was submitted — potential bid rigging or entry barrier", icon: <Users size={14} />, severity: "critical" },
  { key: "flag_zero_bidders", label: "Zero Bidders", description: "No bidders recorded — possible data manipulation or cancelled tender", icon: <Users size={14} />, severity: "critical" },
  { key: "flag_short_window", label: "Short Window", description: "Tender period was unusually short, limiting fair competition", icon: <Clock size={14} />, severity: "high" },
  { key: "flag_non_open", label: "Non-Open Procurement", description: "Procurement method was not open tender — reduced transparency", icon: <FileText size={14} />, severity: "high" },
  { key: "flag_high_value", label: "High Value", description: "Contract value is above the 95th percentile for this category", icon: <Banknote size={14} />, severity: "medium" },
  { key: "flag_buyer_concentration", label: "Buyer Concentration", description: "This buyer dominates >70% of contracts in this category", icon: <Building2 size={14} />, severity: "high" },
  { key: "flag_round_amount", label: "Round Amount", description: "Contract amount is suspiciously round — possible fixed pricing", icon: <Tag size={14} />, severity: "medium" },
  { key: "ml_anomaly_flag", label: "ML Anomaly", description: "Machine learning model flagged this as a statistical outlier", icon: <Brain size={14} />, severity: "high" },
];

export default function BidDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [tender, setTender] = useState<BidAnalysisTender | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    const decodedId = decodeURIComponent(id);
    api.bidAnalysis({ search: decodedId, page_size: 50, page: 1 })
      .then((res) => {
        const match = res.tenders.find(
          (t: BidAnalysisTender) => t.ocid === decodedId || t.tender_id === decodedId
        ) || res.tenders[0];
        if (match) {
          setTender(match);
        } else {
          setError("Tender not found");
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted text-sm font-[var(--font-syne)]">Loading tender analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !tender) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <AlertTriangle size={48} className="mx-auto text-accent-red/40 mb-4" />
          <p className="text-text font-[var(--font-syne)] font-bold mb-2">Tender Not Found</p>
          <p className="text-muted text-sm mb-4">{error || "Could not load the requested tender."}</p>
          <button onClick={() => router.back()} className="px-4 py-2 bg-accent-green/10 text-accent-green border border-accent-green/30 rounded-lg text-sm font-[var(--font-syne)] hover:bg-accent-green/20 transition-all">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const riskColor = getRiskColor(tender.risk_score);
  const riskLabel = getRiskLabel(tender.risk_score);
  const tenderTitle = tender.title || tender.tender_title || "Untitled Tender";

  // Extract flags
  const flagSource = tender.flags ?? tender;
  const activeFlags = FLAG_DEFINITIONS.filter((f) => {
    const val = (flagSource as unknown as Record<string, unknown>)[f.key];
    return val === 1 || val === true;
  });
  const inactiveFlags = FLAG_DEFINITIONS.filter((f) => {
    const val = (flagSource as unknown as Record<string, unknown>)[f.key];
    return val !== 1 && val !== true;
  });

  // Radar chart data for risk profile
  const radarData = FLAG_DEFINITIONS.map((f) => {
    const val = (flagSource as unknown as Record<string, unknown>)[f.key];
    return {
      flag: f.label,
      value: val === 1 || val === true ? 100 : 0,
    };
  });

  // Risk factors bar chart
  const riskFactors = [
    { name: "Risk Score", value: tender.risk_score, color: getRiskColor(tender.risk_score) },
    { name: "Anomaly", value: Math.round((tender.anomaly_score || 0) * 100), color: "#6366f1" },
    { name: "Suspicion", value: Math.round((tender.suspicion_probability || 0) * 100), color: tender.predicted_suspicious ? "#e53e5c" : "#00b876" },
  ];

  // Risk explanation points
  const riskPoints = (tender.risk_explanation || "").split(";").map((s) => s.trim()).filter(Boolean);

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted">
        <button onClick={() => router.back()} className="flex items-center gap-1 hover:text-text transition-colors">
          <ArrowLeft size={16} />
          <span className="font-[var(--font-syne)]">Back</span>
        </button>
        <ChevronRight size={14} />
        <Link href="/dashboard/bids" className="hover:text-text transition-colors font-[var(--font-syne)]">Bid Analysis</Link>
        <ChevronRight size={14} />
        <span className="text-text font-[var(--font-syne)]">{tender.tender_id}</span>
      </div>

      {/* Header Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-surface border border-border rounded-xl p-6"
      >
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <span className="text-[10px] bg-surface2 border border-border px-2 py-1 rounded font-[var(--font-space-mono)] text-muted">
                {tender.tender_id}
              </span>
              <span className="text-[10px] bg-surface2 border border-border px-2 py-1 rounded font-[var(--font-space-mono)] text-muted">
                {tender.ocid}
              </span>
              {tender.procurement_method && (
                <span className="text-[10px] bg-accent-blue/10 text-accent-blue border border-accent-blue/30 px-2 py-1 rounded font-[var(--font-space-mono)]">
                  {tender.procurement_method}
                </span>
              )}
            </div>
            <h1 className="font-[var(--font-syne)] text-xl lg:text-2xl font-bold text-text mb-2">
              {tenderTitle}
            </h1>
            <div className="flex items-center gap-4 text-sm text-muted flex-wrap">
              <span className="flex items-center gap-1"><Building2 size={14} /> {tender.buyer_name}</span>
              {tender.category && <span className="flex items-center gap-1"><Tag size={14} /> {tender.category}</span>}
            </div>
          </div>

          {/* Risk Score Circle */}
          <div className="flex-shrink-0 text-center">
            <div className="relative w-28 h-28 mx-auto">
              <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                <circle cx="50" cy="50" r="42" stroke="currentColor" strokeWidth="6" fill="none" className="text-surface2" />
                <motion.circle
                  cx="50" cy="50" r="42"
                  stroke={riskColor}
                  strokeWidth="6"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 42}`}
                  initial={{ strokeDashoffset: 2 * Math.PI * 42 }}
                  animate={{ strokeDashoffset: 2 * Math.PI * 42 * (1 - tender.risk_score / 100) }}
                  transition={{ duration: 1.2, ease: "easeOut" }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-[var(--font-space-mono)] text-3xl font-bold" style={{ color: riskColor }}>
                  {Math.round(tender.risk_score)}
                </span>
                <span className="text-[9px] text-muted uppercase tracking-wider">Risk</span>
              </div>
            </div>
            <p className="text-sm font-[var(--font-syne)] font-bold mt-2" style={{ color: riskColor }}>
              {riskLabel}
            </p>
          </div>
        </div>
      </motion.div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <KpiCard
          icon={<Banknote size={16} className="text-accent-blue" />}
          label="Contract Value"
          value={formatCurrency(tender.amount)}
          delay={0}
        />
        <KpiCard
          icon={<Users size={16} className="text-accent-yellow" />}
          label="Bidders"
          value={String(tender.num_tenderers)}
          delay={1}
        />
        <KpiCard
          icon={<Clock size={16} className="text-muted" />}
          label="Duration"
          value={`${tender.duration_days}d`}
          delay={2}
        />
        <KpiCard
          icon={<Brain size={16} className="text-accent-blue" />}
          label="Anomaly Score"
          value={`${Math.round((tender.anomaly_score || 0) * 100)}%`}
          delay={3}
        />
        <KpiCard
          icon={tender.predicted_suspicious ? <ShieldAlert size={16} className="text-accent-red" /> : <ShieldCheck size={16} className="text-accent-green" />}
          label="ML Prediction"
          value={tender.predicted_suspicious ? `SUS ${Math.round(tender.suspicion_probability * 100)}%` : "CLEAN"}
          delay={4}
          highlight={tender.predicted_suspicious === 1}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Risk Explanation */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="xl:col-span-2 bg-surface border border-border rounded-xl p-5"
        >
          <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-4 flex items-center gap-2">
            <AlertTriangle size={16} className="text-accent-yellow" />
            Risk Analysis
          </h3>
          {riskPoints.length > 0 ? (
            <div className="space-y-3">
              {riskPoints.map((point, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.08 }}
                  className="flex items-start gap-3 p-3 bg-surface2/50 rounded-lg border border-border/50"
                >
                  <div className="w-6 h-6 rounded-full bg-accent-red/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-[10px] font-[var(--font-space-mono)] font-bold text-accent-red">{i + 1}</span>
                  </div>
                  <p className="text-sm text-muted leading-relaxed">{point}</p>
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="text-muted text-sm">No specific risk factors identified.</p>
          )}
        </motion.div>

        {/* Risk Scores Bar Chart */}
        {mounted && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-surface border border-border rounded-xl p-5"
          >
            <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-4 flex items-center gap-2">
              <TrendingUp size={16} className="text-accent-blue" />
              Score Breakdown
            </h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskFactors} layout="vertical" barSize={20}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d8dce8" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: "#6b7394", fontFamily: "monospace" }} />
                  <YAxis dataKey="name" type="category" width={70} tick={{ fontSize: 10, fill: "#6b7394", fontFamily: "monospace" }} />
                  <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #d8dce8", borderRadius: 8, fontSize: 12, fontFamily: "monospace", color: "#1a1f36" }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {riskFactors.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}
      </div>

      {/* Flags Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-surface border border-border rounded-xl p-5"
      >
        <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-4 flex items-center gap-2">
          <Flag size={16} className="text-accent-red" />
          Flag Analysis
          <span className="text-[10px] bg-accent-red/10 text-accent-red px-2 py-0.5 rounded-full font-[var(--font-space-mono)]">
            {activeFlags.length}/{FLAG_DEFINITIONS.length} triggered
          </span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {activeFlags.map((flag, i) => (
            <motion.div
              key={flag.key}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 + i * 0.05 }}
              className={`p-3 rounded-lg border-l-[3px] ${
                flag.severity === "critical" ? "border-l-accent-red bg-accent-red/5 border border-accent-red/20" :
                flag.severity === "high" ? "border-l-accent-yellow bg-accent-yellow/5 border border-accent-yellow/20" :
                "border-l-accent-blue bg-accent-blue/5 border border-accent-blue/20"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`${
                  flag.severity === "critical" ? "text-accent-red" :
                  flag.severity === "high" ? "text-accent-yellow" : "text-accent-blue"
                }`}>{flag.icon}</span>
                <span className="text-xs font-[var(--font-syne)] font-bold text-text">{flag.label}</span>
                <span className={`ml-auto text-[9px] font-[var(--font-space-mono)] font-bold uppercase px-1.5 py-0.5 rounded ${
                  flag.severity === "critical" ? "bg-accent-red/10 text-accent-red" :
                  flag.severity === "high" ? "bg-accent-yellow/10 text-accent-yellow" : "bg-accent-blue/10 text-accent-blue"
                }`}>
                  triggered
                </span>
              </div>
              <p className="text-[11px] text-muted leading-relaxed">{flag.description}</p>
            </motion.div>
          ))}
          {inactiveFlags.map((flag) => (
            <div key={flag.key} className="p-3 rounded-lg border border-border/50 bg-surface2/30 opacity-50">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-muted">{flag.icon}</span>
                <span className="text-xs font-[var(--font-syne)] font-bold text-muted">{flag.label}</span>
                <span className="ml-auto text-[9px] font-[var(--font-space-mono)] text-muted uppercase px-1.5 py-0.5 rounded bg-surface2">
                  clear
                </span>
              </div>
              <p className="text-[11px] text-muted/60 leading-relaxed">{flag.description}</p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Radar Chart + Summary */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {mounted && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-surface border border-border rounded-xl p-5"
          >
            <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-4">Risk Profile Radar</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#d8dce8" />
                  <PolarAngleAxis dataKey="flag" tick={{ fontSize: 9, fill: "#6b7394" }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9, fill: "#6b7394" }} />
                  <Radar
                    name="Flags"
                    dataKey="value"
                    stroke="#e53e5c"
                    fill="#e53e5c"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                  <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #d8dce8", borderRadius: 8, fontSize: 12, color: "#1a1f36" }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* Tender Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-surface border border-border rounded-xl p-5"
        >
          <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-4">Tender Summary</h3>
          <div className="space-y-3">
            <DetailRow label="Tender ID" value={tender.tender_id} />
            <DetailRow label="OCID" value={tender.ocid} />
            <DetailRow label="Title" value={tenderTitle} />
            <DetailRow label="Buyer" value={tender.buyer_name} />
            <DetailRow label="Category" value={tender.category || "—"} />
            <DetailRow label="Procurement Method" value={tender.procurement_method || "—"} />
            <DetailRow label="Contract Value" value={formatCurrency(tender.amount)} />
            <DetailRow label="Number of Bidders" value={String(tender.num_tenderers)} />
            <DetailRow label="Duration (Days)" value={String(tender.duration_days)} />
            <DetailRow label="Risk Tier" value={(tender.risk_tier || "").replace(/[🔴🟡🟢]\s*/g, "")} highlight />
            <DetailRow label="ML Suspicious" value={tender.predicted_suspicious ? "Yes" : "No"} highlight={tender.predicted_suspicious === 1} />
            <DetailRow label="Suspicion Probability" value={`${Math.round(tender.suspicion_probability * 100)}%`} />
          </div>
        </motion.div>
      </div>

      {/* Due Process Notice */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="bg-surface2/80 border border-border rounded-xl p-4 flex items-start gap-3"
      >
        <div className="w-8 h-8 rounded-full bg-accent-yellow/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <AlertTriangle size={16} className="text-accent-yellow" />
        </div>
        <div>
          <p className="text-sm">
            <span className="text-accent-yellow font-[var(--font-syne)] font-bold">Due Process Notice: </span>
            <span className="text-muted">
              All flags are probabilistic risk indicators based on statistical anomalies in public data.
              No flag constitutes proof of wrongdoing. This analysis requires human review and independent
              investigation before any action. Risk scores reflect pattern similarity, not guilt.
            </span>
          </p>
        </div>
      </motion.div>
    </div>
  );
}

function KpiCard({ icon, label, value, delay, highlight }: {
  icon: React.ReactNode; label: string; value: string; delay: number; highlight?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.08, duration: 0.4 }}
      className={`bg-surface border rounded-xl p-4 ${highlight ? 'border-accent-red/30 bg-accent-red/5' : 'border-border'}`}
    >
      <div className="flex items-center gap-2 mb-2">{icon}</div>
      <p className={`font-[var(--font-space-mono)] text-xl font-bold ${highlight ? 'text-accent-red' : 'text-text'}`}>{value}</p>
      <p className="text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] mt-1">{label}</p>
    </motion.div>
  );
}

function DetailRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border/30 last:border-0">
      <span className="text-xs text-muted font-[var(--font-syne)]">{label}</span>
      <span className={`text-sm font-[var(--font-space-mono)] ${highlight ? 'text-accent-red font-bold' : 'text-text'} text-right max-w-[60%] truncate`}>
        {value}
      </span>
    </div>
  );
}
