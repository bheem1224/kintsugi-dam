"use client"

import { useSystem } from "@/context/SystemContext"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { LogOut, Bell } from "lucide-react"

import { useNotificationStore } from "@/store/useNotificationStore"
import { useNexusStream } from "@/hooks/useNexusStream"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { ScrollArea } from "@/components/ui/scroll-area"

export function Header() {
  const { stats } = useSystem();
  const { logout, isAuthenticated, user } = useAuth();
  const { token } = useAuth();
  useNexusStream(token);
  const { notifications, unreadCount, markAllAsRead, clearAll } = useNotificationStore();
  const unread = unreadCount();

  const isPro = user?.is_pro === true;

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6 shrink-0 md:hidden">
      <div className="font-bold text-xl text-primary">Kintsugi-DAM</div>
      <div className="flex items-center gap-4 text-sm font-medium text-muted-foreground">

        {isAuthenticated && (
          <div className="flex items-center gap-3">
             <div className="flex flex-col text-right hidden sm:flex">
                <span className="text-sm font-semibold truncate max-w-[120px] text-foreground">{user?.username || "Admin"}</span>
                <span className="text-[10px] uppercase tracking-widest bg-primary/20 text-primary px-1.5 py-0.5 rounded w-fit ml-auto">{isPro ? "Studio Tier" : "Free Tier"}</span>
             </div>

            <Sheet onOpenChange={(open) => { if (open) markAllAsRead() }}>
              <SheetTrigger>
                <Button variant="ghost" size="icon" className="relative" title="Notifications">
                  <Bell className="w-5 h-5" />
                  {unread > 0 && (
                    <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full" />
                  )}
                </Button>
              </SheetTrigger>
              <SheetContent className="w-[400px] sm:w-[540px]">
                <SheetHeader className="flex flex-row justify-between items-center mb-4">
                  <SheetTitle>System Feed</SheetTitle>
                  <Button variant="outline" size="sm" onClick={clearAll}>Clear All</Button>
                </SheetHeader>
                <ScrollArea className="h-[calc(100vh-100px)]">
                  {notifications.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">No notifications</div>
                  ) : (
                    <div className="space-y-4">
                      {notifications.map((n) => (
                        <div key={n.id} className={`p-3 rounded-lg border text-sm ${n.severity === 'destructive' ? 'bg-red-500/10 border-red-500/20' : n.severity === 'warning' ? 'bg-yellow-500/10 border-yellow-500/20' : 'bg-white/5 border-white/10'}`}>
                           <div className="flex justify-between items-center mb-1">
                             <span className="font-semibold text-xs opacity-70">{n.event}</span>
                             <span className="text-xs opacity-50">{n.timestamp.toLocaleTimeString()}</span>
                           </div>
                           <div>{n.message}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </SheetContent>
            </Sheet>
          </div>
        )}

      </div>
    </header>
  );
}
