"use client";

import { useEffect, useState } from "react";
import { useStreamStore } from "@/lib/store";
import { api } from "@/lib/api";
import type { KPIData } from "@/lib/types";
import {
  Zap, Globe, Landmark, AlertTriangle, DollarSign, User, Database,
} from "lucide-react";
import { motion } from "framer-motion";

const modules = [
  { id: 'bid_rigging', label: 'Bid Rigging', icon: <Zap size={16} />, kpiKey: 'bid_rigging_detected' as keyof KPIData },
  { id: 'shell_network', label: 'Shell Networks', icon: <Globe size={16} />, kpiKey: 'shell_networks_mapped' as keyof KPIData },
  { id: 'political_connection', label: 'Political Links', icon: <Landmark size={16} />, kpiKey: 'political_connections' as keyof KPIData },
  { id: 'high_value', label: 'High Value', icon: <DollarSign size={16} />, kpiKey: null },
  { id: 'short_window', label: 'Short Window', icon: <AlertTriangle size={16} />, kpiKey: null },
];

const riskLevels = [
  { id: 'high', label: 'High', range: '60–100', colorDot: 'bg-accent-red', kpiKey: 'high_risk_tenders' as keyof KPIData },
  { id: 'medium', label: 'Medium', range: '30–59', colorDot: 'bg-accent-yellow', kpiKey: 'medium_risk_tenders' as keyof KPIData },
  { id: 'low', label: 'Low', range: '0–29', colorDot: 'bg-accent-green', kpiKey: 'low_risk_tenders' as keyof KPIData },
];

export default function Sidebar() {
  const { alertTypeFilter, setAlertTypeFilter, riskTierFilter, setRiskTierFilter } = useStreamStore();
  const [kpis, setKpis] = useState<KPIData | null>(null);

  useEffect(() => {
    api.kpis().then(setKpis).catch(() => {});
  }, []);

  return (
    <div className="p-4 space-y-6">
      {/* User Info */}
      <div className="flex items-center gap-3 p-3 bg-surface2 rounded-xl border border-border">
        <div className="w-10 h-10 rounded-full bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center">
          <User size={18} className="text-accent-blue" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-[var(--font-syne)] font-bold text-text truncate">Investigator</p>
          <span className="inline-block px-2 py-0.5 bg-accent-blue/10 border border-accent-blue/30 rounded text-[10px] text-accent-blue font-[var(--font-space-mono)] font-bold">
            ANALYST
          </span>
        </div>
      </div>

      {/* Detection Modules */}
      <div>
        <h3 className="text-muted text-[10px] uppercase tracking-[0.2em] font-[var(--font-syne)] font-bold mb-3">
          Detection Modules
        </h3>
        <div className="space-y-1">
          {modules.map((mod) => {
            const count = mod.kpiKey && kpis ? (kpis[mod.kpiKey] as number | undefined) : null;
            const isActive = alertTypeFilter === mod.id;
            return (
              <motion.button
                key={mod.id}
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setAlertTypeFilter(isActive ? null : mod.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left ${
                  isActive
                    ? 'bg-accent-green/10 border border-accent-green/30 text-accent-green'
                    : 'text-muted hover:bg-surface2 hover:text-text border border-transparent'
                }`}
              >
                <span className={isActive ? 'text-accent-green' : 'text-muted'}>
                  {mod.icon}
                </span>
                <span className="flex-1 text-sm font-[var(--font-syne)] font-semibold">{mod.label}</span>
                {count != null && (
                  <span className={`min-w-[24px] h-6 flex items-center justify-center rounded-full text-xs font-[var(--font-space-mono)] font-bold ${
                    isActive ? 'bg-accent-green/20 text-accent-green' : 'bg-surface2 text-muted'
                  }`}>
                    {(count ?? 0).toLocaleString()}
                  </span>
                )}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Risk Level */}
      <div>
        <h3 className="text-muted text-[10px] uppercase tracking-[0.2em] font-[var(--font-syne)] font-bold mb-3">
          Risk Level
        </h3>
        <div className="space-y-1.5">
          {riskLevels.map((level) => {
            const count = kpis ? (kpis[level.kpiKey] as number | undefined) : null;
            const isActive = riskTierFilter === level.id;
            return (
              <button
                key={level.id}
                onClick={() => setRiskTierFilter(isActive ? null : level.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                  isActive ? 'bg-surface2 border border-border' : 'hover:bg-surface2/50 border border-transparent'
                }`}
              >
                <span className={`w-2.5 h-2.5 rounded-full ${level.colorDot}`} />
                <span className="flex-1 text-sm text-text font-[var(--font-syne)]">
                  {level.label} ({level.range})
                </span>
                {count != null && (
                  <span className="text-sm font-[var(--font-space-mono)] text-muted">
                    {(count ?? 0).toLocaleString()}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Summary */}
      {kpis && (
        <div>
          <h3 className="text-muted text-[10px] uppercase tracking-[0.2em] font-[var(--font-syne)] font-bold mb-3">
            Summary
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between px-3">
              <span className="text-muted">Total Tenders</span>
              <span className="font-[var(--font-space-mono)] text-text">{(kpis.total_tenders_analyzed ?? 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between px-3">
              <span className="text-muted">Bond Value</span>
              <span className="font-[var(--font-space-mono)] text-text">₹{(kpis.total_bond_value_cr ?? 0).toLocaleString()}Cr</span>
            </div>
            <div className="flex justify-between px-3">
              <span className="text-muted">Parties Linked</span>
              <span className="font-[var(--font-space-mono)] text-text">{kpis.political_parties_linked ?? 0}</span>
            </div>
          </div>
        </div>
      )}

      {/* Data Sources */}
      <div>
        <h3 className="text-muted text-[10px] uppercase tracking-[0.2em] font-[var(--font-syne)] font-bold mb-3">
          Data Sources
        </h3>
        <div className="space-y-2">
          {[
            { name: 'Procurement (OCDS)', status: 'live' },
            { name: 'Company Registry', status: 'live' },
            { name: 'Electoral Bonds', status: 'live' },
            { name: 'ML Pipeline', status: 'live' },
          ].map((src) => (
            <div key={src.name} className="flex items-center justify-between px-3 py-1.5">
              <div className="flex items-center gap-2">
                <Database size={12} className="text-muted" />
                <span className="text-sm text-text font-[var(--font-syne)]">{src.name}</span>
              </div>
              <span className="text-xs font-[var(--font-space-mono)] font-bold text-accent-green">Live</span>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-4 border-t border-border">
        <p className="text-[10px] text-muted/40 font-[var(--font-space-mono)] text-center">
          STREAM v2.4 · ML Pipeline v3.2
        </p>
      </div>
    </div>
  );
}
