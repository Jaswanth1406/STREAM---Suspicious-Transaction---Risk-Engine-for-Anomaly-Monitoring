"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { VendorProfile, VendorSearchResult } from "@/lib/types";
import { motion } from "framer-motion";
import {
  Shield, Search, Landmark, Users, MapPin, Link2,
  ArrowUpRight, FileText,
} from "lucide-react";

const connectionIcons: Record<string, React.ReactNode> = {
  political_bond: <Landmark size={14} />,
  co_bidder: <Link2 size={14} />,
  shared_address: <MapPin size={14} />,
  shared_director: <Users size={14} />,
};

const riskColors: Record<string, string> = {
  HIGH: 'text-accent-red',
  MED: 'text-accent-yellow',
  LOW: 'text-accent-green',
};

function getScoreColor(score: number): string {
  if (score >= 60) return '#e53e5c';
  if (score >= 30) return '#d49a00';
  return '#00b876';
}

export default function RightPanel() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<VendorSearchResult[]>([]);
  const [vendor, setVendor] = useState<VendorProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [ringOffset, setRingOffset] = useState(283);

  useEffect(() => {
    if (vendor) {
      const score = vendor.composite_risk_score ?? vendor.overall_risk_score ?? 0;
      const timer = setTimeout(() => {
        setRingOffset(283 - (283 * score / 100));
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [vendor]);

  useEffect(() => {
    if (query.length < 3) { 
      setSearchResults([]); 
      return; 
    }

    const timer = setTimeout(async () => {
      try {
        const data = await api.vendorSearch(query, 10);
        setSearchResults(data.results);
      } catch { 
        setSearchResults([]); 
      }
    }, 500); // Increased debounce from 300ms to 500ms

    return () => clearTimeout(timer);
  }, [query]);

  const selectVendor = async (id: string) => {
    setLoading(true);
    setSearchResults([]);
    setQuery('');
    try {
      const data = await api.vendor(id);
      setVendor(data);
    } catch { /* noop */ }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin" />
          <p className="text-muted text-xs font-[var(--font-space-mono)]">Loading vendor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto">
      {/* Search */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search vendor..."
          className="w-full bg-surface2 border border-border rounded-lg pl-9 pr-3 py-2 text-sm text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-green/30 font-[var(--font-space-mono)]"
        />
        {searchResults.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-surface border border-border rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
            {searchResults.map((r) => (
              <button
                key={r.entity_id}
                onClick={() => selectVendor(r.entity_id)}
                className="w-full text-left px-3 py-2.5 hover:bg-surface2 transition-colors border-b border-border/50 last:border-0"
              >
                <p className="text-sm font-[var(--font-syne)] font-semibold text-text truncate">{r.company_name}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] font-[var(--font-space-mono)] text-muted">{r.cin}</span>
                  <span className={`text-[10px] font-[var(--font-space-mono)] font-bold ${
                    r.risk_tier === 'HIGH' ? 'text-accent-red' : r.risk_tier === 'MEDIUM' ? 'text-accent-yellow' : 'text-accent-green'
                  }`}>{r.composite_risk_score?.toFixed(1)}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {!vendor ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Shield size={48} className="mx-auto text-muted/20 mb-4" />
            <p className="text-muted text-sm font-[var(--font-syne)]">Search a vendor to view profile</p>
          </div>
        </div>
      ) : (
        <>
          {/* Vendor Name */}
          <div>
            <h2 className="font-[var(--font-syne)] text-lg font-extrabold text-text leading-tight">{vendor.company_name}</h2>
            <p className="font-[var(--font-space-mono)] text-xs text-muted mt-1">CIN: {vendor.cin}</p>
            <div className="flex gap-2 mt-2 flex-wrap">
              <span className="text-[10px] bg-surface2 border border-border rounded px-2 py-0.5 font-[var(--font-space-mono)] text-muted">{vendor.company_status ?? vendor.status ?? '—'}</span>
              {vendor.state && <span className="text-[10px] bg-surface2 border border-border rounded px-2 py-0.5 font-[var(--font-space-mono)] text-muted">{vendor.state}</span>}
              {vendor.risk_tier && <span className={`text-[10px] border rounded px-2 py-0.5 font-[var(--font-space-mono)] font-bold ${
                vendor.risk_tier === 'HIGH' ? 'border-accent-red/30 text-accent-red bg-accent-red/10' :
                vendor.risk_tier === 'MEDIUM' ? 'border-accent-yellow/30 text-accent-yellow bg-accent-yellow/10' :
                'border-accent-green/30 text-accent-green bg-accent-green/10'
              }`}>{vendor.risk_tier}</span>}
            </div>
          </div>

          {/* Risk Ring */}
          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center gap-6">
            <div className="relative w-28 h-28 flex-shrink-0">
              <svg viewBox="0 0 100 100" className="w-28 h-28 -rotate-90">
                <circle cx="50" cy="50" r="45" fill="none" stroke="var(--border)" strokeWidth="6" />
                <circle cx="50" cy="50" r="45" fill="none" stroke={getScoreColor(vendor.composite_risk_score ?? 0)} strokeWidth="6" strokeLinecap="round" strokeDasharray="283" strokeDashoffset={ringOffset} className="transition-all duration-[1.5s] ease-out" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="font-[var(--font-space-mono)] text-3xl font-bold" style={{ color: getScoreColor(vendor.composite_risk_score ?? 0) }}>{Math.round(vendor.composite_risk_score ?? 0)}</span>
              </div>
            </div>
            <div className="space-y-2 flex-1">
              <SubScore label="Bid Pattern" value={vendor.sub_scores?.bid_pattern ?? 0} color={getScoreColor(vendor.sub_scores?.bid_pattern ?? 0)} />
              <SubScore label="Shell Risk" value={vendor.sub_scores?.shell_risk ?? 0} color={getScoreColor(vendor.sub_scores?.shell_risk ?? 0)} />
              <SubScore label="Political" value={vendor.sub_scores?.political ?? 0} color={getScoreColor(vendor.sub_scores?.political ?? 0)} />
              <SubScore label="Financials" value={vendor.sub_scores?.financials ?? 0} color={getScoreColor(vendor.sub_scores?.financials ?? 0)} />
            </div>
          </motion.div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-surface2 rounded-lg p-2 border border-border">
              <p className="text-[10px] text-muted font-[var(--font-syne)]">Connections</p>
              <p className="text-lg font-[var(--font-space-mono)] font-bold text-text">{vendor.connections?.length ?? 0}</p>
            </div>
            <div className="bg-surface2 rounded-lg p-2 border border-border">
              <p className="text-[10px] text-muted font-[var(--font-syne)]">Review</p>
              <p className="text-lg font-[var(--font-space-mono)] font-bold text-accent-red">{vendor.requires_human_review ? 'Required' : 'OK'}</p>
            </div>
          </div>

          {/* Connections */}
          <div>
            <h3 className="text-muted text-[10px] uppercase tracking-[0.2em] font-[var(--font-syne)] font-bold mb-3">
              Connections ({vendor.connections?.length ?? 0})
            </h3>
            <div className="space-y-2">
              {(vendor.connections ?? []).map((conn, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-3 p-2.5 bg-surface2/50 rounded-lg border border-border hover:border-border/80 transition-all cursor-pointer group"
                >
                  <div className="w-8 h-8 rounded-full bg-surface flex items-center justify-center text-muted group-hover:text-text transition-colors">
                    {connectionIcons[conn.type] || <Link2 size={14} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-text font-[var(--font-syne)] font-semibold truncate">{conn.label ?? conn.entity_name ?? conn.type}</p>
                    <p className="text-[10px] text-muted font-[var(--font-space-mono)]">
                      {conn.type}{conn.cluster_size ? ` · ${conn.cluster_size} entities` : ''}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Shell Explanation */}
          {vendor.shell_explanation && (
            <div className="bg-accent-yellow/5 border border-accent-yellow/20 rounded-lg p-3">
              <h3 className="text-muted text-[10px] uppercase tracking-[0.2em] font-[var(--font-syne)] font-bold mb-2">
                Shell Risk Analysis
              </h3>
              <p className="text-xs text-text/80 font-[var(--font-space-mono)] leading-relaxed">{vendor.shell_explanation}</p>
            </div>
          )}

          {/* Recent Tenders */}
          {vendor.recent_tenders && vendor.recent_tenders.length > 0 && (
            <div>
              <h3 className="text-muted text-[10px] uppercase tracking-[0.2em] font-[var(--font-syne)] font-bold mb-3">
                Recent Tenders
              </h3>
              <div className="space-y-2">
                {vendor.recent_tenders.map((t, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 bg-surface2/50 rounded-lg border border-border">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text font-[var(--font-syne)] font-semibold truncate">{t.title}</p>
                      <p className="text-[10px] text-muted font-[var(--font-space-mono)]">{t.tender_id} · {t.date}</p>
                    </div>
                    <span className={`font-[var(--font-space-mono)] text-lg font-bold ${
                      t.risk_score >= 60 ? 'text-accent-red' : t.risk_score >= 30 ? 'text-accent-yellow' : 'text-accent-green'
                    }`}>{t.risk_score}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-2 pt-2">
            <button className="w-full flex items-center gap-2 px-4 py-2.5 bg-accent-red/10 border border-accent-red/30 rounded-lg text-accent-red text-sm font-[var(--font-syne)] font-bold hover:bg-accent-red/20 transition-all">
              <ArrowUpRight size={14} /> Escalate
            </button>
            <button className="w-full flex items-center gap-2 px-4 py-2.5 bg-accent-blue/10 border border-accent-blue/30 rounded-lg text-accent-blue text-sm font-[var(--font-syne)] font-bold hover:bg-accent-blue/20 transition-all">
              <FileText size={14} /> Annotate
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function SubScore({ label, value, color }: { label: string; value: number; color: string }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(value), 400);
    return () => clearTimeout(t);
  }, [value]);

  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-muted font-[var(--font-syne)] w-16 flex-shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-surface rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${width}%` }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
        />
      </div>
      <span className="text-xs font-[var(--font-space-mono)] text-muted w-7 text-right">{value}</span>
    </div>
  );
}
