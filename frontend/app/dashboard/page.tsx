"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle, Eye, Search, X,
  TrendingUp, Building2, Target,
  ChevronLeft, ChevronRight,
} from "lucide-react";
import { useStreamStore } from "@/lib/store";
import { api } from "@/lib/api";
import type { KPIData, AlertsResponse } from "@/lib/types";
import AlertCard from "@/components/AlertCard";
import Link from "next/link";
import { useEffect, useState, useCallback } from "react";

export default function FraudAlertsPage() {
  const { alertTypeFilter, riskTierFilter, searchQuery, setSearchQuery } = useStreamStore();
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [alertsData, setAlertsData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    api.kpis().then(setKpis).catch(() => {});
  }, []);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        page,
        page_size: pageSize,
        sort_by: 'risk_score',
        sort_order: 'desc',
      };
      if (alertTypeFilter) params.alert_type = alertTypeFilter;
      if (riskTierFilter) params.risk_tier = riskTierFilter;
      if (searchQuery) params.search = searchQuery;
      const data = await api.alerts(params);
      setAlertsData(data);
    } catch {
      setAlertsData(null);
    }
    setLoading(false);
  }, [alertTypeFilter, riskTierFilter, searchQuery, page]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);
  useEffect(() => { setPage(1); }, [alertTypeFilter, riskTierFilter, searchQuery]);

  const alerts = alertsData?.alerts || [];
  const totalPages = alertsData?.total_pages || 1;
  const total = alertsData?.total || 0;

  return (
    <div className="space-y-6">
      {/* Tab Bar */}
      <div className="flex items-center gap-1 border-b border-border pb-0 overflow-x-auto">
        <span className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-accent-green tab-active whitespace-nowrap">Fraud Alerts</span>
        <Link href="/dashboard/network" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Network Graph</Link>
        <Link href="/dashboard/bids" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Bid Analysis</Link>
        <Link href="/dashboard/timeline" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Timeline</Link>
        <Link href="/dashboard/chat" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">AI Assistant</Link>
      </div>

      {/* KPI Cards */}
      {kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
          <KpiCard value={kpis.active_flags.toLocaleString()} label="Active Flags" delay={0} icon={<AlertTriangle size={18} />} color="text-accent-red" />
          <KpiCard value={`₹${kpis.at_risk_value_cr.toLocaleString()}Cr`} label="At Risk Value" delay={1} icon={<TrendingUp size={18} />} color="text-accent-red" />
          <KpiCard value={kpis.vendors_tracked.toLocaleString()} label="Vendors Tracked" delay={2} icon={<Building2 size={18} />} color="text-accent-blue" />
          <KpiCard value={`${kpis.precision_rate}%`} label="False Positive Control" delay={3} icon={<Target size={18} />} color="text-accent-green" />
        </div>
      )}

      {/* Due Process Banner */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
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
              No flag constitutes proof of wrongdoing. Each alert requires human review and independent
              investigation before any action. Confidence scores reflect pattern similarity, not guilt.
            </span>
          </p>
        </div>
      </motion.div>

      {/* Search Bar */}
      <div className="relative">
        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search tender ID, buyer name, category... ESC to clear"
          className="w-full bg-surface border border-border rounded-xl pl-11 pr-10 py-3 text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-green/30 transition-all font-[var(--font-space-mono)] text-sm"
          onKeyDown={(e) => e.key === 'Escape' && setSearchQuery('')}
        />
        {searchQuery && (
          <button onClick={() => setSearchQuery('')} className="absolute right-4 top-1/2 -translate-y-1/2 text-muted hover:text-text">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Results info */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted font-[var(--font-space-mono)]">{total.toLocaleString()} alerts found</p>
        {alertTypeFilter && (
          <button
            onClick={() => useStreamStore.getState().setAlertTypeFilter(null)}
            className="text-xs text-accent-green hover:underline font-[var(--font-space-mono)]"
          >
            Clear filter: {alertTypeFilter.replace(/_/g, ' ')}
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="w-10 h-10 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin" />
        </div>
      )}

      {/* Alert Cards */}
      {!loading && (
        <div className="space-y-4">
          {alerts.map((alert, index) => (
            <motion.div
              key={alert.id + '-' + index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.03, duration: 0.4 }}
            >
              <AlertCard alert={alert} />
            </motion.div>
          ))}
          {alerts.length === 0 && (
            <div className="text-center py-16">
              <Eye size={48} className="mx-auto text-muted/30 mb-4" />
              <p className="text-muted font-[var(--font-syne)]">No alerts match your current filters</p>
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-4">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page <= 1}
            className="flex items-center gap-1 px-3 py-2 rounded-lg border border-border text-sm text-muted hover:text-text disabled:opacity-30 transition-all"
          >
            <ChevronLeft size={14} /> Prev
          </button>
          <span className="text-sm font-[var(--font-space-mono)] text-muted">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages}
            className="flex items-center gap-1 px-3 py-2 rounded-lg border border-border text-sm text-muted hover:text-text disabled:opacity-30 transition-all"
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function KpiCard({ value, label, delay, icon, color }: {
  value: string; label: string; delay: number; icon: React.ReactNode; color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.1, duration: 0.5 }}
      className="bg-surface border border-border rounded-xl p-4 transition-all group"
    >
      <div className={`flex items-center gap-2 ${color} mb-2`}>{icon}</div>
      <p className={`font-[var(--font-space-mono)] text-2xl md:text-3xl font-bold ${color}`}>{value}</p>
      <p className="text-muted text-xs font-[var(--font-syne)] font-semibold uppercase tracking-wider mt-1">{label}</p>
    </motion.div>
  );
}
