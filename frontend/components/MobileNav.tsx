"use client";

import { useStreamStore } from "@/lib/store";
import { 
  AlertTriangle, Globe, Landmark, Link2, Zap, Menu,
  MessageSquare, LayoutDashboard, Network, BarChart3, Clock
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: '/dashboard', label: 'Alerts', icon: AlertTriangle },
  { href: '/dashboard/network', label: 'Network', icon: Network },
  { href: '/dashboard/bids', label: 'Bids', icon: BarChart3 },
  { href: '/dashboard/timeline', label: 'Timeline', icon: Clock },
  { href: '/dashboard/chat', label: 'Chat', icon: MessageSquare },
];

export default function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-surface/95 header-blur border-t border-border px-2 py-1">
      <div className="flex items-center justify-around">
        {navItems.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/dashboard' && pathname?.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-0.5 px-3 py-2 rounded-lg transition-all ${
                isActive ? 'text-accent-green' : 'text-muted'
              }`}
            >
              <Icon size={18} />
              <span className="text-[9px] font-[var(--font-syne)] font-semibold">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
