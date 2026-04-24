"use client"

import * as React from "react"
import { Shield, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/context/AuthContext"

interface ProUpsellModalProps {
  featureName: string;
  onClose: () => void;
}

export function ProUpsellModal({ featureName, onClose }: ProUpsellModalProps) {
  const { token } = useAuth();
  const [licenseKey, setLicenseKey] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [success, setSuccess] = React.useState("");

  const handleUnlock = async () => {
    if (!licenseKey) {
      setError("Please enter a license key.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(`/api/license/activate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ license_key: licenseKey })
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess(data.message || "License verified successfully!");
        setTimeout(() => {
          onClose();
          // Optionally reload the page to refresh the user state and UI limits
          window.location.reload();
        }, 1500);
      } else {
        setError(data.detail || "Invalid license key.");
      }
    } catch (err) {
      setError("Failed to verify license key. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md bg-black/70 backdrop-blur-xl border border-primary/20 rounded-2xl shadow-2xl overflow-hidden p-6">

        {/* Glow effect */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-primary/20 rounded-full blur-[60px] pointer-events-none" />

        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex flex-col items-center text-center mt-2">
          <div className="p-3 bg-primary/10 rounded-full mb-4">
            <Shield className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-2">Upgrade to Pro</h2>
          <p className="text-muted-foreground text-sm mb-6">
            Unlock <span className="text-foreground font-medium">{featureName}</span> with Kintsugi Pro.
            Enter your LemonSqueezy License Key below to provision your account.
          </p>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="license">License Key</Label>
            <Input
              id="license"
              placeholder="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              className="font-mono text-xs"
            />
          </div>

          {error && <p className="text-sm text-destructive font-medium">{error}</p>}
          {success && <p className="text-sm text-primary font-medium">{success}</p>}

          <Button
            className="w-full font-bold shadow-[0_0_15px_rgba(var(--primary),0.3)]"
            onClick={handleUnlock}
            disabled={loading || !!success}
          >
            {loading ? "Verifying..." : success ? "Unlocked!" : "Unlock Pro Features"}
          </Button>

          <p className="text-center text-xs text-muted-foreground mt-4">
            Don't have a key? <a href="#" className="text-primary hover:underline">Purchase Kintsugi Pro</a>
          </p>
        </div>
      </div>
    </div>
  )
}
