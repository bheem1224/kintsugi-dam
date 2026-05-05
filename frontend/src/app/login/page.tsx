"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useAuth } from "@/context/AuthContext"
import { Card, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Shield, ChevronRight, Zap, ChevronLeft } from "lucide-react"
import { useRouter } from "next/navigation"

// Step Components
import { StepAdmin } from "./components/StepAdmin"
import { StepPaths } from "./components/StepPaths"
import { StepThree } from "./components/StepThree"
import { StepFour } from "./components/StepFour"

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()

  const [setupRequired, setSetupRequired] = React.useState<boolean | null>(null)
  const [adminExists, setAdminExists] = React.useState(false)
  const [oidcEnabled, setOidcEnabled] = React.useState<boolean>(false)
  const [currentStep, setCurrentStep] = React.useState(0) // 0: Check, 1: Welcome/Admin, 2: Paths, 3: Triage, 4: Success
  const [direction, setDirection] = React.useState(0)

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

  // Step 3: Triage Options State
  const [autoRestore, setAutoRestore] = React.useState(true)
  const [autoRestoreCloud, setAutoRestoreCloud] = React.useState(false)
  const [autoRestoreAI, setAutoRestoreAI] = React.useState(false)
  const [aiUseKintsugiCloud, setAiUseKintsugiCloud] = React.useState(true)

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

  const paginate = (newStep: number) => {
    setDirection(newStep > currentStep ? 1 : -1)
    setCurrentStep(newStep)
  }

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
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
        localStorage.setItem("token", data.access_token)
        if (setupRequired) {
          paginate(2)
        } else {
          login(data.access_token)
        }
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
        paginate(2)
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
          auto_restore: autoRestore,
          auto_restore_cloud: autoRestoreCloud,
          auto_restore_ai: autoRestoreAI,
          ai_use_kintsugi_cloud: aiUseKintsugiCloud,
          is_setup_complete: true
        })
      })

      if (res.ok) {
        paginate(4)
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

  const variants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 100 : -100,
      opacity: 0
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1
    },
    exit: (direction: number) => ({
      zIndex: 0,
      x: direction < 0 ? 100 : -100,
      opacity: 0
    })
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
             {/* Simple login form kept inline for non-setup flow */}
             <div className="p-6 space-y-4">
              <h2 className="text-xl font-bold">Sign In</h2>
              <p className="text-sm text-muted-foreground">Enter your credentials to access your library.</p>
              
              {oidcEnabled && (
                <div className="space-y-4">
                  <Button type="button" variant="outline" className="w-full bg-white text-black hover:bg-gray-200 transition-all hover:-translate-y-0.5 hover:shadow-lg" onClick={() => window.location.href = "/api/auth/oidc/login"}>
                    Login with SSO
                  </Button>
                  <div className="relative"><div className="absolute inset-0 flex items-center"><span className="w-full border-t border-white/10" /></div><div className="relative flex justify-center text-xs uppercase"><span className="bg-black/50 px-2 text-muted-foreground">Or</span></div></div>
                </div>
              )}
              
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2"><label className="text-sm font-medium">Username</label><input className="w-full bg-white/5 border border-white/10 rounded-md p-2" value={username} onChange={(e) => setUsername(e.target.value)} required /></div>
                <div className="space-y-2"><label className="text-sm font-medium">Password</label><input className="w-full bg-white/5 border border-white/10 rounded-md p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
                {error && <div className="text-xs text-red-500">{error}</div>}
                <Button type="submit" className="w-full transition-all hover:-translate-y-0.5 hover:shadow-lg" disabled={loading}>{loading ? "Authenticating..." : "Sign In"}</Button>
              </form>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[radial-gradient(circle_at_center_top,_#1a1a1a_0%,_hsl(var(--background))_70%)] relative overflow-hidden">
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

        <div className="relative">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={currentStep}
              custom={direction}
              variants={variants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{
                x: { type: "spring", stiffness: 300, damping: 30 },
                opacity: { duration: 0.3 }
              }}
            >
              {currentStep < 4 ? (
                <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl">
                  {currentStep === 1 && (
                    <StepAdmin
                      adminExists={adminExists}
                      username={username} setUsername={setUsername}
                      email={email} setEmail={setEmail}
                      password={password} setPassword={setPassword}
                      confirmPassword={confirmPassword} setConfirmPassword={setConfirmPassword}
                      error={error}
                    />
                  )}
                  {currentStep === 2 && (
                    <StepPaths
                      mediaPath={mediaPath} setMediaPath={setMediaPath}
                      triagePath={triagePath} setTriagePath={setTriagePath}
                      pathTestResults={pathTestResults}
                      testPaths={testPaths}
                      loading={loading}
                    />
                  )}
                  {currentStep === 3 && (
                    <StepThree
                      autoRestore={autoRestore} setAutoRestore={setAutoRestore}
                      autoRestoreCloud={autoRestoreCloud} setAutoRestoreCloud={setAutoRestoreCloud}
                      autoRestoreAI={autoRestoreAI} setAutoRestoreAI={setAutoRestoreAI}
                      aiUseKintsugiCloud={aiUseKintsugiCloud} setAiUseKintsugiCloud={setAiUseKintsugiCloud}
                    />
                  )}

                  <CardFooter className="flex gap-3">
                    {currentStep > 1 && (
                      <Button variant="ghost" onClick={() => paginate(currentStep - 1)} className="gap-2 transition-all hover:bg-white/5">
                        <ChevronLeft className="w-4 h-4" /> Back
                      </Button>
                    )}
                    
                    {currentStep === 1 && (
                      <Button onClick={adminExists ? handleLogin : handleAdminCreation} className="flex-1 h-12 text-lg font-semibold transition-all hover:-translate-y-0.5 hover:shadow-lg" disabled={loading}>
                        {loading ? "Processing..." : (adminExists ? "Sign In to Continue" : "Create Admin Account")} <ChevronRight className="ml-2 w-5 h-5" />
                      </Button>
                    )}
                    {currentStep === 2 && (
                      <Button className="flex-1 h-12 text-lg font-semibold transition-all hover:-translate-y-0.5 hover:shadow-lg" onClick={() => paginate(3)} disabled={!pathTestResults || pathTestResults.media?.status !== 'ok' || pathTestResults.triage?.status !== 'ok'}>
                        Continue <ChevronRight className="ml-2 w-5 h-5" />
                      </Button>
                    )}
                    {currentStep === 3 && (
                      <Button className="flex-1 h-12 text-lg font-semibold transition-all hover:-translate-y-0.5 hover:shadow-lg" onClick={finalizeSetup} disabled={loading}>
                        {loading ? "Finalizing..." : "Complete Setup"} <ChevronRight className="ml-2 w-5 h-5" />
                      </Button>
                    )}
                  </CardFooter>
                </Card>
              ) : (
                <StepFour />
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {currentStep === 4 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="flex justify-center mt-8"
          >
            <Button size="lg" className="h-14 px-10 text-xl font-bold rounded-full shadow-[0_0_30px_rgba(var(--primary),0.4)] hover:shadow-[0_0_50px_rgba(var(--primary),0.6)] transition-all hover:-translate-y-1 active:scale-95" onClick={() => login(localStorage.getItem("token")!)}>
              Launch Dashboard
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  )
}
