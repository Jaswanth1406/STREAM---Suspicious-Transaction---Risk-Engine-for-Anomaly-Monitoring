"use client";

import type { ApiAlert } from "@/lib/types";
import { motion } from "framer-motion";
import { Landmark, Banknote, Users, Clock, AlertTriangle, FileText } from "lucide-react";
import { useEffect, useState } from "react";

const alertTypeConfig: Record<string, { label: string; color: string; bg: string; border: string }> = {
  political:   { label: 'Electoral Bond', color: 'text-accent-red', bg: 'bg-accent-red/10', border: 'border-accent-red/30' },
  bid_rigging: { label: 'Bid Rigging',    color: 'text-accent-yellow', bg: 'bg-accent-yellow/10', border: 'border-accent-yellow/30' },
  shell_network:        { label: 'Shell Network', color: 'text-accent-blue', bg: 'bg-accent-blue/10', border: 'border-accent-blue/30' },
  political_connection: { label: 'Political Link', color: 'text-accent-blue', bg: 'bg-accent-blue/10', border: 'border-accent-blue/30' },
  high_value:    { label: 'High Value',    color: 'text-accent-red', bg: 'bg-accent-red/10', border: 'border-accent-red/30' },
  short_window:  { label: 'Short Window',  color: 'text-accent-yellow', bg: 'bg-accent-yellow/10', border: 'border-accent-yellow/30' },
};

function getRiskColor(score: number): string {
  if (score >= 60) return 'text-accent-red';
  if (score >= 30) return 'text-accent-yellow';
  return 'text-accent-green';
}

function getBorderColor(score: number): string {
  if (score >= 60) return 'border-l-accent-red';
  if (score >= 30) return 'border-l-accent-yellow';
  return 'border-l-accent-green';
}

function formatCurrency(value: number): string {
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(1)}Cr`;
  if (value >= 1e5) return `₹${(value / 1e5).toFixed(1)}L`;
  return `₹${value.toLocaleString()}`;
}

export default function AlertCard({ alert }: { alert: ApiAlert }) {
  const config = alertTypeConfig[alert.alert_type] || alertTypeConfig.political;
  const [barWidth, setBarWidth] = useState(0);
  const isBond = alert.sub_type === 'electoral_bond' || alert.alert_type === 'political';

  useEffect(() => {
    const timer = setTimeout(() => setBarWidth(alert.evidence_strength), 200);
    return () => clearTimeout(timer);
  }, [alert.evidence_strength]);

  // Build display flags
  const displayFlags: string[] = [];
  if (isBond) {
    displayFlags.push(...(alert.flags_triggered || []));
  } else {
    // Procurement alert — extract from flags object
    const flagEntries = Object.entries(alert.flags ?? {})
      .filter(([, v]) => v === 1)
      .map(([k]) => k.replace(/^flag_/, '').replace(/^ml_anomaly_flag$/, 'ml_anomaly').replace(/_/g, ' '));
    displayFlags.push(...flagEntries);
  }

  return (
    <div className={`alert-card bg-surface border border-border rounded-xl p-5 border-l-[3px] ${getBorderColor(alert.risk_score)} cursor-pointer group`}>
      {/* Top row */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`${config.bg} ${config.border} border ${config.color} px-2.5 py-1 rounded text-[10px] font-[var(--font-space-mono)] font-bold tracking-wider uppercase`}>
            {config.label}
          </span>
          {alert.sub_type && (
            <span className="bg-surface2 border border-border px-2 py-1 rounded text-[10px] text-muted font-[var(--font-space-mono)] capitalize">
              {alert.sub_type.replace(/_/g, ' ')}
            </span>
          )}
          {alert.risk_tier && (
            <span className={`px-2 py-1 rounded text-[10px] font-[var(--font-space-mono)] font-bold ${
              alert.risk_tier === 'High' ? 'bg-accent-red/10 text-accent-red border border-accent-red/30' :
              alert.risk_tier === 'Medium' ? 'bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/30' :
              'bg-accent-green/10 text-accent-green border border-accent-green/30'
            }`}>
              {alert.risk_tier.replace(/[🔴🟡🟢]\s*/g, '')} RISK
            </span>
          )}
        </div>
        <div className="text-right flex-shrink-0 ml-3">
          <p className={`font-[var(--font-space-mono)] text-3xl font-bold ${getRiskColor(alert.risk_score)}`}>
            {Math.round(alert.risk_score)}
          </p>
          <p className="text-[10px] text-muted uppercase tracking-wider">Risk Score</p>
          <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-[var(--font-space-mono)] font-bold ${
            alert.confidence >= 0.85 ? 'bg-accent-green/10 text-accent-green border border-accent-green/30' :
            alert.confidence >= 0.70 ? 'bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/30' :
            'bg-accent-blue/10 text-accent-blue border border-accent-blue/30'
          }`}>
            {Math.round(alert.confidence * 100)}% CONF.
          </span>
        </div>
      </div>

      {/* Title */}
      <h3 className="font-[var(--font-syne)] text-lg font-bold text-text mb-2 group-hover:text-accent-green transition-colors">
        {alert.title}
      </h3>

      {/* Description */}
      <p className="text-muted text-sm leading-relaxed mb-4">
        {alert.explanation || alert.risk_explanation || ''}
      </p>

      {/* Metadata — adapts based on alert type */}
      {isBond ? (
        <div className="flex items-center gap-4 mb-4 text-xs text-muted flex-wrap">
          <span className="flex items-center gap-1 font-[var(--font-space-mono)]">
            <Banknote size={12} className="text-accent-yellow" />
            ₹{(alert.total_bond_value_cr ?? 0).toLocaleString()}Cr
          </span>
          <span className="flex items-center gap-1 font-[var(--font-space-mono)]">
            <FileText size={12} />
            {(alert.total_bonds ?? 0).toLocaleString()} bonds
          </span>
          <span className="flex items-center gap-1 font-[var(--font-space-mono)]">
            <Landmark size={12} />
            {(alert.parties_funded?.length ?? 0)} parties
          </span>
          {alert.purchaser_name && (
            <span className="flex items-center gap-1 font-[var(--font-space-mono)]">
              <Users size={12} />
              {alert.purchaser_name}
            </span>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-4 mb-4 text-xs text-muted flex-wrap">
          {alert.amount != null && (
            <span className="font-[var(--font-space-mono)]">
              <Banknote size={12} className="inline mr-1" />
              {alert.amount_display || formatCurrency(alert.amount)}
            </span>
          )}
          {alert.buyer_name && (
            <span className="font-[var(--font-space-mono)]">{alert.buyer_name}</span>
          )}
          {alert.num_tenderers != null && (
            <span className="font-[var(--font-space-mono)]">
              {alert.num_tenderers} bidder{alert.num_tenderers !== 1 ? 's' : ''}
            </span>
          )}
          {alert.duration_days != null && (
            <span className="font-[var(--font-space-mono)]">
              <Clock size={12} className="inline mr-1" />{alert.duration_days}d window
            </span>
          )}
        </div>
      )}

      {/* Parties funded (bond-specific) */}
      {isBond && alert.parties_funded && alert.parties_funded.length > 0 && (
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          {alert.parties_funded.slice(0, 4).map((party, i) => (
            <span key={i} className="text-[9px] bg-accent-blue/10 text-accent-blue border border-accent-blue/20 px-2 py-0.5 rounded font-[var(--font-space-mono)]">
              {party.length > 25 ? party.slice(0, 25) + '…' : party}
            </span>
          ))}
          {alert.parties_funded.length > 4 && (
            <span className="text-[9px] text-muted font-[var(--font-space-mono)]">+{alert.parties_funded.length - 4} more</span>
          )}
        </div>
      )}

      {/* Flags */}
      {displayFlags.length > 0 && (
        <div className="flex items-center gap-2 mb-4 text-xs text-muted flex-wrap">
          <AlertTriangle size={12} className="text-accent-red" />
          {displayFlags.slice(0, 3).map((flag, i) => (
            <span key={i} className="text-[9px] bg-accent-red/10 text-accent-red border border-accent-red/20 px-1.5 py-0.5 rounded font-[var(--font-space-mono)] capitalize">{flag}</span>
          ))}
          {displayFlags.length > 3 && <span className="text-[9px] text-muted">+{displayFlags.length - 3}</span>}
        </div>
      )}

      {/* Evidence strength */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)]">Evidence strength</span>
          <span className="text-xs font-[var(--font-space-mono)] text-muted">{alert.evidence_strength}/100</span>
        </div>
        <div className="h-1.5 bg-surface2 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${
              alert.evidence_strength >= 60 ? 'bg-accent-red' :
              alert.evidence_strength >= 30 ? 'bg-accent-yellow' : 'bg-accent-blue'
            }`}
            initial={{ width: 0 }}
            animate={{ width: `${barWidth}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </div>
      </div>
    </div>
  );
}
