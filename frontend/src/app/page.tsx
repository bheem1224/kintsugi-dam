"use client"

import * as React from "react"
import { useSystem } from "@/context/SystemContext"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  ShieldAlert, Bug, ShieldCheck,
  Cpu,
  CheckCircle,
  Activity,
  Clock,
  HeartPulse,
  AlertTriangle,
  FolderSearch,
  Database,
  Cloud,
  Wand2,
  HardDrive,
  FileWarning,
  Server,
  Zap,
  History,
  Timer
} from "lucide-react"


import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_scanned: 0,
    bit_rot_alerts: 0,
    remediation_deltas: 0,
    ttl_expirations: 0
  });

  useEffect(() => {
    fetch('/api/stats')
      .then(r => r.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  const { stats, loading } = useSystem()

  // MOCK DATA: Quadrant 1 (System Integrity Pool)
  const integrityPool = {
    totalStorage: "40 TB",
    scannedStorage: "14.2 TB",
    throughput: 142, // items/sec
    zfsSnapshotSafe: true,
  }

  // MOCK DATA: Quadrant 2 (Deep Core Audit / Telemetry)
  const auditTelemetry = {
    bitRotAlerts: 42,
    truncatedMedia: 15,
    corruptedExif: 8,
  }

  // MOCK DATA: Quadrant 3 (Remediation Deltas)
  const remediationDeltas = {
    zfsRestores: 1204,
    cloudFetches: 450,
    aiInfills: 89,
  }

  // MOCK DATA: Quadrant 4 (Retention Queue Clock)
  const retentionQueue = [
    { filename: "File_02.jpg", timeRemaining: "14h 22m", status: "critical" },
    { filename: "IMG_9043.CR2", timeRemaining: "1d 4h", status: "warning" },
    { filename: "backup_archive.zip", timeRemaining: "2d 12h", status: "normal" },
    { filename: "video_clip_01.mp4", timeRemaining: "5d 0h", status: "normal" },
  ]

  if (loading) {
    return <div className="p-8">Loading dashboard...</div>
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto h-full flex flex-col pb-safe">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white/90">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Real-time system telemetry and integrity pool status.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 grid-rows-2 gap-6 flex-1 min-h-[600px]">
        {/* Quadrant 1: System Integrity Pool */}
        <Card className="bg-card/50 backdrop-blur-md border-white/5 flex flex-col overflow-hidden relative">
          <div className="absolute -right-10 -top-10 opacity-5 pointer-events-none">
            <Database className="w-64 h-64" />
          </div>
          <CardHeader className="pb-4">
            <CardTitle className="text-xl flex items-center gap-2 text-white/80">
              <HardDrive className="w-5 h-5 text-primary" />
              System Integrity Pool
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-between">
            <div className="space-y-6">
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">Storage Capacity Scanned</p>
                <div className="flex items-end gap-2">
                  <span className="text-4xl font-bold text-white/90">{integrityPool.scannedStorage}</span>
                  <span className="text-xl text-muted-foreground pb-1">/ {integrityPool.totalStorage}</span>
                </div>
                {/* Progress bar mock */}
                <div className="w-full bg-white/5 h-2 mt-3 rounded-full overflow-hidden">
                  <div className="bg-primary h-full rounded-full" style={{ width: '35.5%' }}></div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                  <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><Zap className="w-3 h-3 text-yellow-500" /> Active Throughput</p>
                  <p className="text-2xl font-mono text-white/90">{integrityPool.throughput} <span className="text-sm text-muted-foreground">i/s</span></p>
                </div>
                <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                  <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><ShieldCheck className="w-3 h-3 text-emerald-500" /> ZFS Snapshot Cache</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${integrityPool.zfsSnapshotSafe ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className={`text-lg font-semibold ${integrityPool.zfsSnapshotSafe ? 'text-emerald-500' : 'text-red-500'}`}>
                      {integrityPool.zfsSnapshotSafe ? "SECURE" : "VULNERABLE"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quadrant 2: Deep Core Audit / Telemetry */}
        <Card className="bg-card/50 backdrop-blur-md border-white/5 flex flex-col overflow-hidden relative">
          <div className="absolute -right-10 -top-10 opacity-5 pointer-events-none">
            <Activity className="w-64 h-64" />
          </div>
          <CardHeader className="pb-4">
            <CardTitle className="text-xl flex items-center gap-2 text-white/80">
              <ShieldAlert className="w-5 h-5 text-destructive" />
              Deep Core Audit Telemetry
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-center gap-4">
            <div className="flex items-center justify-between p-4 bg-destructive/10 border border-destructive/20 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-destructive/20 rounded-lg">
                  <Bug className="w-6 h-6 text-destructive" />
                </div>
                <div>
                  <p className="font-semibold text-destructive">Bit-Rot Alerts</p>
                  <p className="text-xs text-destructive/70">Cryptographic hash mismatch</p>
                </div>
              </div>
              <span className="text-3xl font-bold text-destructive">{auditTelemetry.bitRotAlerts}</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-500/20 rounded-lg">
                  <FileWarning className="w-6 h-6 text-yellow-500" />
                </div>
                <div>
                  <p className="font-semibold text-yellow-500">Truncated Media</p>
                  <p className="text-xs text-yellow-500/70">Incomplete file payloads</p>
                </div>
              </div>
              <span className="text-3xl font-bold text-yellow-500">{auditTelemetry.truncatedMedia}</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-orange-500/10 border border-orange-500/20 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-orange-500" />
                </div>
                <div>
                  <p className="font-semibold text-orange-500">Corrupted EXIF/Headers</p>
                  <p className="text-xs text-orange-500/70">Malformed metadata</p>
                </div>
              </div>
              <span className="text-3xl font-bold text-orange-500">{auditTelemetry.corruptedExif}</span>
            </div>
          </CardContent>
        </Card>

        {/* Quadrant 3: Remediation Deltas */}
        <Card className="bg-card/50 backdrop-blur-md border-white/5 flex flex-col overflow-hidden relative">
          <div className="absolute -right-10 -top-10 opacity-5 pointer-events-none">
            <History className="w-64 h-64" />
          </div>
          <CardHeader className="pb-4">
            <CardTitle className="text-xl flex items-center gap-2 text-white/80">
              <CheckCircle className="w-5 h-5 text-primary" />
              Remediation Deltas
            </CardTitle>
            <CardDescription>Cumulative automated corrections</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex gap-4">
            <div className="flex-1 flex flex-col justify-center items-center p-4 bg-black/40 rounded-xl border border-white/5 text-center transition-colors hover:bg-white/5">
              <Server className="w-8 h-8 text-blue-400 mb-3" />
              <span className="text-3xl font-bold text-white/90">{remediationDeltas.zfsRestores.toLocaleString()}</span>
              <span className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">ZFS Restores</span>
            </div>
            <div className="flex-1 flex flex-col justify-center items-center p-4 bg-black/40 rounded-xl border border-white/5 text-center transition-colors hover:bg-white/5">
              <Cloud className="w-8 h-8 text-cyan-400 mb-3" />
              <span className="text-3xl font-bold text-white/90">{remediationDeltas.cloudFetches.toLocaleString()}</span>
              <span className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Cloud Fetches</span>
            </div>
            <div className="flex-1 flex flex-col justify-center items-center p-4 bg-black/40 rounded-xl border border-white/5 text-center transition-colors hover:bg-white/5">
              <Wand2 className="w-8 h-8 text-purple-400 mb-3" />
              <span className="text-3xl font-bold text-white/90">{remediationDeltas.aiInfills.toLocaleString()}</span>
              <span className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">AI Infills</span>
            </div>
          </CardContent>
        </Card>

        {/* Quadrant 4: Retention Queue Clock */}
        <Card className="bg-card/50 backdrop-blur-md border-white/5 flex flex-col overflow-hidden relative">
           <div className="absolute -right-10 -top-10 opacity-5 pointer-events-none">
            <Timer className="w-64 h-64" />
          </div>
          <CardHeader className="pb-4">
            <CardTitle className="text-xl flex items-center gap-2 text-white/80">
              <Clock className="w-5 h-5 text-orange-400" />
              Retention Queue Clock
            </CardTitle>
            <CardDescription>Items nearing automated pruning deadlines</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
             <div className="space-y-3 h-full overflow-y-auto pr-2 custom-scrollbar">
                {retentionQueue.map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-black/40 rounded-lg border border-white/5">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${
                        item.status === 'critical' ? 'bg-destructive animate-pulse' :
                        item.status === 'warning' ? 'bg-yellow-500' : 'bg-primary'
                      }`} />
                      <span className="text-sm font-medium text-white/80 truncate">{item.filename}</span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-muted-foreground">Pruning in</span>
                      <Badge variant="outline" className={`font-mono ${
                        item.status === 'critical' ? 'border-destructive text-destructive' :
                        item.status === 'warning' ? 'border-yellow-500 text-yellow-500' : 'border-white/20 text-muted-foreground'
                      }`}>
                        {item.timeRemaining}
                      </Badge>
                    </div>
                  </div>
                ))}
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
