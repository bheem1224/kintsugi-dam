"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Zap, Shield, Cloud, Brain, Info } from "lucide-react"

interface StepThreeProps {
  autoRestore: boolean
  setAutoRestore: (v: boolean) => void
  autoRestoreCloud: boolean
  setAutoRestoreCloud: (v: boolean) => void
  autoRestoreAI: boolean
  setAutoRestoreAI: (v: boolean) => void
  aiUseKintsugiCloud: boolean
  setAiUseKintsugiCloud: (v: boolean) => void
}

export function StepThree({
  autoRestore,
  setAutoRestore,
  autoRestoreCloud,
  setAutoRestoreCloud,
  autoRestoreAI,
  setAutoRestoreAI,
  aiUseKintsugiCloud,
  setAiUseKintsugiCloud,
}: StepThreeProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 p-4 rounded-xl border border-white/10 bg-white/5 transition-all hover:bg-white/10">
        <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
          <Shield className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold">Local Snapshots</span>
            <Badge variant="outline" className="text-[10px] uppercase tracking-wider">Free</Badge>
          </div>
          <p className="text-xs text-muted-foreground">Restore from local filesystem snapshots.</p>
        </div>
        <Switch checked={autoRestore} onCheckedChange={setAutoRestore} />
      </div>

      <div className="flex items-center gap-3 p-4 rounded-xl border border-white/10 bg-white/5 transition-all hover:bg-white/10 opacity-70 cursor-not-allowed">
        <div className="p-2 bg-purple-500/20 rounded-lg text-purple-400">
          <Cloud className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold">Cloud Backup</span>
            <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20 text-[10px] uppercase tracking-wider">Pro</Badge>
          </div>
          <p className="text-xs text-muted-foreground">Secure off-site recovery for catastrophic failure.</p>
        </div>
        <Switch checked={false} disabled />
      </div>

      <div className="flex flex-col gap-3 p-4 rounded-xl border border-white/10 bg-white/5 transition-all hover:bg-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/20 rounded-lg text-primary">
            <Brain className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold">Kintsugi-AI</span>
              <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] uppercase tracking-wider">Pro Plugin</Badge>
            </div>
            <p className="text-xs text-muted-foreground">AI-powered perceptual healing and reconstruction.</p>
          </div>
          <Switch checked={autoRestoreAI} onCheckedChange={setAutoRestoreAI} />
        </div>

        <AnimatePresence>
          {autoRestoreAI && (
            <motion.div
              initial={{ height: 0, opacity: 0, marginTop: 0 }}
              animate={{ height: "auto", opacity: 1, marginTop: 12 }}
              exit={{ height: 0, opacity: 0, marginTop: 0 }}
              className="overflow-hidden border-t border-white/10 pt-3"
            >
              <div className="flex items-center justify-between p-3 rounded-lg bg-black/40 border border-primary/10">
                <div className="space-y-0.5">
                  <Label className="text-xs font-medium">Use Kintsugi-Cloud API (Fallback)</Label>
                  <p className="text-[10px] text-muted-foreground">Cost: 1 Credit = 1 Photo Restored.</p>
                </div>
                <Switch size="sm" checked={aiUseKintsugiCloud} onCheckedChange={setAiUseKintsugiCloud} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
