"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Shield } from "lucide-react"

export default function LoginPage() {
  const { login } = useAuth()
  const [isRegister, setIsRegister] = React.useState(false)

  const [username, setUsername] = React.useState("")
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login"
      const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${endpoint}`

      let body: any
      let headers: Record<string, string> = {}

      if (isRegister) {
        body = JSON.stringify({ username, email, password })
        headers["Content-Type"] = "application/json"
      } else {
        const formData = new URLSearchParams()
        formData.append("username", username)
        formData.append("password", password)
        body = formData
        headers["Content-Type"] = "application/x-www-form-urlencoded"
      }

      const res = await fetch(url, {
        method: "POST",
        headers,
        body
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

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[radial-gradient(circle_at_center_top,_#1a1a1a_0%,_hsl(var(--background))_70%)] relative">
      {/* Background decoration */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md z-10 px-4">
        <div className="flex flex-col items-center mb-8">
          <div className="p-4 bg-black/40 rounded-2xl border border-white/10 backdrop-blur-md mb-4 shadow-xl">
            <Shield className="w-10 h-10 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Kintsugi-DAM</h1>
          <p className="text-muted-foreground mt-2 text-center">
            Secure digital asset management and automated healing.
          </p>
        </div>

        <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl">
          <div className="flex border-b border-border">
            <button
              type="button"
              onClick={() => setIsRegister(false)}
              className={`flex-1 px-4 py-4 font-medium text-sm transition-colors ${!isRegister ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setIsRegister(true)}
              className={`flex-1 px-4 py-4 font-medium text-sm transition-colors ${isRegister ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              Create Account
            </button>
          </div>

          <CardHeader>
            <CardTitle>{isRegister ? "Create an account" : "Welcome back"}</CardTitle>
            <CardDescription>
              {isRegister
                ? "Enter your details to provision a new administrative account."
                : "Enter your credentials to access your library."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  required
                />
              </div>

              {isRegister && (
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@example.com"
                    required
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              {error && (
                <div className="p-3 bg-destructive/20 border border-destructive/30 text-destructive text-sm rounded-md">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full mt-4" disabled={loading}>
                {loading ? "Authenticating..." : (isRegister ? "Register" : "Sign In")}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
