"use client";

import { useSession } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import RightPanel from "@/components/RightPanel";
import Header from "@/components/Header";
import ChatBot from "@/components/ChatBot";
import MobileNav from "@/components/MobileNav";
import { useStreamStore } from "@/lib/store";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, isPending } = useSession();
  const router = useRouter();
  const { isChatOpen, sidebarOpen } = useStreamStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isPending && !session) {
      // For dev/demo, don't redirect. In production uncomment:
      // router.push("/login");
    }
  }, [session, isPending, router]);

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin" />
          <p className="text-muted font-[var(--font-space-mono)] text-sm">Loading STREAM...</p>
        </div>
      </div>
    );
  }

  const user = session?.user || { name: "Nitheesh Kumar", email: "nitheesh@stream.gov.in" };

  return (
    <div className="min-h-screen flex flex-col">
      <Header user={user} />
      <MobileNav />

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Desktop */}
        <aside className="sidebar-desktop w-[260px] flex-shrink-0 border-r border-border bg-surface/50 overflow-y-auto h-[calc(100vh-64px)] sticky top-16 hidden lg:block">
          <Sidebar />
        </aside>

        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div className="lg:hidden fixed inset-0 z-50">
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => useStreamStore.getState().toggleSidebar()}
            />
            <aside className="absolute left-0 top-0 bottom-0 w-[280px] bg-surface border-r border-border overflow-y-auto">
              <Sidebar />
            </aside>
          </div>
        )}

        {/* Center Panel */}
        <main className="flex-1 overflow-y-auto h-[calc(100vh-64px)] p-4 md:p-6">
          {children}
        </main>

        {/* Right Panel - Desktop */}
        <aside className="hidden xl:block w-[320px] flex-shrink-0 border-l border-border bg-surface/50 overflow-y-auto h-[calc(100vh-64px)] sticky top-16">
          <RightPanel />
        </aside>
      </div>

      {isChatOpen && <ChatBot />}
    </div>
  );
}
