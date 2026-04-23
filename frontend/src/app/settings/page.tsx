"use client"

import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function SettingsPage() {
  const [webhookUrls, setWebhookUrls] = React.useState({
    discord: "",
    ntfy: ""
  })
  const [saving, setSaving] = React.useState(false)

  const handleWebhookSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/settings/webhooks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          discord_webhook_url: webhookUrls.discord || null,
          ntfy_topic_url: webhookUrls.ntfy || null
        })
      })
      // Could show a toast here in the future
    } catch (error) {
      console.error("Failed to update webhooks:", error)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Configure detection algorithms and notification settings.
        </p>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold tracking-tight">Active Detectors</h2>
        <Card>
          <CardContent className="p-0">
            <div className="flex items-center justify-between p-6 border-b">
              <div className="space-y-0.5">
                <Label className="text-base">ImageMagick (identify)</Label>
                <div className="text-sm text-muted-foreground">Standard structural validation for images</div>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between p-6 border-b">
              <div className="space-y-0.5">
                <Label className="text-base">jpeginfo</Label>
                <div className="text-sm text-muted-foreground">Deep Huffman boundary scanning</div>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between p-6">
              <div className="space-y-0.5">
                <Label className="text-base">Local AI Detector (ONNX)</Label>
                <div className="text-sm text-muted-foreground">Heuristic analysis for visual glitching</div>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold tracking-tight">Active Backup Providers</h2>
        <Card>
          <CardContent className="p-0">
            <div className="flex items-center justify-between p-6 border-b">
              <div className="space-y-0.5">
                <Label className="text-base">ZFS Snapshots</Label>
                <div className="text-sm text-muted-foreground">Local network storage</div>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between p-6">
              <div className="space-y-0.5">
                <Label className="text-base">Cloud AI Repair</Label>
                <div className="text-sm text-muted-foreground">Reconstruct corrupted payload using Context Match</div>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold tracking-tight">System Settings</h2>
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Receive alerts when corrupted files are detected in your library.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleWebhookSubmit} className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="discord">Discord Webhook URL</Label>
                <Input 
                  id="discord" 
                  placeholder="https://discord.com/api/webhooks/..." 
                  value={webhookUrls.discord}
                  onChange={(e) => setWebhookUrls({...webhookUrls, discord: e.target.value})}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="ntfy">Ntfy Topic URL</Label>
                <Input 
                  id="ntfy" 
                  placeholder="https://ntfy.sh/mytopic" 
                  value={webhookUrls.ntfy}
                  onChange={(e) => setWebhookUrls({...webhookUrls, ntfy: e.target.value})}
                />
              </div>
              <Button type="submit" disabled={saving}>
                {saving ? "Saving..." : "Save Settings"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
