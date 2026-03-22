"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useStreamStore } from "@/lib/store";
import { api } from "@/lib/api";
import { Send, Bot, User, Sparkles, AlertTriangle, TrendingUp, Search } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import Link from "next/link";

const presetQueries = [
  { icon: <Search size={14} />, label: "Top risky vendors", query: "Show me the top 5 riskiest vendors with their risk scores" },
  { icon: <AlertTriangle size={14} />, label: "Bid rigging patterns", query: "Analyze recent bid rigging patterns across all tenders" },
  { icon: <TrendingUp size={14} />, label: "Shell company links", query: "Map all shell company connections in the current dataset" },
  { icon: <Sparkles size={14} />, label: "Electoral bond analysis", query: "Summarize electoral bond correlations with contract awards" },
];

export default function ChatPage() {
  const { chatMessages, addChatMessage } = useStreamStore();
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, streamingMessage]);

  const handleSend = async (text?: string) => {
    const content = text || input.trim();
    if (!content || isTyping) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    addChatMessage(userMsg);
    setInput("");
    setIsTyping(true);
    setStreamingMessage("");

    try {
      let fullResponse = '';
      let messageAdded = false;

      await api.agent.chatStreamFetch(
        {
          messages: [...chatMessages, userMsg],
        },
        (event) => {
          if (event.type === 'token' && event.content) {
            fullResponse += event.content;
            setStreamingMessage(fullResponse);
          } else if (event.type === 'tool_start') {
            console.log(`Tool started: ${event.tool}`, event.input);
          } else if (event.type === 'tool_end') {
            console.log(`Tool completed: ${event.tool}`);
          } else if (event.type === 'done') {
            if (!messageAdded) {
              messageAdded = true;
              // Add the final message to store
              const botMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: fullResponse || "Sorry, no response was generated.",
                timestamp: new Date().toISOString(),
              };
              addChatMessage(botMsg);
              setStreamingMessage("");
              setIsTyping(false);
            }
          }
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };
      addChatMessage(errorMsg);
      setStreamingMessage("");
      setIsTyping(false);
    }
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

          {streamingMessage && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot size={14} className="text-accent-blue" />
              </div>
              <div className="max-w-[75%] rounded-2xl px-5 py-4 bg-surface2 border border-border text-text">
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{streamingMessage}</p>
                <p className="text-[10px] text-muted/50 mt-2 font-[var(--font-space-mono)]">{new Date().toLocaleTimeString()}</p>
              </div>
            </motion.div>
          )}

          {isTyping && !streamingMessage && (
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

        {chatMessages.length <= 1 && !streamingMessage && (
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
