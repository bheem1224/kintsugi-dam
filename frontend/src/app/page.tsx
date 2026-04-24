"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useSystem } from "@/context/SystemContext"
import { CheckCircle, ShieldAlert, Cpu, Activity, Clock, HeartPulse, AlertTriangle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

export default function Dashboard() {
  const { stats, loading } = useSystem();
  const { toast } = useToast();
  const [toastShown, setToastShown] = React.useState(false);

  React.useEffect(() => {
    if (stats && !stats.watcher_active && !toastShown) {
      toast({
        title: "System Health Degraded",
        description: "The background real-time folder watcher is not running.",
        variant: "destructive"
      });
      setToastShown(true);
    }
  }, [stats, toastShown, toast]);

  if (loading || !stats) {
    return <div className="p-8">Loading dashboard...</div>
  }

  const isScanning = stats.current_scanner_state === "Scanning";
  const hasCorruption = stats.corrupted_files > 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          System overview and active monitoring status.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Hero Card */}
        <Card className="col-span-full md:col-span-2 lg:col-span-3 bg-gradient-to-br from-card to-black/60 relative overflow-hidden">
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
    </div>
  )
}
