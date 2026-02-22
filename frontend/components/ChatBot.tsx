"use client";

import { useStreamStore } from "@/lib/store";
import { api } from "@/lib/api";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, Bot, User, Minimize2, Maximize2 } from "lucide-react";
import type { ChatMessage } from "@/lib/types";

const presetQuestions = [
  "Show me the top 5 riskiest vendors",
  "Analyze bid patterns for tender GEM/2024/B/4521897",
  "Find all shell company connections to INFRATECH",
  "Summarize electoral bond links in Tamil Nadu",
];

export default function ChatBot() {
  const { chatMessages, addChatMessage, toggleChat } = useStreamStore();
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    addChatMessage(userMsg);
    setInput("");
    setIsTyping(true);
    setStreamingMessage("");

    try {
      let fullResponse = '';

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
            // Add the final message to store
            const botMsg: ChatMessage = {
              id: (Date.now() + 1).toString(),
              role: 'assistant',
              content: fullResponse,
              timestamp: new Date().toISOString(),
            };
            addChatMessage(botMsg);
            setStreamingMessage("");
            setIsTyping(false);
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
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        className="fixed bottom-4 right-4 z-50 w-[380px] max-w-[calc(100vw-2rem)]"
      >
        <div className="bg-surface border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col" style={{ maxHeight: isMinimized ? '56px' : '520px' }}>
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-surface2 border-b border-border">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-accent-blue/20 flex items-center justify-center">
                <Bot size={16} className="text-accent-blue" />
              </div>
              <div>
                <p className="text-sm font-[var(--font-syne)] font-bold text-text">
                  STREAM Assistant
                </p>
                <div className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent-green" />
                  <span className="text-[10px] text-accent-green font-[var(--font-space-mono)]">
                    Online
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="text-muted hover:text-text p-1.5 transition-colors"
              >
                {isMinimized ? <Maximize2 size={14} /> : <Minimize2 size={14} />}
              </button>
              <button
                onClick={toggleChat}
                className="text-muted hover:text-accent-red p-1.5 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px]">
                {chatMessages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="w-6 h-6 rounded-full bg-accent-blue/20 flex items-center justify-center flex-shrink-0 mt-1">
                        <Bot size={12} className="text-accent-blue" />
                      </div>
                    )}
                    <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                      msg.role === 'user'
                        ? 'bg-accent-blue/20 text-text ml-auto'
                        : 'bg-surface2 text-text'
                    }`}>
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                    {msg.role === 'user' && (
                      <div className="w-6 h-6 rounded-full bg-accent-green/20 flex items-center justify-center flex-shrink-0 mt-1">
                        <User size={12} className="text-accent-green" />
                      </div>
                    )}
                  </motion.div>
                ))}

                {streamingMessage && (
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-2 justify-start"
                  >
                    <div className="w-6 h-6 rounded-full bg-accent-blue/20 flex items-center justify-center flex-shrink-0 mt-1">
                      <Bot size={12} className="text-accent-blue" />
                    </div>
                    <div className="max-w-[80%] rounded-xl px-3 py-2 text-sm bg-surface2 text-text">
                      <p className="whitespace-pre-wrap leading-relaxed">{streamingMessage}</p>
                    </div>
                  </motion.div>
                )}

                {isTyping && !streamingMessage && (
                  <div className="flex gap-2">
                    <div className="w-6 h-6 rounded-full bg-accent-blue/20 flex items-center justify-center flex-shrink-0">
                      <Bot size={12} className="text-accent-blue" />
                    </div>
                    <div className="bg-surface2 rounded-xl px-4 py-3 flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-muted typing-dot" />
                      <div className="w-2 h-2 rounded-full bg-muted typing-dot" />
                      <div className="w-2 h-2 rounded-full bg-muted typing-dot" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Preset Questions */}
              {chatMessages.length <= 1 && !streamingMessage && (
                <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                  {presetQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => { setInput(q); }}
                      className="text-[10px] bg-surface2 border border-border rounded-full px-3 py-1.5 text-muted hover:text-text hover:border-accent-blue/30 transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}

              {/* Input */}
              <div className="p-3 border-t border-border">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask about vendors, patterns, risks..."
                    className="flex-1 bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-blue/30 font-[var(--font-space-mono)]"
                  />
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleSend}
                    disabled={!input.trim()}
                    className="w-9 h-9 rounded-lg bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center text-accent-blue hover:bg-accent-blue/30 transition-all disabled:opacity-30"
                  >
                    <Send size={14} />
                  </motion.button>
                </div>
              </div>
            </>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
