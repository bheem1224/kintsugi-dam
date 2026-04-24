"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { ProUpsellModal } from "@/components/modals/ProUpsellModal"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Folder, Image as ImageIcon, ChevronRight, Scan } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

type FSItem = {
  name: string;
  type: string;
  path: string;
}

export default function BrowserPage() {
  const { user, token } = useAuth()
  const [currentPath, setCurrentPath] = React.useState("/media")
  const [items, setItems] = React.useState<FSItem[]>([])
  const [loading, setLoading] = React.useState(true)
  const [scanLoading, setScanLoading] = React.useState<string | null>(null)

  const { toast } = useToast()

  const [breadcrumbClicks, setBreadcrumbClicks] = React.useState(0)
  const clickTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)

  const handleBreadcrumbClick = () => {
    setBreadcrumbClicks(prev => prev + 1)

    if (clickTimeoutRef.current) clearTimeout(clickTimeoutRef.current)

    clickTimeoutRef.current = setTimeout(() => {
      setBreadcrumbClicks(0)
    }, 1500)
  }

  React.useEffect(() => {
    if (breadcrumbClicks >= 5) {
      setBreadcrumbClicks(0)
      // Decode S0lOVFNVR0ktQkVUQS01MA==
      const code = atob("S0lOVFNVR0ktQkVUQS01MA==")
      toast({
        title: "🎟️ You found a Golden Ticket!",
        description: `Use code ${code} at checkout for 50% off Kintsugi Pro. Only 10 available!`,
        className: "bg-black/40 backdrop-blur-md border-white/10 text-primary shadow-2xl",
        duration: 8000,
      })
    }
  }, [breadcrumbClicks, toast])

  const fetchPath = React.useCallback(async (path: string) => {
    if (!token) return
    setLoading(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/fs/browse?path=${encodeURIComponent(path)}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })
      if (res.ok) {
        const data = await res.json()
        setItems(data)
        setCurrentPath(path)
      } else {
        toast({
          title: "Access Denied",
          description: "Cannot browse this directory.",
          variant: "destructive"
        })
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [token, toast])

  React.useEffect(() => {
    if (user?.is_pro) {
      fetchPath("/media")
    } else {
      setLoading(false)
    }
  }, [user, fetchPath])

  const handleScan = async (path: string) => {
    setScanLoading(path)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/fs/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ path })
      })
      if (res.ok) {
        toast({
          title: "Scan Initiated",
          description: `Background scan started for ${path}`
        })
      } else {
        const data = await res.json()
        toast({
          title: "Scan Failed",
          description: data.detail || "Failed to start scan",
          variant: "destructive"
        })
      }
    } catch (e) {
      toast({
        title: "Error",
        description: "Network error occurred.",
        variant: "destructive"
      })
    } finally {
      setScanLoading(null)
    }
  }

  const navigateUp = () => {
    if (currentPath === "/media") return
    const newPath = currentPath.split("/").slice(0, -1).join("/")
    fetchPath(newPath || "/media")
  }

  const isPro = user?.is_pro === true

  return (
    <div className="relative space-y-6 max-w-5xl mx-auto h-full">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Pro File Browser</h1>
        <p className="text-muted-foreground mt-2">
          Navigate your active media library and trigger manual scans.
        </p>
      </div>

      <div className={`transition-all duration-500 ${!isPro ? "blur-md pointer-events-none opacity-50" : ""}`}>
        <Card>
          <CardHeader className="bg-muted/30 border-b border-border flex flex-row items-center gap-2 p-4 cursor-pointer select-none" onClick={handleBreadcrumbClick}>
            <div className="font-mono text-sm text-muted-foreground bg-muted px-2 py-1 rounded">
              {currentPath}
            </div>
            {currentPath !== "/media" && (
              <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); navigateUp(); }}>
                <ChevronRight className="w-4 h-4 rotate-180 mr-1" /> Back
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-muted-foreground">Loading directory...</div>
            ) : items.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">Directory is empty.</div>
            ) : (
              <div className="divide-y divide-border">
                {items.map((item) => (
                  <div key={item.path} className="flex items-center justify-between p-4 hover:bg-muted/30 transition-colors">
                    <div
                      className={`flex items-center gap-3 ${item.type === "directory" ? "cursor-pointer hover:text-primary" : ""}`}
                      onClick={() => item.type === "directory" && fetchPath(item.path)}
                    >
                      {item.type === "directory" ? (
                        <Folder className="w-5 h-5 text-primary" />
                      ) : (
                        <ImageIcon className="w-5 h-5 text-muted-foreground" />
                      )}
                      <span className="font-medium">{item.name}</span>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleScan(item.path)}
                      disabled={scanLoading === item.path}
                    >
                      <Scan className="w-4 h-4 mr-2" />
                      {scanLoading === item.path ? "Scanning..." : "Scan Now"}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {!loading && !isPro && (
        <ProUpsellModal featureName="Advanced File Browser" onClose={() => {}} />
      )}
    </div>
  )
}
