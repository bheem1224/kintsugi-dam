"use client"

import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ShieldAlert, Cpu, CheckCircle, ShieldCheck } from "lucide-react"
import { AIRepairDialog } from "@/components/AIRepairDialog"
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

export default function TriageGallery() {
  const [corruptedFiles, setCorruptedFiles] = React.useState<MediaFile[]>([])
  const [loading, setLoading] = React.useState(true)
  const [selectedFile, setSelectedFile] = React.useState<MediaFile | null>(null)
  const { token } = useAuth();

  React.useEffect(() => {
    async function fetchCorrupted() {
      try {
        if (!token) return;
        const res = await fetch(`/api/files/corrupted`, {
          credentials: "include",
        headers: {
            "Authorization": `Bearer ${token}`
          }
        })
        if (res.ok) {
          const data = await res.json()
          setCorruptedFiles(data)
        }
      } catch (error) {
        console.error("Failed to fetch corrupted files:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchCorrupted()
  }, [token])

  if (loading) {
    return <div className="p-8">Loading triage gallery...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Triage Gallery</h1>
        <p className="text-muted-foreground mt-2">
          Review and remediate files flagged by detection algorithms.
        </p>
      </div>

      {corruptedFiles.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-20 text-center border border-white/5 bg-white/5 rounded-3xl backdrop-blur-md relative overflow-hidden group">
          {/* Background Glow */}
          <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
          
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl animate-pulse" />
            <ShieldCheck className="w-20 h-20 text-primary relative z-10 animate-pulse" />
          </div>
          
          <h2 className="text-2xl font-bold mt-6 tracking-tight">All Systems Nominal</h2>
          <p className="text-muted-foreground mt-2 max-w-xs mx-auto">
            Library is secure. No corruption detected.
          </p>
          
          <Button variant="outline" className="mt-8 gap-2 border-white/10 hover:bg-white/5 transition-all hover:-translate-y-0.5">
            Run Manual Audit
          </Button>
        </div>
      ) : (
        <div className="columns-1 md:columns-2 lg:columns-3 gap-4 space-y-4">
          {corruptedFiles.map((file) => (
            <Card key={file.id} className="break-inside-avoid transition-all hover:bg-white/5 hover:border-white/20">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <Badge variant="destructive" className="mb-2">
                    [CORRUPTED]
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(file.last_hashed_date || Date.now()).toLocaleDateString()}
                  </span>
                </div>
                <CardTitle className="text-base break-all leading-tight">
                  {file.filepath.split('/').pop()}
                </CardTitle>
                <div className="text-xs text-muted-foreground break-all mt-1">
                  {file.filepath}
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-muted p-2 rounded-md font-mono text-[10px] break-all text-muted-foreground">
                  <span className="font-bold text-foreground">SHA256: </span>
                  {file.sha256_hash || "PENDING"}
                </div>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button variant="outline" className="flex-1" size="sm">
                  <ShieldAlert className="w-4 h-4 mr-2" />
                  Quarantine
                </Button>
                <Button
                  variant="default"
                  className="flex-1"
                  size="sm"
                  onClick={() => setSelectedFile(file)}
                >
                  <Cpu className="w-4 h-4 mr-2" />
                  Repair with AI
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {selectedFile && (
        <AIRepairDialog
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
        />
      )}
    </div>
  )
}
