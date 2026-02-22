"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Building2,
  AlertTriangle,
  Link2,
  FileText,
  Download,
  Flag,
  ExternalLink,
} from "lucide-react";
import { api } from "@/lib/api";
import type { VendorProfile } from "@/lib/types";

function getScoreColor(score: number) {
  if (score >= 60) return "#e53e5c";
  if (score >= 30) return "#d49a00";
  return "#00b876";
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = getScoreColor(value);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[var(--text-secondary)]">{label}</span>
        <span style={{ color }} className="font-mono font-bold">
          {value}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--bg-tertiary)]">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8 }}
        />
      </div>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-[var(--bg-secondary)] rounded-lg p-3 text-center">
      <p className="text-lg font-bold font-mono text-[var(--text-primary)]">
        {value}
      </p>
      <p className="text-[10px] text-[var(--text-secondary)] uppercase tracking-wider">
        {label}
      </p>
    </div>
  );
}

export default function VendorPage() {
  const { cin } = useParams<{ cin: string }>();
  const router = useRouter();
  const [vendor, setVendor] = useState<VendorProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cin) return;
    setLoading(true);
    api
      .vendor(cin)
      .then(setVendor)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cin]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-[var(--accent-green)] border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !vendor) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4">
        <AlertTriangle className="w-12 h-12 text-[var(--accent-red)]" />
        <p className="text-[var(--text-secondary)]">
          {error ?? "Vendor not found"}
        </p>
        <button
          onClick={() => router.back()}
          className="text-sm text-[var(--accent-blue)] hover:underline"
        >
          Go back
        </button>
      </div>
    );
  }

  const risk = vendor.composite_risk_score ?? vendor.overall_risk_score ?? 0;
  const riskColor = getScoreColor(risk);
  const circumference = 2 * Math.PI * 54;
  const dashOffset = circumference - (risk / 100) * circumference;

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Back */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      {/* Company Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border-primary)] p-6"
      >
        <div className="flex flex-col md:flex-row items-start gap-6">
          {/* Risk Ring */}
          <div className="relative flex-shrink-0">
            <svg width="130" height="130" className="-rotate-90">
              <circle
                cx="65"
                cy="65"
                r="54"
                fill="none"
                stroke="var(--bg-tertiary)"
                strokeWidth="8"
              />
              <circle
                cx="65"
                cy="65"
                r="54"
                fill="none"
                stroke={riskColor}
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span
                className="text-2xl font-bold font-mono"
                style={{ color: riskColor }}
              >
                {risk}
              </span>
              <span className="text-[9px] uppercase tracking-widest text-[var(--text-secondary)]">
                Risk
              </span>
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <Building2 className="w-5 h-5 text-[var(--text-secondary)]" />
              <h1 className="text-xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-display)] truncate">
                {vendor.company_name}
              </h1>
            </div>
            <p className="text-xs text-[var(--text-secondary)] mb-4">
              CIN: {vendor.cin} &middot;{" "}
              {vendor.company_status ?? vendor.status ?? 'Unknown'}
              {vendor.state ? ` · ${vendor.state}` : ''}
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatBox label="Risk Score" value={Math.round(vendor.composite_risk_score ?? 0)} />
              <StatBox label="Risk Tier" value={vendor.risk_tier ?? "\u2014"} />
              <StatBox label="Connections" value={vendor.connections?.length ?? 0} />
              <StatBox label="Review" value={vendor.requires_human_review ? 'Required' : 'OK'} />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Sub-scores */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border-primary)] p-6"
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4 font-[family-name:var(--font-display)]">
          Risk Sub-Scores
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <ScoreBar
            label="Bid Pattern Risk"
            value={vendor.sub_scores?.bid_pattern ?? 0}
          />
          <ScoreBar
            label="Shell Company Risk"
            value={vendor.sub_scores?.shell_risk ?? 0}
          />
          <ScoreBar
            label="Political Connection"
            value={vendor.sub_scores?.political ?? 0}
          />
          <ScoreBar
            label="Financial Health"
            value={vendor.sub_scores?.financials ?? 0}
          />
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connections */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border-primary)] p-6"
        >
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2 font-[family-name:var(--font-display)]">
            <Link2 className="w-4 h-4" />
            Connections ({vendor.connections?.length ?? 0})
          </h2>
          {vendor.connections && vendor.connections.length > 0 ? (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {vendor.connections.map((c, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-2 rounded-lg bg-[var(--bg-secondary)] text-xs"
                >
                  <div>
                    <p className="font-medium text-[var(--text-primary)]">
                      {c.entity_name}
                    </p>
                    <p className="text-[var(--text-secondary)]">
                      {c.type} {c.detail ? `· ${c.detail}` : ""}
                    </p>
                  </div>
                  <span
                    className={`font-mono font-bold text-xs ${
                      c.risk_level === 'HIGH' ? 'text-[#e53e5c]' : c.risk_level === 'MED' ? 'text-[#d49a00]' : 'text-[#00b876]'
                    }`}
                  >
                    {c.risk_level ?? "—"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[var(--text-secondary)]">
              No connections found
            </p>
          )}
        </motion.div>

        {/* Shell Explanation */}
        {vendor.shell_explanation && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border-primary)] p-6"
          >
            <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3 font-[family-name:var(--font-display)]">
              Shell Risk Analysis
            </h2>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              {vendor.shell_explanation}
            </p>
          </motion.div>
        )}

        {/* Recent Tenders */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border-primary)] p-6"
        >
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2 font-[family-name:var(--font-display)]">
            <FileText className="w-4 h-4" />
            Recent Tenders ({vendor.recent_tenders?.length ?? 0})
          </h2>
          {vendor.recent_tenders && vendor.recent_tenders.length > 0 ? (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {vendor.recent_tenders.map((t, i) => (
                <div
                  key={i}
                  className="p-2 rounded-lg bg-[var(--bg-secondary)] text-xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-[var(--text-primary)] flex-1 line-clamp-1">
                      {t.title}
                    </p>
                    <span
                      className="font-mono font-bold text-xs flex-shrink-0"
                      style={{ color: getScoreColor(t.risk_score ?? 0) }}
                    >
                      {t.risk_score ?? "—"}
                    </span>
                  </div>
                  <p className="text-[var(--text-secondary)] mt-0.5">
                    {t.amount ? `₹${(t.amount / 10000000).toFixed(1)} Cr` : "—"} &middot; {t.date ?? ""}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[var(--text-secondary)]">
              No tenders found
            </p>
          )}
        </motion.div>
      </div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex flex-wrap gap-3"
      >
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--accent-red)]/10 text-[var(--accent-red)] text-xs font-medium hover:bg-[var(--accent-red)]/20 transition-colors">
          <Flag className="w-3.5 h-3.5" />
          Flag for Review
        </button>
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] text-xs font-medium hover:bg-[var(--accent-blue)]/20 transition-colors">
          <ExternalLink className="w-3.5 h-3.5" />
          View on MCA
        </button>
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-xs font-medium hover:bg-[var(--bg-tertiary)]/80 transition-colors">
          <Download className="w-3.5 h-3.5" />
          Export Report
        </button>
      </motion.div>
    </div>
  );
}
