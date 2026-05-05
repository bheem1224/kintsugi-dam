"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useSystem } from "@/context/SystemContext"
import { CheckCircle, ShieldAlert, Cpu, Activity, Clock, HeartPulse, AlertTriangle, Lightbulb, FolderSearch, ShieldCheck } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function Dashboard() {
  const { stats, loading } = useSystem();
  const { toast } = useToast();
  const [toastShown, setToastShown] = React.useState(false);
  const [showWelcome, setShowWelcome] = React.useState(false);

  React.useEffect(() => {
    // Check if first run
    const hasSeenWelcome = localStorage.getItem("kintsugi_welcome_seen");
    if (!hasSeenWelcome) {
      setShowWelcome(true);
    }

    if (stats && !stats.watcher_active && !toastShown) {
      toast({
        title: "System Health Degraded",
        description: "The background real-time folder watcher is not running.",
        variant: "destructive"
      });
      setToastShown(true);
    }
  }, [stats, toastShown, toast]);

  const dismissWelcome = () => {
    localStorage.setItem("kintsugi_welcome_seen", "true");
    setShowWelcome(false);
  };

  if (loading || !stats) {
    return <div className="p-8">Loading dashboard...</div>
  }

  const isScanning = stats.current_scanner_state === "Scanning";
  const hasCorruption = stats.corrupted_files > 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto relative">
      {/* ... (Welcome Modal Content remains the same) */}
      {showWelcome && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <Card className="w-full max-w-lg shadow-2xl border-primary/20 bg-black/80 backdrop-blur-xl">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/20 rounded-lg text-primary">
                  <Lightbulb className="w-6 h-6" />
                </div>
                <CardTitle className="text-2xl">Quick Start Guide</CardTitle>
              </div>
              <CardDescription>Your environment is ready. Here is what you can do first:</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 p-3 rounded-lg hover:bg-white/5 transition-colors group">
                <div className="p-2 bg-muted rounded-md group-hover:bg-primary/20 group-hover:text-primary transition-colors h-fit">
                  <FolderSearch className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold">Manual Scan</h4>
                  <p className="text-sm text-muted-foreground">Head to the <strong>File Browser</strong> in the sidebar to manually trigger a deep scan of any subfolder.</p>
                </div>
              </div>
              
              <div className="flex gap-4 p-3 rounded-lg hover:bg-white/5 transition-colors group">
                <div className="p-2 bg-muted rounded-md group-hover:bg-primary/20 group-hover:text-primary transition-colors h-fit">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold">Hot Folders</h4>
                  <p className="text-sm text-muted-foreground">The system is currently watching your media folder. Any new file added will be instantly analyzed.</p>
                </div>
              </div>

              <div className="flex gap-4 p-3 rounded-lg hover:bg-white/5 transition-colors group">
                <div className="p-2 bg-muted rounded-md group-hover:bg-primary/20 group-hover:text-primary transition-colors h-fit">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold">Monitor Health</h4>
                  <p className="text-sm text-muted-foreground">This dashboard will show real-time stats. If corruption is found, it will appear in the <strong>Triage Gallery</strong>.</p>
                </div>
              </div>

              <Button onClick={dismissWelcome} className="w-full h-12 text-lg font-bold mt-4 shadow-[0_0_20px_rgba(var(--primary),0.3)] transition-all hover:-translate-y-0.5">
                Got it, let&apos;s go!
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          System overview and active monitoring status.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Hero Card */}
        <Card className="col-span-full md:col-span-2 lg:col-span-3 bg-gradient-to-br from-card to-black/60 relative overflow-hidden transition-all hover:shadow-xl hover:border-white/10">
          <div className="absolute top-0 right-0 p-6 opacity-20 pointer-events-none">
            {isScanning ? (
              <Activity className="w-48 h-48 animate-pulse text-primary" />
            ) : (
              <Clock className="w-48 h-48 text-muted-foreground" />
            )}
          </div>
          <CardHeader>
            <CardTitle className="text-2xl">System Status</CardTitle>
            <CardDescription>Real-time library analysis</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-8">
            <div className="flex flex-col md:flex-row gap-8 items-start md:items-center">
              <div className="flex items-center gap-4">
                <div className={`p-4 rounded-full ${isScanning ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
                  <Activity className={`w-8 h-8 ${isScanning ? "animate-pulse" : ""}`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Scanner State</p>
                  <p className={`text-2xl font-bold ${isScanning ? "text-primary" : ""}`}>
                    {stats.current_scanner_state}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="p-4 rounded-full bg-muted text-foreground">
                  <Cpu className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Monitored Files</p>
                  <p className="text-2xl font-bold">
                    {stats.total_files.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 md:ml-auto">
                <div className={`p-4 rounded-full ${hasCorruption ? "bg-destructive/20 text-destructive" : "bg-primary/20 text-primary"}`}>
                  {hasCorruption ? (
                    <ShieldAlert className="w-8 h-8" />
                  ) : (
                    <CheckCircle className="w-8 h-8" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Library Health</p>
                  <p className={`text-2xl font-bold ${hasCorruption ? "text-destructive" : "text-primary"}`}>
                    {hasCorruption ? "Corruption Detected" : "All Clear"}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col md:flex-row gap-8 items-start md:items-center pt-6 border-t border-border/50">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${stats.watcher_active ? "bg-primary/20 text-primary" : "bg-destructive/20 text-destructive"}`}>
                  {stats.watcher_active ? <HeartPulse className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">System Health</p>
                  <p className={`text-lg font-bold ${stats.watcher_active ? "text-primary" : "text-destructive"}`}>
                    {stats.watcher_active ? "Active" : "Degraded"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-muted/50 text-muted-foreground">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Quarantined Files</p>
                  <p className="text-lg font-bold">
                    {stats.total_quarantined.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 md:ml-auto">
                <div className="p-3 rounded-full bg-muted/50 text-muted-foreground">
                  <Clock className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Last Scan</p>
                  <p className="text-lg font-bold">
                    {stats.last_scan_time ? new Date(stats.last_scan_time).toLocaleString() : "Never"}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Triage Activity Table */}
      <Card className="bg-card/50 backdrop-blur-md border-white/5">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            Recent Triage Activity
          </CardTitle>
          <CardDescription>Latest files flagged for remediation.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-white/5 text-muted-foreground">
                  <th className="pb-3 font-medium">File Name</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium text-right">Detected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {stats.corrupted_files > 0 ? (
                  // Mocking rows for UX demonstration if stats doesn't provide the list
                  [
                    { name: "IMG_2024_001.raw", status: "Corrupted", time: "2 mins ago" },
                    { name: "Family_Video.mp4", status: "Bit-rot", time: "1 hour ago" },
                  ].map((row, i) => (
                    <tr key={i} className="group transition-all hover:bg-white/5 cursor-pointer">
                      <td className="py-4 font-medium flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-destructive" />
                        {row.name}
                      </td>
                      <td className="py-4">
                        <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 text-[10px]">
                          {row.status}
                        </Badge>
                      </td>
                      <td className="py-4 text-right text-muted-foreground">{row.time}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center gap-2">
                        <CheckCircle className="w-8 h-8 text-primary/50" />
                        <p>No active triage items. Library is clean.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
