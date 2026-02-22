"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { useStreamStore } from "@/lib/store";
import { Send, Bot, User, Sparkles, AlertTriangle, TrendingUp, Search } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import Link from "next/link";

const presetQueries = [
  { icon: <Search size={14} />, label: "Top risky vendors", query: "Show me the top 5 riskiest vendors with their risk scores" },
  { icon: <AlertTriangle size={14} />, label: "Bid rigging patterns", query: "Analyze recent bid rigging patterns across all tenders" },
  { icon: <TrendingUp size={14} />, label: "Shell company links", query: "Map all shell company connections in the current dataset" },
  { icon: <Sparkles size={14} />, label: "Electoral bond analysis", query: "Summarize electoral bond correlations with contract awards" },
];

const mockResponses: string[] = [
  `Based on my analysis of the current dataset, here are the **top 5 riskiest vendors**:\n\n1. **ROADTECH INDIA LTD** — Risk Score: 92\n   • Cartel pattern detected across 12 tenders\n   • Bid rotation with 2 other vendors\n\n2. **INFRATECH SOLUTIONS PVT LTD** — Risk Score: 87\n   • Cover bidding in 4 tenders\n   • Electoral bond linkage: ₹12Cr\n\n3. **ALPHA CONSTRUCTIONS** — Risk Score: 83\n   • Price clustering in 5 bids (0.5% range)\n   • Same network IP submissions\n\n4. **NEXGEN INFRA PVT LTD** — Risk Score: 79\n   • Phantom bidder pattern\n   • Company incorporated 45 days before tender\n\n5. **BUILDSMART PVT LTD** — Risk Score: 74\n   • Shell network of 7 entities\n   • Single director across all companies\n\n⚠️ *These are probabilistic risk indicators. Each requires independent investigation.*`,
  `**Bid Rigging Pattern Analysis**\n\nI've identified **3 distinct patterns** across the current alert dataset:\n\n**Pattern 1: Cover Bidding** (3 instances)\n• Losing bids inflated 18-23% above winner\n• Bids submitted within minutes of each other\n• Vendors share registered addresses\n\n**Pattern 2: Phantom Bidding** (2 instances)\n• Ghost companies with no verifiable presence\n• Incorporated days before tender deadlines\n• Zero employees on MCA filings\n\n**Pattern 3: Price Clustering** (1 instance)\n• 5 bids within 0.5% range\n• IP analysis shows same network origin\n• Statistical probability of coincidence: <0.1%\n\n📊 Overall confidence in pattern detection: **87%**`,
  `**Shell Company Network Map**\n\nI've traced **4 distinct shell company clusters**:\n\n**Cluster 1** — BUILDSMART Network (7 entities)\n• Common Director: DIN 09876543\n• All registered: Gurugram, Haryana\n• Combined contracts: ₹890 Cr\n\n**Cluster 2** — PRIMECORE Chain (4 layers)\n• Cross-jurisdictional ownership\n• Ultimate beneficiary: debarred contractor\n• Contract value: ₹230 Cr\n\n**Cluster 3** — TECHWISE Group (5 entities)\n• Incorporated within 2 weeks\n• Same CA office registration\n• Active contracts: ₹145 Cr\n\n🔗 Total shell entities identified: **23**`,
  `**Electoral Bond Correlation Analysis**\n\n📊 Key Findings:\n\n**INFRATECH SOLUTIONS PVT LTD**\n• Bond purchased: ₹12 Cr (Mar 2023)\n• Contract awarded: ₹450 Cr (Jun 2023)\n• Time gap: 3 months\n• Correlation strength: 76%\n\n**SAATHI INFRASTRUCTURE LTD**\n• Director served as party treasurer (2019-2022)\n• 8 contracts worth ₹670 Cr during tenure\n• State: Rajasthan (party-governed)\n• Correlation strength: 69%\n\n⚠️ *Bond correlations are temporal associations, not proof of quid pro quo. Independent investigation required.*`,
];

export default function ChatPage() {
  const { chatMessages, addChatMessage } = useStreamStore();
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [responseIndex, setResponseIndex] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleSend = (text?: string) => {
    const content = text || input.trim();
    if (!content) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    addChatMessage(userMsg);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: mockResponses[responseIndex % mockResponses.length],
        timestamp: new Date().toISOString(),
      };
      addChatMessage(botMsg);
      setResponseIndex((prev) => prev + 1);
      setIsTyping(false);
    }, 2000);
  };

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex items-center gap-1 border-b border-border pb-0 overflow-x-auto flex-shrink-0">
        <Link href="/dashboard" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Fraud Alerts</Link>
        <Link href="/dashboard/network" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Network Graph</Link>
        <Link href="/dashboard/bids" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Bid Analysis</Link>
        <Link href="/dashboard/timeline" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Timeline</Link>
        <span className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-accent-green tab-active whitespace-nowrap">AI Assistant</span>
      </div>

      <div className="flex-1 flex flex-col bg-surface border border-border rounded-2xl overflow-hidden min-h-0">
        <div className="px-6 py-4 border-b border-border flex items-center gap-3 flex-shrink-0">
          <div className="w-10 h-10 rounded-full bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center">
            <Bot size={20} className="text-accent-blue" />
          </div>
          <div>
            <h2 className="font-[var(--font-syne)] text-lg font-bold text-text">STREAM Intelligence Assistant</h2>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-accent-green pulse-live" />
              <span className="text-xs text-accent-green font-[var(--font-space-mono)]">Active · Analyzing 47 flags</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 min-h-0">
          {chatMessages.map((msg) => (
            <motion.div key={msg.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot size={14} className="text-accent-blue" />
                </div>
              )}
              <div className={`max-w-[75%] rounded-2xl px-5 py-4 ${msg.role === "user" ? "bg-accent-green/10 border border-accent-green/20 text-text" : "bg-surface2 border border-border text-text"}`}>
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                <p className="text-[10px] text-muted/50 mt-2 font-[var(--font-space-mono)]">{new Date(msg.timestamp).toLocaleTimeString()}</p>
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-accent-green/20 border border-accent-green/30 flex items-center justify-center flex-shrink-0 mt-1">
                  <User size={14} className="text-accent-green" />
                </div>
              )}
            </motion.div>
          ))}

          {isTyping && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center flex-shrink-0">
                <Bot size={14} className="text-accent-blue" />
              </div>
              <div className="bg-surface2 border border-border rounded-2xl px-5 py-4 flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-accent-blue typing-dot" />
                <div className="w-2 h-2 rounded-full bg-accent-blue typing-dot" />
                <div className="w-2 h-2 rounded-full bg-accent-blue typing-dot" />
                <span className="text-xs text-muted ml-2">Analyzing data...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {chatMessages.length <= 1 && (
          <div className="px-6 pb-3 flex flex-wrap gap-2 flex-shrink-0">
            {presetQueries.map((q, i) => (
              <motion.button key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + i * 0.1 }}
                onClick={() => handleSend(q.query)}
                className="flex items-center gap-2 text-xs bg-surface2 border border-border rounded-xl px-4 py-2.5 text-muted hover:text-text hover:border-accent-blue/30 transition-all"
              >
                {q.icon}
                <span className="font-[var(--font-syne)] font-semibold">{q.label}</span>
              </motion.button>
            ))}
          </div>
        )}

        <div className="p-4 border-t border-border flex-shrink-0">
          <div className="flex items-center gap-3">
            <input
              type="text" value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about vendors, procurement patterns, risk analysis..."
              className="flex-1 bg-bg border border-border rounded-xl px-4 py-3 text-sm text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-blue/30 font-[var(--font-space-mono)]"
            />
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => handleSend()} disabled={!input.trim() || isTyping}
              className="w-11 h-11 rounded-xl bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center text-accent-blue hover:bg-accent-blue/30 transition-all disabled:opacity-30"
            >
              <Send size={16} />
            </motion.button>
          </div>
          <p className="text-[10px] text-muted/40 mt-2 text-center font-[var(--font-space-mono)]">AI responses are analytical suggestions. All findings require independent verification.</p>
        </div>
      </div>
    </div>
  );
}
