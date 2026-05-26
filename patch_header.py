import re

with open("frontend/src/components/layout/Header.tsx", "r") as f:
    content = f.read()

imports_to_add = """
import { Bell } from "lucide-react"
import { useNotificationStore } from "@/store/useNotificationStore"
import { useNexusStream } from "@/hooks/useNexusStream"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
"""

content = content.replace('import { LogOut } from "lucide-react"', 'import { LogOut } from "lucide-react"\n' + imports_to_add)

hooks_to_add = """  const { token } = useAuth();
  useNexusStream(token);
  const { notifications, unreadCount, markAllAsRead, clearAll } = useNotificationStore();
  const unread = unreadCount();
"""

content = content.replace('  const { logout, isAuthenticated } = useAuth();', '  const { logout, isAuthenticated } = useAuth();\n' + hooks_to_add)

bell_component = """
        {isAuthenticated && (
          <Sheet onOpenChange={(open) => { if (open) markAllAsRead() }}>
            <SheetTrigger asChild>
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
        )}
"""

content = content.replace('{isAuthenticated && (', bell_component + '\n        {isAuthenticated && (')

with open("frontend/src/components/layout/Header.tsx", "w") as f:
    f.write(content)

print("Header patched")
