import { create } from 'zustand';
import type { ChatMessage } from './types';

interface StreamStore {
  // Alert Filters
  alertTypeFilter: string | null;
  setAlertTypeFilter: (type: string | null) => void;
  riskTierFilter: string | null;
  setRiskTierFilter: (tier: string | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;

  // Chat
  chatMessages: ChatMessage[];
  addChatMessage: (msg: ChatMessage) => void;
  isChatOpen: boolean;
  toggleChat: () => void;

  // Sidebar
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useStreamStore = create<StreamStore>((set) => ({
  alertTypeFilter: null,
  setAlertTypeFilter: (type) => set({ alertTypeFilter: type }),
  riskTierFilter: null,
  setRiskTierFilter: (tier) => set({ riskTierFilter: tier }),
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),

  chatMessages: [
    {
      id: '1',
      role: 'assistant',
      content:
        'Welcome to STREAM Intelligence Assistant. I can help you analyze procurement patterns, investigate vendor connections, and provide risk assessments. What would you like to investigate?',
      timestamp: new Date().toISOString(),
    },
  ],
  addChatMessage: (msg) =>
    set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  isChatOpen: false,
  toggleChat: () => set((s) => ({ isChatOpen: !s.isChatOpen })),

  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
