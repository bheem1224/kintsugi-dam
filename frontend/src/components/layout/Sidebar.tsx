"use client"
import React, { useState } from "react";

import Link from 'next/link';
import { useSystem } from "@/context/SystemContext"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { ProUpsellModal } from "@/components/modals/ProUpsellModal"
import { LogOut } from "lucide-react"
import { usePathname } from 'next/navigation';

export function Sidebar() {
  const { stats } = useSystem();
  const { logout, user } = useAuth();
  const pathname = usePathname();
  const [isUpsellOpen, setIsUpsellOpen] = useState(false);

  const isPro = user?.is_pro === true;

  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col p-4 shrink-0 justify-between h-full">
      <div>
        <div className="font-bold text-xl text-primary px-2 mb-6 tracking-tight">Kintsugi-DAM</div>
        <div className="font-semibold text-xs text-muted-foreground uppercase tracking-wider px-2 mb-2">Navigation</div>
        <nav className="flex flex-col space-y-1">
          <Link
            href="/"
            className={`px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            Dashboard
          </Link>
          <Link
            href="/browser"
            className={`px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/browser' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            File Browser
          </Link>
          <Link
            href="/triage"
            className={`px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/triage' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            Triage Gallery
          </Link>
          <Link
            href="/settings"
            className={`px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/settings' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            Settings
          </Link>
        </nav>
      </div>

      <div className="flex flex-col gap-4">
        {!isPro && (
          <div className="px-2">
            <Button
              className="w-full bg-primary/10 text-primary hover:bg-primary hover:text-black font-semibold border border-primary/20 transition-all"
              onClick={() => setIsUpsellOpen(true)}
            >
              Upgrade to Pro
            </Button>
          </div>
        )}

        <div className="bg-muted/30 rounded-lg p-3 border border-border flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Cloud Credits</span>
            <span className="text-xs font-bold text-primary">{stats ? stats.cloud_credits.toLocaleString() : "..."}</span>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-border">
            <div className="flex flex-col">
              <span className="text-sm font-semibold truncate max-w-[120px]">{user?.username || "Admin"}</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest">{isPro ? "Pro" : "Free Tier"}</span>
            </div>
            <Button variant="ghost" size="icon" onClick={logout} title="Logout" className="text-muted-foreground hover:text-destructive shrink-0">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
      {isUpsellOpen && (
        <ProUpsellModal
          featureName=""
          onClose={() => setIsUpsellOpen(false)}
        />
      )}
    </aside>
  );
}
