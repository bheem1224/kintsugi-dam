import * as React from "react"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Cpu, Cloud, AlertCircle, Key } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useAuth } from "@/context/AuthContext"

// Types matching the backend response
type MediaFile = {
  id: number
  filepath: string
  mtime: number
  size: number
  sha256_hash: string | null
  last_hashed_date: string | null
  state: string
}

interface AIRepairDialogProps {
  file: MediaFile;
  onClose: () => void;
}

export function AIRepairDialog({ file, onClose }: AIRepairDialogProps) {
  const { user } = useAuth()
  const isPro = user?.is_pro === true
  const [useCloud, setUseCloud] = React.useState(false)
  const [licenseKey, setLicenseKey] = React.useState("")
  const [isRepairing, setIsRepairing] = React.useState(false)
  const [message, setMessage] = React.useState("")
  const [contextFiles, setContextFiles] = React.useState<number[]>([])

  const handleActivateLicense = async () => {
    try {
      const res = await fetch(`/api/license/activate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ license_key: licenseKey })
      })
      const data = await res.json()
      if (res.ok) {
        setMessage(data.message)
      } else {
        setMessage(data.detail || "Failed to activate license")
      }
    } catch (err) {
      setMessage("Error activating license")
    }
  }

  const handleRepair = async () => {
    setIsRepairing(true)
    setMessage("")
    try {
      const provider = useCloud ? "cloud" : "local"
      const res = await fetch(`/api/files/${file.id}/repair/ai`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context_file_ids: contextFiles, provider })
      })

      const data = await res.json()
      if (res.ok) {
        setMessage(data.message)
      } else {
        setMessage(data.detail || "Repair failed")
      }
    } catch (err) {
      setMessage("Error connecting to repair service")
    } finally {
      setIsRepairing(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card text-card-foreground shadow-lg rounded-xl w-full max-w-md overflow-hidden border">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5" />
            AI Repair Configuration
          </h2>

          <div className="text-sm text-muted-foreground mb-6 break-all">
            Target: {file.filepath}
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="cloud-mode" className="text-base font-medium flex items-center gap-2">
                  <Cloud className="w-4 h-4 text-blue-500" />
                  Cloud AI Generation
                </Label>
                <p className="text-xs text-muted-foreground">
                  Use advanced models. Consumes 1 Cloud Credit.
                </p>
              </div>
              {!isPro ? (
    <TooltipProvider delay={100}>
      <Tooltip>
        <TooltipTrigger>
          <span className="inline-block cursor-not-allowed">
            <Switch id="cloud-mode" checked={false} disabled className="pointer-events-none" />
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <p>Available with Kintsugi Pro.</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ) : (
    <Switch
      id="cloud-mode"
      checked={useCloud}
      onCheckedChange={setUseCloud}
    />
  )}
            </div>

            {useCloud && (
              <div className="bg-muted p-4 rounded-lg space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-amber-600 dark:text-amber-500">
                  <AlertCircle className="w-4 h-4" />
                  Requires Cloud Credits
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter License Key (or DEV_BYPASS_LICENSE)"
                    value={licenseKey}
                    onChange={(e) => setLicenseKey(e.target.value)}
                    className="h-8 text-xs"
                  />
                  <Button size="sm" onClick={handleActivateLicense} variant="secondary" className="h-8">
                    <Key className="w-4 h-4 mr-1" />
                    Activate
                  </Button>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label className="text-sm font-medium">Context Images (Max 3)</Label>
              <p className="text-xs text-muted-foreground mb-2">
                Select up to 3 clean images to guide the AI repair.
              </p>
              <div className="text-xs italic text-muted-foreground border p-2 rounded bg-muted/50 text-center">
                Context Picker Component Placeholder
              </div>
            </div>

            {message && (
              <div className="p-3 text-sm bg-accent text-accent-foreground rounded-md text-center">
                {message}
              </div>
            )}
          </div>
        </div>

        <div className="bg-muted/50 p-4 border-t flex justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={isRepairing}>
            Cancel
          </Button>
          <Button onClick={handleRepair} disabled={isRepairing}>
            {isRepairing ? "Simulating..." : "Start Repair"}
          </Button>
        </div>
      </div>
    </div>
  )
}
