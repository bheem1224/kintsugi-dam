"use client"

import * as React from "react"
import { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ShieldCheck } from "lucide-react"

interface StepAdminProps {
  adminExists: boolean
  username: string
  setUsername: (v: string) => void
  email: string
  setEmail: (v: string) => void
  password: string
  setPassword: (v: string) => void
  confirmPassword: string
  setConfirmPassword: (v: string) => void
  error: string
}

export function StepAdmin({
  adminExists,
  username,
  setUsername,
  email,
  setEmail,
  password,
  setPassword,
  confirmPassword,
  setConfirmPassword,
  error
}: StepAdminProps) {
  return (
    <>
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
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="admin" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            {error && <div className="p-3 bg-destructive/20 border border-destructive/30 text-destructive text-sm rounded-md">{error}</div>}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
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
          </div>
        )}
      </CardContent>
    </>
  )
}
