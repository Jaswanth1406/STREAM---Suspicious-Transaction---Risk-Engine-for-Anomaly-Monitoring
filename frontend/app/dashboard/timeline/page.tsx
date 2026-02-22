"use client";

import { motion } from "framer-motion";
import { api } from "@/lib/api";
import type { ActivityEvent } from "@/lib/types";
import { Clock, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

const typeColors: Record<string, { border: string; bg: string }> = {
  flag_raised: { border: 'border-accent-red', bg: 'bg-accent-red/10' },
  contract_awarded: { border: 'border-accent-yellow', bg: 'bg-accent-yellow/10' },
  bond_purchased: { border: 'border-accent-blue', bg: 'bg-accent-blue/10' },
  electoral_bond: { border: 'border-accent-blue', bg: 'bg-accent-blue/10' },
  prediction_made: { border: 'border-accent-green', bg: 'bg-accent-green/10' },
};

const iconMap: Record<string, string> = {
  bond: '🏦',
  flag: '🚩',
  contract: '📄',
  prediction: '🤖',
};

export default function TimelinePage() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, unknown> = { limit: 100 };
    if (filterType) params.event_type = filterType;
    api.activityRecent(params)
      .then((data) => setEvents(data.activities ?? data.events ?? []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [filterType]);

  return (
    <div className="space-y-4">
      {/* Tab Bar */}
      <div className="flex items-center gap-1 border-b border-border pb-0 overflow-x-auto">
        <Link href="/dashboard" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Fraud Alerts</Link>
        <Link href="/dashboard/network" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Network Graph</Link>
        <Link href="/dashboard/bids" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Bid Analysis</Link>
        <span className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-accent-green tab-active whitespace-nowrap">Timeline</span>
        <Link href="/dashboard/chat" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">AI Assistant</Link>
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="font-[var(--font-syne)] text-xl font-bold text-text">Event Timeline</h2>
        <div className="flex items-center gap-2">
          <Clock size={14} className="text-muted" />
          <span className="text-xs font-[var(--font-space-mono)] text-muted">{events.length} events</span>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2 flex-wrap">
        {[
          { key: null, label: 'All' },
          { key: 'electoral_bond', label: '🏦 Electoral Bonds' },
          { key: 'flag_raised', label: '🚩 Flags' },
          { key: 'contract_awarded', label: '📄 Contracts' },
          { key: 'prediction_made', label: '🤖 ML Predictions' },
        ].map((f) => (
          <button
            key={f.key || 'all'}
            onClick={() => setFilterType(f.key)}
            className={`text-[10px] px-3 py-1.5 rounded-lg border font-[var(--font-space-mono)] transition-all ${
              filterType === f.key
                ? 'border-accent-green/50 text-accent-green bg-accent-green/10'
                : 'border-border text-muted hover:text-text'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-10 h-10 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin" />
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />
          <div className="space-y-0">
            {events.map((event, index) => {
              const colors = typeColors[event.event_type] || typeColors.flag_raised;
              const displayIcon = iconMap[event.icon] || event.icon || '📋';
              return (
                <motion.div
                  key={`${event.event_type}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03, duration: 0.4 }}
                  className="relative flex items-start gap-4 py-4 group"
                >
                  <div className="relative z-10 w-12 flex-shrink-0 flex items-center justify-center">
                    <div className={`w-10 h-10 rounded-full ${colors.bg} border ${colors.border} flex items-center justify-center transition-all group-hover:scale-110`}>
                      <span className="text-base">{displayIcon}</span>
                    </div>
                  </div>
                  <div className="flex-1 bg-surface border border-border rounded-xl p-4 transition-all cursor-pointer group-hover:translate-x-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        {event.risk_tier && (
                          <span className={`text-[10px] font-[var(--font-space-mono)] font-bold px-1.5 py-0.5 rounded ${
                            event.risk_tier === 'HIGH' ? 'text-accent-red bg-accent-red/10' :
                            event.risk_tier === 'MEDIUM' ? 'text-accent-yellow bg-accent-yellow/10' :
                            'text-accent-green bg-accent-green/10'
                          }`}>{event.risk_tier}</span>
                        )}
                        <span className="text-muted/30">·</span>
                        <span className="text-[10px] font-[var(--font-space-mono)] text-muted capitalize">{event.event_type.replace(/_/g, ' ')}</span>
                      </div>
                      {event.risk_score != null && (
                        <span className={`font-[var(--font-space-mono)] text-lg font-bold ${
                          event.risk_score >= 60 ? 'text-accent-red' : event.risk_score >= 30 ? 'text-accent-yellow' : 'text-accent-green'
                        }`}>
                          {Math.round(event.risk_score)}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-1 group-hover:text-accent-green transition-colors">
                      {event.title}
                    </h3>
                    <p className="text-xs text-muted mb-2">{event.subtitle}</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      {event.amount_cr != null && (
                        <span className="text-[9px] bg-surface2 border border-border px-2 py-0.5 rounded font-[var(--font-space-mono)] text-muted">
                          ₹{event.amount_cr.toLocaleString()} Cr
                        </span>
                      )}
                      {event.entity_name && (
                        <span className="text-[9px] bg-surface2 border border-border px-2 py-0.5 rounded font-[var(--font-space-mono)] text-muted">
                          {event.entity_name}
                        </span>
                      )}
                      {event.party_name && (
                        <span className="text-[9px] bg-surface2 border border-border px-2 py-0.5 rounded font-[var(--font-space-mono)] text-accent-blue">
                          {event.party_name}
                        </span>
                      )}
                      <ChevronRight size={12} className="text-muted/30" />
                    </div>
                  </div>
                </motion.div>
              );
            })}
            {events.length === 0 && (
              <div className="text-center py-16">
                <Clock size={48} className="mx-auto text-muted/30 mb-4" />
                <p className="text-muted font-[var(--font-syne)]">No events found</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
