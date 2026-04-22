"use client"

import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ShieldAlert, Cpu } from "lucide-react"

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

  React.useEffect(() => {
    async function fetchCorrupted() {
      try {
        const res = await fetch("http://localhost:8000/api/files/corrupted")
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
  }, [])

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
        <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed">
          <p className="text-lg font-medium">All clear</p>
          <p className="text-sm text-muted-foreground mt-1">No corrupted files detected in the active library.</p>
        </div>
      ) : (
        <div className="columns-1 md:columns-2 lg:columns-3 gap-4 space-y-4">
          {corruptedFiles.map((file) => (
            <Card key={file.id} className="break-inside-avoid">
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
                <Button variant="default" className="flex-1" size="sm">
                  <Cpu className="w-4 h-4 mr-2" />
                  Repair with AI
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
