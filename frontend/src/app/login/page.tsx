"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Shield, Info, CheckCircle2, ChevronRight, HardDrive, ShieldCheck, Zap } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()

  const [setupRequired, setSetupRequired] = React.useState<boolean | null>(null)
  const [oidcEnabled, setOidcEnabled] = React.useState<boolean>(false)
  const [currentStep, setCurrentStep] = React.useState(0) // 0: Check, 1: Admin, 2: Settings, 3: Demo, 4: Success

  // Admin Provisioning State
  const [username, setUsername] = React.useState("")
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  // Settings State
  const [monitoredDirectory, setMonitoredDirectory] = React.useState("/media")
  const [autoRestore, setAutoRestore] = React.useState(false)
  const [autoRepair, setAutoRepair] = React.useState(false)
  const [retentionDays, setRetentionDays] = React.useState(90)

  // Demo State
  const [demoState, setDemoState] = React.useState<"initial" | "corrupted" | "restored">("initial")

  React.useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch("/api/auth/status")
        if (res.ok) {
          const data = await res.json()
          setSetupRequired(data.setup_required)
          setOidcEnabled(data.oidc_enabled || false)
          if (data.setup_required) {
            setCurrentStep(1)
          }
        } else {
          setSetupRequired(false) // Fallback
        }
      } catch (err) {
        console.error("Failed to fetch setup status", err)
        setSetupRequired(false) // Fallback
      }
    }
    checkStatus()
  }, [])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const formData = new URLSearchParams()
      formData.append("username", username)
      formData.append("password", password)

      const res = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        login(data.access_token)
      } else {
        const data = await res.json()
        setError(data.detail || "Authentication failed")
      }
    } catch (err) {
      setError("Network error. Please ensure the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
      })

      if (res.ok) {
        const data = await res.json()
        login(data.access_token) // Log them in to get token for next steps
        setCurrentStep(2)
      } else {
        const data = await res.json()
        setError(data.detail || "Registration failed")
      }
    } catch (err) {
      setError("Network error.")
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({
          monitored_directory: monitoredDirectory,
          auto_restore: autoRestore,
          auto_repair: autoRepair,
          retention_days: retentionDays
        })
      })

      if (res.ok) {
        setCurrentStep(3)
        // Start demo animation sequence
        setTimeout(() => setDemoState("corrupted"), 1500)
      } else {
        const data = await res.json()
        setError(data.detail || "Failed to save settings")
      }
    } catch (err) {
      setError("Network error.")
    } finally {
      setLoading(false)
    }
  }

  const handleDemoRestore = () => {
    setDemoState("restored")
    setTimeout(() => {
      setCurrentStep(4)
      setTimeout(() => {
        router.push("/browser")
      }, 2000)
    }, 2000)
  }


  if (setupRequired === null) {
    return <div className="min-h-screen flex items-center justify-center bg-background"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>
  }

  // STANDARD LOGIN (Setup already complete)
  if (!setupRequired) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-[radial-gradient(circle_at_center_top,_#1a1a1a_0%,_hsl(var(--background))_70%)] relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
        <div className="w-full max-w-md z-10 px-4">
          <div className="flex flex-col items-center mb-8">
            <div className="p-4 bg-black/40 rounded-2xl border border-white/10 backdrop-blur-md mb-4 shadow-xl">
              <Shield className="w-10 h-10 text-primary" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">Kintsugi-DAM</h1>
            <p className="text-muted-foreground mt-2 text-center">Secure digital asset management and automated healing.</p>
          </div>
          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl">
            <CardHeader>
              <CardTitle>Sign In</CardTitle>
              <CardDescription>Enter your credentials to access your library.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {oidcEnabled && (
                <div className="space-y-4">
                  <Button type="button" variant="outline" className="w-full bg-white text-black hover:bg-gray-200" onClick={() => window.location.href = "/api/auth/oidc/login"}>
                    <ShieldCheck className="w-4 h-4 mr-2" />
                    Login with SSO
                  </Button>
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-white/10" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-black/50 px-2 text-muted-foreground backdrop-blur-md">Or</span>
                    </div>
                  </div>
                </div>
              )}
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="admin" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
                </div>
                {error && <div className="p-3 bg-destructive/20 border border-destructive/30 text-destructive text-sm rounded-md">{error}</div>}
                <Button type="submit" className="w-full mt-4" disabled={loading}>{loading ? "Authenticating..." : "Sign In"}</Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // WIZARD UI
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[radial-gradient(circle_at_center_top,_#1a1a1a_0%,_hsl(var(--background))_70%)] relative">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-xl z-10 px-4">
        {currentStep < 4 && (
          <div className="flex flex-col items-center mb-8">
            <div className="p-4 bg-black/40 rounded-2xl border border-white/10 backdrop-blur-md mb-4 shadow-xl">
              <Zap className="w-10 h-10 text-primary" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">Welcome to Kintsugi-DAM</h1>
            <p className="text-muted-foreground mt-2 text-center">Let's get your secure environment set up.</p>

            {/* Progress indicators */}
            <div className="flex gap-2 mt-6">
              {[1, 2, 3].map((step) => (
                <div key={step} className={`h-2 w-16 rounded-full transition-colors ${currentStep >= step ? 'bg-primary' : 'bg-white/10'}`} />
              ))}
            </div>
          </div>
        )}

        {/* STEP 1: Admin Provisioning */}
        {currentStep === 1 && (
          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-primary"/> Step 1: Admin Provisioning</CardTitle>
              <CardDescription>Create the master administrative account. Self-registration will be locked after this step.</CardDescription>
            </CardHeader>
            <CardContent>
              <form id="register-form" onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Admin Username</Label>
                  <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="admin" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Recovery Email</Label>
                  <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@example.com" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Secure Password</Label>
                  <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
                </div>
                {error && <div className="p-3 bg-destructive/20 border border-destructive/30 text-destructive text-sm rounded-md">{error}</div>}
              </form>
            </CardContent>
            <CardFooter>
               <Button type="submit" form="register-form" className="w-full" disabled={loading}>
                 {loading ? "Provisioning..." : "Create Admin Account"} <ChevronRight className="w-4 h-4 ml-2" />
               </Button>
            </CardFooter>
          </Card>
        )}

        {/* STEP 2: Core Configuration */}
        {currentStep === 2 && (
          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><HardDrive className="w-5 h-5 text-primary"/> Step 2: Core Configuration</CardTitle>
              <CardDescription>Configure where Kintsugi-DAM looks for files and how it handles corruption.</CardDescription>
            </CardHeader>
            <CardContent>
              <form id="settings-form" onSubmit={handleSaveSettings} className="space-y-6">

                <div className="space-y-2">
                  <Label htmlFor="monitoredDirectory">Monitored Directory Path</Label>
                  <Input id="monitoredDirectory" value={monitoredDirectory} onChange={(e) => setMonitoredDirectory(e.target.value)} placeholder="/media" required />
                  <p className="text-xs text-muted-foreground">The main library or watchdog target.</p>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-white/10 p-4 bg-black/20">
                  <div className="space-y-0.5">
                    <Label className="text-base">Auto-Restore from Backups</Label>
                    <p className="text-sm text-muted-foreground">Automatically pull clean files from Snapshots/Cloud when corruption is detected.</p>
                  </div>
                  <Switch checked={autoRestore} onCheckedChange={setAutoRestore} />
                </div>

                <div className="flex items-center justify-between rounded-lg border border-white/10 p-4 bg-black/20">
                  <div className="space-y-0.5">
                    <Label className="text-base">Auto-Quarantine Corruption</Label>
                    <p className="text-sm text-muted-foreground">Automatically move bad files to the Triage folder.</p>
                  </div>
                  <Switch checked={autoRepair} onCheckedChange={setAutoRepair} />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="retentionDays">Retention Policy (Days)</Label>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger type="button"><Info className="w-4 h-4 text-muted-foreground hover:text-foreground" /></TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p>To prevent accidental data loss, corrupted originals are kept in a local Triage folder before permanent deletion. 90 days allows ample time for manual review if needed.</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <Input id="retentionDays" type="number" min="1" value={retentionDays} onChange={(e) => setRetentionDays(parseInt(e.target.value) || 90)} required />
                </div>

                {error && <div className="p-3 bg-destructive/20 border border-destructive/30 text-destructive text-sm rounded-md">{error}</div>}
              </form>
            </CardContent>
            <CardFooter>
               <Button type="submit" form="settings-form" className="w-full" disabled={loading}>
                 {loading ? "Saving..." : "Save Configuration"} <ChevronRight className="w-4 h-4 ml-2" />
               </Button>
            </CardFooter>
          </Card>
        )}

        {/* STEP 3: Interactive Demo */}
        {currentStep === 3 && (
          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500 overflow-hidden">
            <CardHeader>
              <CardTitle>Step 3: Interactive Demo</CardTitle>
              <CardDescription>Let's simulate a corruption event so you know what to do.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="relative w-full aspect-video rounded-xl overflow-hidden border border-white/10 bg-black flex items-center justify-center">
                 {/* Mock Image */}
                 <div className="absolute inset-0 bg-cover bg-center" style={{backgroundImage: "url('https://images.unsplash.com/photo-1682687220742-aba13b6e50ba?w=800&q=80')"}}></div>

                 {/* Glitch Overlay */}
                 {demoState === "corrupted" && (
                   <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMSIvPgo8L3N2Zz4=')] animate-pulse mix-blend-overlay opacity-80" style={{ backdropFilter: 'sepia(100%) hue-rotate(90deg) saturate(300%)' }}></div>
                 )}

                 {/* Restored Overlay */}
                 {demoState === "restored" && (
                    <div className="absolute inset-0 bg-primary/20 backdrop-blur-[2px] flex items-center justify-center animate-in fade-in duration-500">
                      <div className="bg-black/60 text-white px-6 py-3 rounded-full flex items-center gap-2 font-medium backdrop-blur-md">
                        <CheckCircle2 className="w-5 h-5 text-green-400" /> Restored Successfully
                      </div>
                    </div>
                 )}

                 <div className="absolute bottom-4 left-4 bg-black/60 px-3 py-1 rounded-md text-sm backdrop-blur-sm">
                   Family_Vacation.jpg
                 </div>
              </div>

              {demoState === "corrupted" && (
                <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-xl animate-in slide-in-from-bottom-2 fade-in duration-300">
                  <div className="flex items-start gap-3">
                     <div className="p-2 bg-destructive/20 rounded-lg text-destructive"><Zap className="w-5 h-5" /></div>
                     <div className="flex-1">
                       <h4 className="font-semibold text-destructive">Corruption Detected!</h4>
                       <p className="text-sm text-muted-foreground mt-1">Valid Snapshot Backup Found in /snapshots/daily</p>
                       <Button onClick={handleDemoRestore} className="mt-3 bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_20px_rgba(var(--primary),0.5)] animate-pulse border border-primary/50">
                          Restore File Now
                       </Button>
                     </div>
                  </div>
                </div>
              )}

              {demoState === "restored" && (
                <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl animate-in fade-in duration-500 text-green-400 text-sm">
                   <p className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4"/> Restored instantly! The corrupted artifact has been safely moved to Triage based on your {retentionDays}-day retention policy.</p>
                </div>
              )}

              {demoState === "initial" && (
                <div className="text-center text-muted-foreground animate-pulse text-sm">Simulating watchdog detection...</div>
              )}

            </CardContent>
          </Card>
        )}

        {/* STEP 4: Success */}
        {currentStep === 4 && (
          <div className="flex flex-col items-center justify-center text-center space-y-6 animate-in zoom-in duration-700">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl scale-150 animate-pulse" />
              <CheckCircle2 className="w-32 h-32 text-primary relative z-10" />
            </div>
            <h2 className="text-4xl font-bold tracking-tight">All Set!</h2>
            <p className="text-xl text-muted-foreground">Your library is now protected by Kintsugi-DAM.</p>
          </div>
        )}

      </div>
    </div>
  )
}
