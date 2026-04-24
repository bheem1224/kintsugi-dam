"use client"

import { useSystem } from "@/context/SystemContext"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"

export function Header() {
  const { stats } = useSystem();
  const { logout, isAuthenticated } = useAuth();

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6 shrink-0">
      <div className="font-bold text-xl text-primary">Kintsugi-DAM</div>
      <div className="flex items-center gap-4 text-sm font-medium text-muted-foreground">
        <div>Cloud Credits: {stats ? stats.cloud_credits.toLocaleString() : "..."}</div>
        {isAuthenticated && (
          <Button variant="ghost" size="icon" onClick={logout} title="Logout">
            <LogOut className="w-4 h-4" />
          </Button>
        )}
      </div>
    </header>
  );
}
