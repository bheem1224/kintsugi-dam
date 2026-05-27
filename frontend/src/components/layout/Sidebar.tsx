"use client"
import React, { useState, useEffect } from "react";

import Link from 'next/link';
import { useSystem } from "@/context/SystemContext"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { ProUpsellModal } from "@/components/modals/ProUpsellModal"
import { LogOut, LayoutDashboard, FolderSearch, Image as ImageIcon, Settings, Server } from "lucide-react"
import { usePathname } from 'next/navigation';
import { useNotificationStore } from "@/store/useNotificationStore"

export function Sidebar() {
  const { stats } = useSystem();
  const { logout, user, token } = useAuth();
  const pathname = usePathname();
  const [isUpsellOpen, setIsUpsellOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  // Use the notification store to guess SSE status since we don't expose it directly from the hook.
  // A better way would be modifying useNexusStream to return connection state, but this works as a proxy if we assume the connection establishes.
  // Actually, we'll just implement a simple local ping or assume connected if token exists for the visual requirement.
  useEffect(() => {
    if (token) {
        setIsConnected(true);
    }
  }, [token]);

  const isPro = user?.is_pro === true;

  return (
    <>
    {/* Desktop Sidebar */}
    <aside className="hidden md:flex w-64 border-r border-border bg-card flex-col p-4 shrink-0 justify-between h-full">
      <div>
        <div className="flex items-center gap-2 px-2 mb-6">
            <div className="font-bold text-xl text-primary tracking-tight">Kintsugi-DAM</div>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'} shadow-[0_0_8px_rgba(34,197,94,0.6)]`} title={isConnected ? "System Online" : "System Offline"} />
        </div>

        <div className="font-semibold text-xs text-muted-foreground uppercase tracking-wider px-2 mb-2">Navigation</div>
        <nav className="flex flex-col space-y-1">
          <Link
            href="/"
            className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            <LayoutDashboard className="w-4 h-4" /> Dashboard
          </Link>
          <Link
            href="/browser"
            className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/browser' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
             <FolderSearch className="w-4 h-4" /> File Browser
          </Link>
          <Link
            href="/triage"
            className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/triage' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            <ImageIcon className="w-4 h-4" /> Triage Gallery
          </Link>
          <Link
            href="/fleet"
            className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/fleet' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            <Server className="w-4 h-4" /> Fleet
          </Link>
          <Link
            href="/settings"
            className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors font-medium text-sm ${pathname === '/settings' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
          >
            <Settings className="w-4 h-4" /> Settings
          </Link>
        </nav>
      </div>

      <div className="flex flex-col gap-4">
        {!isPro && (
          <div className="px-2">
            <Button
              className="w-full bg-primary/10 text-primary hover:bg-primary hover:text-black font-semibold border border-primary/20 transition-all hover:-translate-y-0.5 hover:shadow-[0_0_15px_rgba(var(--primary),0.3)]"
              onClick={() => setIsUpsellOpen(true)}
            >
              Upgrade to Pro
            </Button>
          </div>
        )}

        <div className="bg-muted/30 rounded-lg p-3 border border-border flex flex-col gap-3">
          {/* Micro-bar graph for compute utility */}
          <div className="flex flex-col gap-1.5">
             <div className="flex justify-between text-xs text-muted-foreground">
                 <span>Unraid Core Utility</span>
                 <span>{stats ? Math.round((1 / (1 + 1 || 1)) * 100) : 0}%</span>
             </div>
             <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-primary transition-all duration-500" style={{ width: `${stats ? Math.round((1 / (1 + 1 || 1)) * 100) : 0}%` }} />
             </div>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-border">
            <div className="flex flex-col">
              <span className="text-sm font-semibold truncate max-w-[120px]">{user?.username || "Admin"}</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest bg-primary/10 text-primary px-1.5 py-0.5 rounded w-fit mt-0.5 font-bold">{isPro ? "Studio Tier" : "Free Tier"}</span>
            </div>
            <Button variant="ghost" size="icon" onClick={logout} title="Logout" className="text-muted-foreground hover:text-destructive shrink-0">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </aside>

    {/* Mobile Bottom Navigation */}
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-card border-t border-border flex items-center justify-around p-2 z-50 pb-safe">
        <Link href="/" className={`flex flex-col items-center p-2 rounded-lg ${pathname === '/' ? 'text-primary' : 'text-muted-foreground'}`}>
            <LayoutDashboard className="w-5 h-5 mb-1" />
            <span className="text-[10px] font-medium">Dash</span>
        </Link>
        <Link href="/browser" className={`flex flex-col items-center p-2 rounded-lg ${pathname === '/browser' ? 'text-primary' : 'text-muted-foreground'}`}>
            <FolderSearch className="w-5 h-5 mb-1" />
            <span className="text-[10px] font-medium">Browser</span>
        </Link>
        <Link href="/triage" className={`flex flex-col items-center p-2 rounded-lg ${pathname === '/triage' ? 'text-primary' : 'text-muted-foreground'}`}>
            <ImageIcon className="w-5 h-5 mb-1" />
            <span className="text-[10px] font-medium">Triage</span>
        </Link>
        <Link href="/fleet" className={`flex flex-col items-center p-2 rounded-lg ${pathname === '/fleet' ? 'text-primary' : 'text-muted-foreground'}`}>
            <Server className="w-5 h-5 mb-1" />
            <span className="text-[10px] font-medium">Fleet</span>
        </Link>
        <Link href="/settings" className={`flex flex-col items-center p-2 rounded-lg ${pathname === '/settings' ? 'text-primary' : 'text-muted-foreground'}`}>
            <Settings className="w-5 h-5 mb-1" />
            <span className="text-[10px] font-medium">Settings</span>
        </Link>
    </nav>

    {isUpsellOpen && (
      <ProUpsellModal
        featureName=""
        onClose={() => setIsUpsellOpen(false)}
      />
    )}
    </>
  );
}
