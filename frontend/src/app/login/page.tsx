"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Shield, CheckCircle2, ChevronRight, HardDrive, ShieldCheck, Zap, Activity, MousePointer2 } from "lucide-react"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()

  const [setupRequired, setSetupRequired] = React.useState<boolean | null>(null)
  const [adminExists, setAdminExists] = React.useState(false)
  const [oidcEnabled, setOidcEnabled] = React.useState<boolean>(false)
  const [currentStep, setCurrentStep] = React.useState(0) // 0: Check, 1: Welcome/Admin, 2: Paths, 3: Scan Settings, 4: Success

  // Admin Provisioning State
  const [username, setUsername] = React.useState("")
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [confirmPassword, setConfirmPassword] = React.useState("")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  // Step 2: Paths State
  const [mediaPath, setMediaPath] = React.useState("/media")
  const [triagePath, setTriagePath] = React.useState("/app/data/triage")
  const [pathTestResults, setPathTestResults] = React.useState<{media?: {status: string, message: string}, triage?: {status: string, message: string}} | null>(null)

  // Step 3: Scan Settings
  const [scanIntensity, setScanIntensity] = React.useState<"eco" | "balanced" | "turbo">("eco")

  React.useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch("/api/auth/status")
        if (res.ok) {
          const data = await res.json()
          setSetupRequired(data.setup_required)
          setAdminExists(data.admin_exists)
          
          setOidcEnabled(data.oidc_enabled || false)
          if (data.setup_required) {
            const token = localStorage.getItem("token")
            if (token && data.admin_exists) {
              setCurrentStep(2) // Skip to paths if already logged in/registered
            } else {
              setCurrentStep(1)
            }
          }
        } else {
          setSetupRequired(false)
        }
      } catch (err) {
        console.error("Failed to fetch setup status", err)
        setSetupRequired(false)
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

  const handleAdminCreation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }
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
        localStorage.setItem("token", data.access_token) // Stash for setup steps
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

  const testPaths = async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/settings/test-paths", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({ media_path: mediaPath, triage_path: triagePath })
      })
      if (res.ok) {
        const data = await res.json()
        setPathTestResults(data)
      }
    } catch (err) {
      setError("Failed to test paths.")
    } finally {
      setLoading(false)
    }
  }

  const savePaths = () => {
    setCurrentStep(3)
  }

  const finalizeSetup = async () => {
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
          monitored_directory: mediaPath,
          triage_directory: triagePath,
          scan_intensity: scanIntensity,
          is_setup_complete: true
        })
      })

      if (res.ok) {
        setCurrentStep(4)
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

  if (setupRequired === null) {
    return <div className="min-h-screen flex items-center justify-center bg-background"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>
  }

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

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[radial-gradient(circle_at_center_top,_#1a1a1a_0%,_hsl(var(--background))_70%)] relative">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-2xl z-10 px-4">
        {currentStep < 4 && (
          <div className="flex flex-col items-center mb-8 text-center">
            <div className="p-4 bg-black/40 rounded-2xl border border-white/10 backdrop-blur-md mb-4 shadow-xl">
              <Zap className="w-10 h-10 text-primary" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">Kintsugi Setup Wizard</h1>
            <p className="text-muted-foreground mt-2">Let&apos;s build your library&apos;s foundation.</p>

            <div className="flex gap-2 mt-6">
              {[1, 2, 3].map((step) => (
                <div key={step} className={`h-1.5 w-20 rounded-full transition-all duration-500 ${currentStep >= step ? 'bg-primary shadow-[0_0_10px_rgba(var(--primary),0.5)]' : 'bg-white/10'}`} />
              ))}
            </div>
          </div>
        )}

        {/* STEP 1: Welcome & Admin */}
        {currentStep === 1 && (
          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-primary"/> Welcome & Admin Creation</CardTitle>
              <CardDescription>
                {adminExists 
                  ? "An administrator already exists. Please sign in to continue setup." 
                  : "Kintsugi needs an admin account to protect the system and manage your assets."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {adminExists ? (
                <form id="login-form-setup" onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="admin" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
                  </div>
                  {error && <div className="p-3 bg-destructive/20 border border-destructive/30 text-destructive text-sm rounded-md">{error}</div>}
                </form>
              ) : (
                <form id="admin-form" onSubmit={handleAdminCreation} className="grid grid-cols-2 gap-4">
                  <div className="space-y-2 col-span-2">
                    <Label htmlFor="username">Admin Username</Label>
                    <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="e.g. curator_alpha" required />
                  </div>
                  <div className="space-y-2 col-span-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@kintsugi.local" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirm">Confirm Password</Label>
                    <Input id="confirm" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" required />
                  </div>
                  {error && <div className="p-3 bg-destructive/20 border border-destructive/30 text-destructive text-sm rounded-md col-span-2">{error}</div>}
                </form>
              )}
            </CardContent>
            <CardFooter>
              {adminExists ? (
                <Button type="submit" form="login-form-setup" className="w-full h-12 text-lg font-semibold" disabled={loading}>
                  {loading ? "Signing In..." : "Sign In to Continue"} <ChevronRight className="ml-2 w-5 h-5" />
                </Button>
              ) : (
                <Button type="submit" form="admin-form" className="w-full h-12 text-lg font-semibold" disabled={loading}>
                  {loading ? "Creating..." : "Create Admin Account"} <ChevronRight className="ml-2 w-5 h-5" />
                </Button>
              )}
            </CardFooter>
          </Card>
        )}

        {/* STEP 2: Path Configuration */}
        {currentStep === 2 && (
          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
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
                <Button variant="outline" size="sm" onClick={testPaths} disabled={loading} className="gap-2 border-primary/20 hover:bg-primary/10">
                  <Activity className="w-4 h-4" /> Test Paths & Permissions
                </Button>
              </div>
            </CardContent>
            <CardFooter className="flex gap-3">
              <Button variant="ghost" onClick={() => setCurrentStep(1)}>Back</Button>
              <Button className="flex-1 h-12 text-lg font-semibold" onClick={savePaths} disabled={!pathTestResults || pathTestResults.media?.status !== 'ok' || pathTestResults.triage?.status !== 'ok'}>
                Continue <ChevronRight className="ml-2 w-5 h-5" />
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* STEP 3: Scan Settings & Freemium */}
        {currentStep === 3 && (
          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Zap className="w-5 h-5 text-primary"/> Step 3: Initial Scan Settings</CardTitle>
              <CardDescription>Choose how aggressively Kintsugi should analyze your library.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
               {[
                 { id: "eco", title: "Eco Mode", desc: "Standard hashing & metadata checks. Lowest CPU impact.", badge: "Free" },
                 { id: "balanced", title: "Balanced", desc: "Deep bitstream analysis & structural validation.", badge: "Pro", locked: true },
                 { id: "turbo", title: "Turbo", desc: "Full frame-by-frame AI perceptual hashing & repair prep.", badge: "Pro", locked: true }
               ].map((opt) => (
                 <div 
                   key={opt.id}
                   onClick={() => !opt.locked && setScanIntensity(opt.id as any)}
                   className={`relative p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${scanIntensity === opt.id ? 'bg-primary/10 border-primary shadow-[0_0_15px_rgba(var(--primary),0.2)]' : 'bg-white/5 border-white/10 hover:border-white/20'}`}
                 >
                   <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${scanIntensity === opt.id ? 'bg-primary text-primary-foreground' : 'bg-white/10 text-muted-foreground'}`}>
                        <Activity className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{opt.title}</span>
                          <Badge variant={opt.locked ? "secondary" : "outline"} className={opt.locked ? "bg-amber-500/10 text-amber-500 border-amber-500/20" : ""}>{opt.badge}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{opt.desc}</p>
                      </div>
                   </div>
                   {opt.locked && <Shield className="w-5 h-5 text-muted-foreground/30" />}
                   {scanIntensity === opt.id && <CheckCircle2 className="w-5 h-5 text-primary" />}
                 </div>
               ))}
            </CardContent>
            <CardFooter className="flex gap-3">
              <Button variant="ghost" onClick={() => setCurrentStep(2)}>Back</Button>
              <Button className="flex-1 h-12 text-lg font-semibold" onClick={finalizeSetup} disabled={loading}>
                {loading ? "Saving..." : "Finalize Setup"} <ChevronRight className="ml-2 w-5 h-5" />
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* STEP 4: Success */}
        {currentStep === 4 && (
          <div className="flex flex-col items-center justify-center text-center space-y-8 py-12 animate-in zoom-in duration-700">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/30 rounded-full blur-[100px] animate-pulse scale-150" />
              <div className="relative z-10 h-32 w-32 rounded-full bg-black/40 border-2 border-primary flex items-center justify-center shadow-[0_0_50px_rgba(var(--primary),0.4)]">
                <CheckCircle2 className="w-20 h-20 text-primary" />
              </div>
            </div>
            
            <div className="space-y-2">
              <h2 className="text-5xl font-extrabold tracking-tighter">Setup Complete</h2>
              <p className="text-xl text-muted-foreground">Kintsugi-DAM is now guarding your digital legacy.</p>
            </div>

            <Button size="lg" className="h-14 px-10 text-xl font-bold rounded-full shadow-[0_0_30px_rgba(var(--primary),0.4)] hover:shadow-[0_0_50px_rgba(var(--primary),0.6)] transition-all" onClick={() => login(localStorage.getItem("token")!)}>
              Launch Dashboard
            </Button>
          </div>
        )}

      </div>
    </div>
  )
}
