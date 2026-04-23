"use client"

import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function SettingsPage() {
  const [activeTab, setActiveTab] = React.useState("general")
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
    } catch (error) {
      console.error("Failed to update webhooks:", error)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-primary">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Configure application parameters, detection logic, and system behavior.
        </p>
      </div>

      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab("general")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${activeTab === "general" ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"}`}
        >
          General
        </button>
        <button
          onClick={() => setActiveTab("detectors")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${activeTab === "detectors" ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"}`}
        >
          Detection Plugins
        </button>
        <button
          onClick={() => setActiveTab("system")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${activeTab === "system" ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"}`}
        >
          System State
        </button>
      </div>

      <div className="mt-6">
        {activeTab === "general" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Maintenance Window</CardTitle>
                <CardDescription>
                  Configure when background scanning operations should occur.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="start-time">Start Time</Label>
                    <Input id="start-time" type="time" defaultValue="02:00" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="end-time">End Time</Label>
                    <Input id="end-time" type="time" defaultValue="06:00" />
                  </div>
                </div>
                <Button className="mt-2">Save Window</Button>
              </CardContent>
            </Card>

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
        )}

        {activeTab === "detectors" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Active Detection Plugins</CardTitle>
                <CardDescription>
                  Enable or disable specific algorithms used during the scanning process.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="flex items-center justify-between p-6 border-b border-border">
                  <div className="space-y-0.5">
                    <Label className="text-base font-semibold text-primary">JpegInfo</Label>
                    <div className="text-sm text-muted-foreground">High-speed primary detector leveraging deep Huffman boundary scanning.</div>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between p-6 border-b border-border">
                  <div className="space-y-0.5">
                    <Label className="text-base font-semibold text-primary">Pillow Deep Scan</Label>
                    <div className="text-sm text-muted-foreground">Secondary consensus fallback verifying structural integrity by fully decompressing images into RAM.</div>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "system" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Database Stats</CardTitle>
                <CardDescription>
                  Overview of current library and SQLite status.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Total Indexed Files</div>
                    <div className="text-2xl font-bold mt-1">12,408</div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Corrupted Found</div>
                    <div className="text-2xl font-bold mt-1 text-destructive">2</div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="text-sm font-medium text-muted-foreground">DB Size</div>
                    <div className="text-2xl font-bold mt-1">4.2 MB</div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Last Scan</div>
                    <div className="text-2xl font-bold mt-1">2 hrs ago</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cache & Storage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button variant="destructive" className="w-full sm:w-auto">Clear Hashing Queue</Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
