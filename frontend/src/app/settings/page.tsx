"use client"
import { ProUpsellModal } from "@/components/modals/ProUpsellModal"

import * as React from "react"
import { useDebounce } from "use-debounce"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useSystem } from "@/context/SystemContext"
import { useAuth } from "@/context/AuthContext"
import { useToast } from "@/hooks/use-toast"

import { Plus } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

export default function SettingsPage() {
  const { stats, refreshStats } = useSystem()
  const { user } = useAuth()
  const { token } = useAuth()
  const { toast } = useToast()
  const [activeTab, setActiveTab] = React.useState("general")
  const [saving, setSaving] = React.useState(false)

  // Form states
  const [maintenanceStart, setMaintenanceStart] = React.useState("01:00")
  const [maintenanceEnd, setMaintenanceEnd] = React.useState("05:00")
  const [monitoredDirectory, setMonitoredDirectory] = React.useState("/media")
  const [snapshotPath, setSnapshotPath] = React.useState("/snapshots")
  const [autoRestore, setAutoRestore] = React.useState(false)
  const [autoRestoreCloud, setAutoRestoreCloud] = React.useState(false)
  const [autoRestoreAI, setAutoRestoreAI] = React.useState(false)
  const [autoRepair, setAutoRepair] = React.useState(false)
  const [aiUseKintsugiCloud, setAiUseKintsugiCloud] = React.useState(true)
  const [upsellFeature, setUpsellFeature] = React.useState("")
  const [showUpsellModal, setShowUpsellModal] = React.useState(false)
  const [retentionDays, setRetentionDays] = React.useState("90")
  const [webhookUrls, setWebhookUrls] = React.useState({
    discord: "",
    ntfy: ""
  })
  const [plugins, setPlugins] = React.useState<Record<string, { is_enabled: boolean }>>({})


  // Fetch initial settings
  const [debouncedMaintenanceStart] = useDebounce(maintenanceStart, 2000)
  const [debouncedMaintenanceEnd] = useDebounce(maintenanceEnd, 2000)
  const [debouncedMonitoredDirectory] = useDebounce(monitoredDirectory, 2000)
  const [debouncedSnapshotPath] = useDebounce(snapshotPath, 2000)
  const [debouncedRetentionDays] = useDebounce(retentionDays, 2000)
  const [debouncedWebhookUrls] = useDebounce(webhookUrls, 2000)

  // Track if initial load is done so we don't overwrite settings immediately
  const [initialLoadDone, setInitialLoadDone] = React.useState(false)

  React.useEffect(() => {
    async function fetchSettings() {
      try {
        if (!token) return;
        const res = await fetch(`/api/settings`, {
          credentials: "include",
        headers: {
            "Authorization": `Bearer ${token}`
          }
        })
        if (res.ok) {
          const data = await res.json()
          if (data.settings) {
            setMaintenanceStart(data.settings.maintenance_start || "02:00")
            setMaintenanceEnd(data.settings.maintenance_end || "06:00")
            setMonitoredDirectory(data.settings.monitored_directory || "/media")
            setSnapshotPath(data.settings.snapshot_mount_path || "/snapshots")
            setAutoRestore(data.settings.auto_restore || false)
            setAutoRestoreCloud(data.settings.auto_restore_cloud || false)
            setAutoRestoreAI(data.settings.auto_restore_ai || false)
            setAiUseKintsugiCloud(data.settings.ai_use_kintsugi_cloud ?? true)
            setRetentionDays(data.settings.retention_days?.toString() || "90")
            setWebhookUrls({
              discord: data.settings.discord_webhook_url || "",
              ntfy: data.settings.ntfy_topic_url || ""
            })
          }
          if (data.plugins) {
            const formattedPlugins: Record<string, { is_enabled: boolean }> = {};
            for (const [key, value] of Object.entries(data.plugins)) {
              if (typeof value === 'boolean') {
                formattedPlugins[key] = { is_enabled: value };
              } else {
                formattedPlugins[key] = value as { is_enabled: boolean };
              }
            }
            setPlugins(formattedPlugins)
          }
          setInitialLoadDone(true)
        }
      } catch (error) {
        console.error("Failed to fetch settings:", error)
      }
    }
    fetchSettings()
  }, [token])

  React.useEffect(() => {
    if (!initialLoadDone) return;
    handleSaveSettings();
  }, [debouncedMaintenanceStart, debouncedMaintenanceEnd, debouncedMonitoredDirectory, debouncedSnapshotPath, autoRestore, autoRepair, debouncedRetentionDays, debouncedWebhookUrls, plugins])

  const handleSaveSettings = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setSaving(true)

    try {
      await fetch(`/api/settings`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({
          maintenance_start: maintenanceStart,
          maintenance_end: maintenanceEnd,
          monitored_directory: monitoredDirectory,
          snapshot_mount_path: snapshotPath,
          auto_restore: autoRestore,
          auto_restore_cloud: autoRestoreCloud,
          auto_restore_ai: autoRestoreAI,
          ai_use_kintsugi_cloud: aiUseKintsugiCloud,
          retention_days: parseInt(retentionDays, 10),
          discord_webhook_url: webhookUrls.discord || null,
          ntfy_topic_url: webhookUrls.ntfy || null,
          plugins: plugins
        })
      })
      // Refresh system stats after save just in case
      await refreshStats()
    } catch (error) {
      console.error("Failed to update settings:", error)
    } finally {
      setSaving(false)
    }
  }

  const togglePlugin = (name: string) => {
    const currentPlugin = plugins[name] || { is_enabled: false };
    const updatedPlugins = {
      ...plugins,
      [name]: { ...currentPlugin, is_enabled: !currentPlugin.is_enabled }
    }
    setPlugins(updatedPlugins)

    // Auto-save plugins when toggled
    fetch(`/api/settings`, {
      method: "POST",
      credentials: "include",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ plugins: updatedPlugins })
    }).catch(console.error)
  }

  const isPro = user?.is_pro === true

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
                <CardTitle>Library Configuration</CardTitle>
                <CardDescription>
                  Configure the root directory to monitor for file corruption.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="monitored-directory">Monitored Directory</Label>
                  <Input
                    id="monitored-directory"
                    value={monitoredDirectory}
                    onChange={(e) => setMonitoredDirectory(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Free Tier is limited to a single root directory. Tip: Use Docker volume mounts to map multiple external folders into this single /media path.
                  </p>
                </div>
                <div className="flex items-center gap-4">

                  {!isPro ? (
                    <TooltipProvider delay={100}>
                      <Tooltip>
                        <TooltipTrigger>
                          <span className="inline-block cursor-not-allowed">
                            <Button variant="outline" disabled className="pointer-events-none">
                              <Plus className="w-4 h-4 mr-2" />
                              Add Another Monitored Directory
                            </Button>
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Available with Kintsugi Pro.</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ) : (
                    <Button variant="outline">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Another Monitored Directory
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

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
                    <Input
                      id="start-time"
                      type="time"
                      value={maintenanceStart}
                      onChange={(e) => setMaintenanceStart(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="end-time">End Time</Label>
                    <Input
                      id="end-time"
                      type="time"
                      value={maintenanceEnd}
                      onChange={(e) => setMaintenanceEnd(e.target.value)}
                    />
                  </div>
                </div>

              </CardContent>
            </Card>


            <Card>
              <CardHeader>
                <CardTitle>Triage & Remediation</CardTitle>
                <CardDescription>
                  Configure automated repairs and snapshot retrieval behavior.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="snapshot-path">Snapshot Mount Path</Label>
                  <Input
                    id="snapshot-path"
                    value={snapshotPath}
                    onChange={(e) => setSnapshotPath(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    The root directory where your read-only ZFS/BTRFS snapshots are mounted.
                  </p>
                </div>

                <div className="flex items-center justify-between py-2">
                  <div className="space-y-0.5">
                    <Label htmlFor="auto-restore" className="text-base cursor-pointer">Auto-Restore from Snapshots</Label>
                    <p className="text-sm text-muted-foreground">Automatically overwrite corrupted files in the live directory if a clean snapshot is found.</p>
                  </div>
                  {!isPro ? (
                    <TooltipProvider delay={100}>
                      <Tooltip>
                        <TooltipTrigger>
                          <span className="inline-block cursor-not-allowed">
                            <Switch checked={false} disabled className="pointer-events-none" />
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Available with Kintsugi Pro.</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ) : (
                    <Switch
                      id="auto-restore"
                      checked={autoRestore}
                      onCheckedChange={setAutoRestore}
                    />
                  )}
                </div>

                <div className="flex items-center justify-between py-2">
                  <div className="space-y-0.5">
                    <Label htmlFor="auto-repair" className="text-base cursor-pointer">Auto-Repair with AI</Label>
                    <p className="text-sm text-muted-foreground">Automatically send irrecoverable files to the Cloud Gateway for AI reconstruction (consumes credits).</p>
                  </div>
                  {!isPro ? (
                    <TooltipProvider delay={100}>
                      <Tooltip>
                        <TooltipTrigger>
                          <span className="inline-block cursor-not-allowed">
                            <Switch checked={false} disabled className="pointer-events-none" />
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Available with Kintsugi Pro.</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ) : (
                    <Switch
                      id="auto-repair"
                      checked={autoRepair}
                      onCheckedChange={setAutoRepair}
                    />
                  )}
                </div>

                <div className="space-y-4 py-2">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <Label className="text-base">Auto-Restore with AI</Label>
                        {!user?.is_pro && <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">Pro</span>}
                      </div>
                      <p className="text-sm text-muted-foreground">Automatically reconstruct irrecoverable files using AI models.</p>
                    </div>
                    <Switch
                      checked={autoRestoreAI}
                      onCheckedChange={(checked) => {
                        if (!user?.is_pro) {
                          setUpsellFeature("Auto-Restore with AI");
                          setShowUpsellModal(true);
                          return;
                        }
                        setAutoRestoreAI(checked);
                      }}
                    />
                  </div>

                  {autoRestoreAI && (
                    <div className="ml-6 pl-4 border-l-2 border-border space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label className="text-sm">Use Kintsugi Cloud AI</Label>
                          <p className="text-xs text-muted-foreground">Offloads processing to high-performance cloud models (consumes credits). If disabled, uses local AI plugins.</p>
                        </div>
                        <Switch
                          checked={aiUseKintsugiCloud}
                          onCheckedChange={setAiUseKintsugiCloud}
                          disabled={!user?.is_pro}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-2 pt-2">
                  <Label htmlFor="retention">Triage Retention Period (Days)</Label>
                  <Input
                    id="retention"
                    type="number"
                    value={retentionDays}
                    onChange={(e) => setRetentionDays(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Corrupted files and manual review snapshots are permanently deleted from the Triage Bin after this period.
                  </p>
                </div>


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
                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="discord">Discord Webhook URL</Label>
                    <Input
                      id="discord"
                      placeholder="https://discord.com/api/webhooks/..."
                      value={webhookUrls.discord}
                      onChange={(e) => setWebhookUrls({ ...webhookUrls, discord: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ntfy">Ntfy Topic URL</Label>
                    <Input
                      id="ntfy"
                      placeholder="https://ntfy.sh/mytopic"
                      value={webhookUrls.ntfy}
                      onChange={(e) => setWebhookUrls({ ...webhookUrls, ntfy: e.target.value })}
                    />
                  </div>

                </div>
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
                  <Switch
                    checked={plugins["JpegInfo"]?.is_enabled ?? false}
                    onCheckedChange={() => togglePlugin("JpegInfo")}
                  />
                </div>
                <div className="flex items-center justify-between p-6 border-b border-border">
                  <div className="space-y-0.5">
                    <Label className="text-base font-semibold text-primary">Pillow Deep Scan</Label>
                    <div className="text-sm text-muted-foreground">Secondary consensus fallback verifying structural integrity by fully decompressing images into RAM.</div>
                  </div>
                  <Switch
                    checked={plugins["Pillow Deep Scan"]?.is_enabled ?? false}
                    onCheckedChange={() => togglePlugin("Pillow Deep Scan")}
                  />
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
                    <div className="text-2xl font-bold mt-1">
                      {stats ? stats.total_files.toLocaleString() : "..."}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Corrupted Found</div>
                    <div className={`text-2xl font-bold mt-1 ${stats && stats.corrupted_files > 0 ? "text-destructive" : ""}`}>
                      {stats ? stats.corrupted_files.toLocaleString() : "..."}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Scanner State</div>
                    <div className={`text-2xl font-bold mt-1 ${stats && stats.current_scanner_state === "Scanning" ? "text-primary" : ""}`}>
                      {stats ? stats.current_scanner_state : "..."}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Cloud Credits</div>
                    <div className="text-2xl font-bold mt-1">
                      {stats ? stats.cloud_credits.toLocaleString() : "..."}
                    </div>
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
      {showUpsellModal && (
        <ProUpsellModal
          featureName="Multi-Directory Monitoring"
          onClose={() => setShowUpsellModal(false)}
        />
      )}
    </div>
  )
}
