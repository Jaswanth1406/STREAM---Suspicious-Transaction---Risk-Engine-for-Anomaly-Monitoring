"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import type { NetworkGraphResponse } from "@/lib/types";
import { ZoomIn, ZoomOut, RotateCcw, Filter } from "lucide-react";
import Link from "next/link";

export default function NetworkPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graphData, setGraphData] = useState<NetworkGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [filterEdgeType, setFilterEdgeType] = useState<string | null>(null);
  const nodePositionsRef = useRef<Record<string, { x: number; y: number }>>({});
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    setLoading(true);
    api.networkGraph({ min_risk_score: 0, limit_nodes: 300 })
      .then((data) => {
        setGraphData(data);
        const positions: Record<string, { x: number; y: number }> = {};
        const cx = 400, cy = 300;
        data.nodes.forEach((node, i) => {
          const angle = (i / data.nodes.length) * Math.PI * 2;
          const radius = 120 + Math.random() * 120;
          positions[node.id] = {
            x: cx + Math.cos(angle) * radius,
            y: cy + Math.sin(angle) * radius,
          };
        });
        // Force simulation
        for (let iter = 0; iter < 80; iter++) {
          for (let i = 0; i < data.nodes.length; i++) {
            for (let j = i + 1; j < data.nodes.length; j++) {
              const a = data.nodes[i], b = data.nodes[j];
              const pa = positions[a.id], pb = positions[b.id];
              if (!pa || !pb) continue;
              const dx = pb.x - pa.x, dy = pb.y - pa.y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const force = 600 / (dist * dist);
              const fx = (dx / dist) * force, fy = (dy / dist) * force;
              pa.x -= fx; pa.y -= fy; pb.x += fx; pb.y += fy;
            }
          }
          data.edges.forEach((edge) => {
            const src = positions[edge.source], tgt = positions[edge.target];
            if (!src || !tgt) return;
            const dx = tgt.x - src.x, dy = tgt.y - src.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = (dist - 100) * 0.01;
            const fx = (dx / dist) * force, fy = (dy / dist) * force;
            src.x += fx; src.y += fy; tgt.x -= fx; tgt.y -= fy;
          });
          data.nodes.forEach((node) => {
            const p = positions[node.id];
            if (p) { p.x += (cx - p.x) * 0.01; p.y += (cy - p.y) * 0.01; }
          });
        }
        nodePositionsRef.current = positions;
      })
      .catch(() => setGraphData(null))
      .finally(() => setLoading(false));
  }, []);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);
    ctx.clearRect(0, 0, rect.width, rect.height);
    ctx.save();
    ctx.translate(offset.x, offset.y);
    ctx.scale(zoom, zoom);

    const pos = nodePositionsRef.current;
    const edges = filterEdgeType
      ? graphData.edges.filter((e) => e.type === filterEdgeType)
      : graphData.edges;

    // Draw edges
    edges.forEach((edge) => {
      const src = pos[edge.source], tgt = pos[edge.target];
      if (!src || !tgt || !isFinite(src.x) || !isFinite(src.y) || !isFinite(tgt.x) || !isFinite(tgt.y)) return;
      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      ctx.strokeStyle = (edge.color ?? '#999999') + "50";
      ctx.lineWidth = Math.min(3, 0.5 + ((edge.weight ?? 1) > 1000 ? 2 : (edge.weight ?? 1) * 0.3));
      ctx.stroke();
    });

    // Draw nodes
    graphData.nodes.forEach((node) => {
      const p = pos[node.id];
      if (!p || !isFinite(p.x) || !isFinite(p.y)) return;
      const isHovered = hoveredNode === node.id;
      const isSelected = selectedNode === node.id;
      const baseRadius = Math.max(4, (node.size ?? 20) * 0.12);
      const radius = isHovered || isSelected ? baseRadius + 3 : baseRadius;
      const color = node.color ?? '#6b7394';

      if (isHovered || isSelected) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, radius + 6, 0, Math.PI * 2);
        const glow = ctx.createRadialGradient(p.x, p.y, radius, p.x, p.y, radius + 6);
        glow.addColorStop(0, color + "40");
        glow.addColorStop(1, color + "00");
        ctx.fillStyle = glow;
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = isHovered || isSelected ? 1 : 0.8;
      ctx.fill();
      ctx.globalAlpha = 1;

      ctx.font = `${isHovered ? "bold " : ""}9px monospace`;
      ctx.fillStyle = "#1a1f36";
      ctx.textAlign = "center";
      ctx.fillText((node.label ?? '').slice(0, 20), p.x, p.y + radius + 14);

      if (isHovered || isSelected) {
        ctx.font = "bold 10px monospace";
        ctx.fillStyle = color;
        ctx.fillText(`Risk: ${node.risk_score ?? '—'}`, p.x, p.y - radius - 6);
      }
    });

    ctx.restore();
    animFrameRef.current = requestAnimationFrame(draw);
  }, [zoom, offset, hoveredNode, selectedNode, filterEdgeType, graphData]);

  useEffect(() => {
    animFrameRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [draw]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;
    const rect = canvas.getBoundingClientRect();

    if (isDragging) {
      setOffset({ x: offset.x + (e.clientX - dragStart.x), y: offset.y + (e.clientY - dragStart.y) });
      setDragStart({ x: e.clientX, y: e.clientY });
      return;
    }

    const pos = nodePositionsRef.current;
    const mx = (e.clientX - rect.left - offset.x) / zoom;
    const my = (e.clientY - rect.top - offset.y) / zoom;
    let found = false;
    for (const node of graphData.nodes) {
      const p = pos[node.id];
      if (!p) continue;
      if (Math.sqrt((mx - p.x) ** 2 + (my - p.y) ** 2) < 20) {
        setHoveredNode(node.id);
        canvas.style.cursor = "pointer";
        found = true;
        break;
      }
    }
    if (!found) {
      setHoveredNode(null);
      canvas.style.cursor = isDragging ? "grabbing" : "grab";
    }
  };

  const edgeTypes = graphData ? [...new Set(graphData.edges.map((e) => e.type))] : [];

  return (
    <div className="space-y-4 h-full">
      {/* Tab Bar */}
      <div className="flex items-center gap-1 border-b border-border pb-0 overflow-x-auto">
        <Link href="/dashboard" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Fraud Alerts</Link>
        <span className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-accent-green tab-active whitespace-nowrap">Network Graph</span>
        <Link href="/dashboard/bids" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Bid Analysis</Link>
        <Link href="/dashboard/timeline" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Timeline</Link>
        <Link href="/dashboard/chat" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">AI Assistant</Link>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <button onClick={() => setZoom((z) => Math.min(z + 0.2, 3))} className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center text-muted hover:text-text"><ZoomIn size={14} /></button>
          <button onClick={() => setZoom((z) => Math.max(z - 0.2, 0.3))} className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center text-muted hover:text-text"><ZoomOut size={14} /></button>
          <button onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }} className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center text-muted hover:text-text"><RotateCcw size={14} /></button>
          <span className="text-xs text-muted font-[var(--font-space-mono)] ml-2">
            {graphData?.stats ? `${graphData.stats.total_nodes} nodes · ${graphData.stats.total_edges} edges` : ''}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Filter size={12} className="text-muted" />
          {edgeTypes.map((type) => (
            <button
              key={type}
              onClick={() => setFilterEdgeType(filterEdgeType === type ? null : type)}
              className={`text-[10px] px-2 py-1 rounded border transition-all font-[var(--font-space-mono)] capitalize ${
                filterEdgeType === type
                  ? "border-accent-green/50 text-accent-green bg-accent-green/10"
                  : "border-border text-muted hover:text-text"
              }`}
            >
              {type.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div className="relative bg-surface/50 border border-border rounded-xl overflow-hidden" style={{ height: "calc(100vh - 240px)" }}>
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin" />
              <p className="text-muted text-xs font-[var(--font-space-mono)]">Loading network...</p>
            </div>
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            className="w-full h-full"
            onMouseMove={handleMouseMove}
            onMouseDown={(e) => { setIsDragging(true); setDragStart({ x: e.clientX, y: e.clientY }); }}
            onMouseUp={() => { setIsDragging(false); if (hoveredNode) setSelectedNode(hoveredNode); }}
            onMouseLeave={() => { setIsDragging(false); setHoveredNode(null); }}
          />
        )}

        {/* Legend */}
        {graphData?.stats && (
          <div className="absolute bottom-4 left-4 bg-surface/90 backdrop-blur-sm border border-border rounded-lg p-3 space-y-2">
            <p className="text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] font-bold mb-2">Node Types</p>
            {Object.entries(graphData.stats.node_types ?? {}).map(([type, count]) => (
              <div key={type} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: type === 'company' ? '#ff4444' : '#ff8800' }} />
                <span className="text-[10px] text-text capitalize font-[var(--font-space-mono)]">{type} ({count})</span>
              </div>
            ))}
            <div className="border-t border-border pt-2 mt-2 space-y-1">
              {Object.entries(graphData.stats.edge_types ?? {}).map(([type, count]) => (
                <div key={type} className="flex items-center gap-2">
                  <div className="w-4 h-0.5" style={{ backgroundColor: type === 'electoral_bond' ? '#ff8800' : type === 'co_bidder' ? '#4488ff' : '#88ff44' }} />
                  <span className="text-[10px] text-muted capitalize font-[var(--font-space-mono)]">{type.replace(/_/g, ' ')} ({count})</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Selected Node */}
        {selectedNode && graphData && (() => {
          const node = graphData.nodes.find((n) => n.id === selectedNode);
          if (!node) return null;
          const connCount = graphData.edges.filter((e) => e.source === node.id || e.target === node.id).length;
          return (
            <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="absolute top-4 right-4 bg-surface/90 backdrop-blur-sm border border-border rounded-lg p-4 w-64">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-[var(--font-syne)] font-bold text-text truncate">{node.label}</h4>
                <button onClick={() => setSelectedNode(null)} className="text-muted hover:text-text">✕</button>
              </div>
              <p className="text-[10px] text-muted mb-2 capitalize font-[var(--font-space-mono)]">
                Type: <span style={{ color: node.color }}>{node.type.replace(/_/g, ' ')}</span>
              </p>
              {node.risk_score != null && (
                <p className="text-lg font-[var(--font-space-mono)] font-bold" style={{ color: node.color }}>
                  Risk: {node.risk_score}
                </p>
              )}
              {node.risk_tier && <p className="text-[10px] text-muted">{node.risk_tier}</p>}
              <p className="text-[10px] text-muted mt-2">{connCount} connections</p>
            </motion.div>
          );
        })()}
      </div>
    </div>
  );
}
