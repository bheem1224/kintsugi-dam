"use client"

import * as React from "react"
import { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { HardDrive, CheckCircle2, Activity } from "lucide-react"

interface StepPathsProps {
  mediaPath: string
  setMediaPath: (v: string) => void
  triagePath: string
  setTriagePath: (v: string) => void
  pathTestResults: any
  testPaths: () => void
  loading: boolean
}

export function StepPaths({
  mediaPath,
  setMediaPath,
  triagePath,
  setTriagePath,
  pathTestResults,
  testPaths,
  loading
}: StepPathsProps) {
  return (
    <>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><HardDrive className="w-5 h-5 text-primary"/> Step 2: Path Configuration</CardTitle>
        <CardDescription>Define where your assets live and where Kintsugi should quarantine issues.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4 p-4 bg-white/5 rounded-xl border border-white/10">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label htmlFor="mediaPath">Media Directory (Watch Folder)</Label>
              {pathTestResults?.media && (
                <span className={`text-xs flex items-center gap-1 ${pathTestResults.media.status === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
                  {pathTestResults.media.status === 'ok' ? <CheckCircle2 className="w-3 h-3"/> : "!"} {pathTestResults.media.message}
                </span>
              )}
            </div>
            <Input id="mediaPath" value={mediaPath} onChange={(e) => setMediaPath(e.target.value)} placeholder="/media" />
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Where your existing library is mounted</p>
          </div>

          <div className="space-y-2">
             <div className="flex justify-between items-center">
              <Label htmlFor="triagePath">Triage Directory (Quarantine)</Label>
              {pathTestResults?.triage && (
                <span className={`text-xs flex items-center gap-1 ${pathTestResults.triage.status === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
                  {pathTestResults.triage.status === 'ok' ? <CheckCircle2 className="w-3 h-3"/> : "!"} {pathTestResults.triage.message}
                </span>
              )}
            </div>
            <Input id="triagePath" value={triagePath} onChange={(e) => setTriagePath(e.target.value)} placeholder="/app/data/triage" />
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Where suspicious files are moved for review</p>
          </div>
        </div>

        <div className="flex justify-center">
          <Button variant="outline" size="sm" onClick={testPaths} disabled={loading} className="gap-2 border-primary/20 hover:bg-primary/10 transition-all hover:-translate-y-0.5">
            <Activity className="w-4 h-4" /> Test Paths & Permissions
          </Button>
        </div>
      </CardContent>
    </>
  )
}
