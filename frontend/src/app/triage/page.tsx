"use client"

import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ShieldAlert, Cpu, CheckCircle, ShieldCheck, LayoutGrid, List, Cloud, Server, UploadCloud, FileWarning, Timer, Info, Database } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { useToast } from "@/hooks/use-toast"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"

// Types matching the backend response
type MediaFile = {
  id: number
  filepath: string
  mtime: number
  size: number
  sha256_hash: string | null
  last_hashed_date: string | null
  state: string
  isAiGenerated?: boolean // Mocked flag for human review gateway
}

export default function TriageGallery() {
  const [corruptedFiles, setCorruptedFiles] = React.useState<MediaFile[]>([])
  const [loading, setLoading] = React.useState(true)
  const [selectedFile, setSelectedFile] = React.useState<MediaFile | null>(null)
  const [viewMode, setViewMode] = React.useState<"gallery" | "list">("gallery")
  const { token } = useAuth()
  const { toast } = useToast()

  // Flyout State
  const [aiEngine, setAiEngine] = React.useState<"cloud" | "local">("local")
  const [promptContext, setPromptContext] = React.useState("")
  const [isUploading, setIsUploading] = React.useState(false)

  React.useEffect(() => {
    async function fetchCorrupted() {
      try {
        const res = await fetch("/api/files/corrupted", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        if (res.ok) {
          const data = await res.json()
          setCorruptedFiles(data)
        } else {
          // Mock fallback if API fails
          setCorruptedFiles([
            { id: 1, filepath: "/media/2023/vacation/DSC_0142.CR2", size: 28400000, state: "corrupted", mtime: 1690000000, sha256_hash: "abc", last_hashed_date: null, isAiGenerated: true },
            { id: 2, filepath: "/media/family/IMG_8821.jpg", size: 4500000, state: "corrupted", mtime: 1680000000, sha256_hash: "def", last_hashed_date: null, isAiGenerated: false },
            { id: 3, filepath: "/media/work/presentation_assets/logo_v2.png", size: 1200000, state: "corrupted", mtime: 1670000000, sha256_hash: "ghi", last_hashed_date: null, isAiGenerated: true },
          ])
        }
      } catch (error) {
        setCorruptedFiles([
            { id: 1, filepath: "/media/2023/vacation/DSC_0142.CR2", size: 28400000, state: "corrupted", mtime: 1690000000, sha256_hash: "abc", last_hashed_date: null, isAiGenerated: true },
            { id: 2, filepath: "/media/family/IMG_8821.jpg", size: 4500000, state: "corrupted", mtime: 1680000000, sha256_hash: "def", last_hashed_date: null, isAiGenerated: false },
        ])
      } finally {
        setLoading(false)
      }
    }
    if (token) fetchCorrupted()
  }, [token])

  const handleAction = async (action: string) => {
    if (!selectedFile) return;
    toast({
      title: "Action Initiated",
      description: `Triggered ${action} for ${selectedFile.filepath.split('/').pop()}`,
    })
    // Simulate API call...
    setTimeout(() => {
      setSelectedFile(null); // Close flyout
      setCorruptedFiles(prev => prev.filter(f => f.id !== selectedFile.id));
    }, 1000);
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && selectedFile) {
      setIsUploading(true);
      toast({ title: "Uploading Replacement", description: `Overwriting ${selectedFile.filepath.split('/').pop()} with ${file.name}` });
      // Simulate API upload
      setTimeout(() => {
        setIsUploading(false);
        setSelectedFile(null);
        setCorruptedFiles(prev => prev.filter(f => f.id !== selectedFile.id));
        toast({ title: "Success", description: "File successfully overwritten.", variant: "default" });
      }, 1500);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden pb-safe max-w-7xl mx-auto">
      <div className="px-6 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white/90">Triage Center</h1>
          <p className="text-muted-foreground mt-2">
            Review and remediate corrupted files across the array.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-black/40 p-1 rounded-lg border border-white/5">
          <Button
            variant={viewMode === "gallery" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewMode("gallery")}
            className="w-10 h-8 p-0"
          >
            <LayoutGrid className="w-4 h-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewMode("list")}
            className="w-10 h-8 p-0"
          >
            <List className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 px-6">
        {loading ? (
          <div className="flex justify-center p-12 text-muted-foreground">Loading triage queue...</div>
        ) : corruptedFiles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground bg-card/20 rounded-xl border border-dashed border-white/10">
            <CheckCircle className="w-16 h-16 text-primary/30 mb-4" />
            <p className="text-xl font-medium">All Clear</p>
            <p className="text-sm">No corrupted files found in the active pool.</p>
          </div>
        ) : (
          <div className={viewMode === "gallery" ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-6" : "space-y-2 pb-6"}>
            {corruptedFiles.map(file => (
              viewMode === "gallery" ? (
                <Card key={file.id} className="bg-card/40 border-white/5 overflow-hidden hover:border-white/20 transition-all cursor-pointer group" onClick={() => setSelectedFile(file)}>
                  <div className="aspect-video bg-black/60 relative flex items-center justify-center">
                    <FileWarning className="w-12 h-12 text-destructive/50 group-hover:scale-110 transition-transform" />
                    {file.isAiGenerated && (
                      <Badge className="absolute top-2 right-2 bg-orange-500/20 text-orange-400 border-orange-500/20 text-[10px]">
                        Review Required
                      </Badge>
                    )}
                  </div>
                  <CardContent className="p-3">
                    <p className="text-sm font-medium truncate" title={file.filepath}>{file.filepath.split('/').pop()}</p>
                    <p className="text-xs text-muted-foreground truncate mt-1">{file.filepath}</p>
                  </CardContent>
                </Card>
              ) : (
                <div key={file.id} className="flex items-center gap-4 p-2 bg-card/40 border border-white/5 rounded-lg hover:bg-card/60 transition-colors cursor-pointer" onClick={() => setSelectedFile(file)}>
                   <div className="w-10 h-10 shrink-0 bg-black/60 rounded flex items-center justify-center border border-white/5">
                     <FileWarning className="w-5 h-5 text-destructive/50" />
                   </div>
                   <div className="flex-1 min-w-0">
                     <div className="flex items-center gap-2">
                       <p className="text-sm font-medium text-white/90 truncate">{file.filepath.split('/').pop()}</p>
                       {file.isAiGenerated && <Badge variant="outline" className="text-[9px] border-orange-500/30 text-orange-400 h-4 px-1 py-0">VETO PENDING</Badge>}
                     </div>
                     <p className="text-xs text-muted-foreground truncate font-mono mt-0.5">{file.filepath}</p>
                   </div>
                   <div className="shrink-0 text-xs text-muted-foreground px-4">
                     {(file.size / (1024*1024)).toFixed(1)} MB
                   </div>
                </div>
              )
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Side-by-Side Review Flyout Drawer (Full Screen Overlay) */}
      {selectedFile && (
        <Dialog open={!!selectedFile} onOpenChange={(open) => !open && setSelectedFile(null)}>
          <DialogContent className="max-w-[95vw] w-full h-[95vh] p-0 flex flex-col md:flex-row bg-background/95 backdrop-blur-xl border-white/10 overflow-hidden">

            {/* Visual Review Pane (Left) */}
            <div className="flex-1 bg-black/50 p-6 flex flex-col border-b md:border-b-0 md:border-r border-white/5">
               <div className="mb-4">
                 <h2 className="text-lg font-bold text-white/90">{selectedFile.filepath.split('/').pop()}</h2>
                 <p className="text-sm text-muted-foreground font-mono">{selectedFile.filepath}</p>
               </div>

               <div className="flex-1 grid grid-rows-2 gap-4">
                 <div className="bg-card/30 rounded-xl border border-destructive/20 flex flex-col items-center justify-center relative">
                   <Badge className="absolute top-4 left-4 bg-destructive/20 text-destructive border-destructive/20">Corrupted Original</Badge>
                   <FileWarning className="w-16 h-16 text-destructive/30 mb-2" />
                   <p className="text-sm text-muted-foreground">Unable to render payload</p>
                 </div>
                 <div className="bg-card/30 rounded-xl border border-primary/20 flex flex-col items-center justify-center relative">
                   <Badge className="absolute top-4 left-4 bg-primary/20 text-primary border-primary/20">Preview Render</Badge>
                   <Info className="w-16 h-16 text-primary/30 mb-2" />
                   <p className="text-sm text-muted-foreground">Select a remediation action to preview</p>
                 </div>
               </div>
            </div>

            {/* Controls Pane (Right) */}
            <div className="w-full md:w-[450px] p-6 flex flex-col overflow-y-auto custom-scrollbar bg-card/10">

               {/* Require Human Review Gateway Notice */}
               {selectedFile.isAiGenerated ? (
                 <div className="mb-6 p-4 rounded-xl bg-orange-500/10 border border-orange-500/30 flex items-start gap-3">
                    <Timer className="w-5 h-5 text-orange-400 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-bold text-orange-400">Veto Pending: Cache Blocked</p>
                      <p className="text-xs text-orange-400/80 mt-1">This item requires manual approval. INFINITE TTL retention is active. Original file cannot be pruned.</p>
                    </div>
                 </div>
               ) : (
                 <div className="mb-6 p-3 rounded-lg bg-white/5 border border-white/10 flex items-center gap-3">
                    <Timer className="w-4 h-4 text-muted-foreground shrink-0" />
                    <p className="text-xs text-muted-foreground">Standard TTL Active: 30d remaining before auto-pruning.</p>
                 </div>
               )}

               <div className="space-y-6">
                 {/* Primary Controls */}
                 <div>
                   <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">Primary Recovery</h3>
                   <div className="grid grid-cols-2 gap-3">
                     <Button variant="outline" className="bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border-blue-500/20" onClick={() => handleAction("ZFS Snapshot Restore")}>
                       <Database className="w-4 h-4 mr-2" /> Local Snapshot
                     </Button>
                     <Button variant="outline" className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border-cyan-500/20" onClick={() => handleAction("Cloud Pull")}>
                       <Cloud className="w-4 h-4 mr-2" /> Cloud Fetch
                     </Button>
                   </div>
                 </div>

                 <div className="h-px bg-white/5" />

                 {/* Generative AI Sub-Menus */}
                 <div>
                   <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                     Generative AI Infill
                     <Badge variant="outline" className="text-[10px] ml-auto">Experimental</Badge>
                   </h3>

                   <Tabs value={aiEngine} onValueChange={(v) => setAiEngine(v as "cloud"|"local")} className="mb-4">
                     <TabsList className="grid w-full grid-cols-2 bg-black/40">
                       <TabsTrigger value="local" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary"><Server className="w-3 h-3 mr-2" /> Local Node</TabsTrigger>
                       <TabsTrigger value="cloud" className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"><Cloud className="w-3 h-3 mr-2" /> Cloud API</TabsTrigger>
                     </TabsList>
                   </Tabs>

                   <div className="space-y-3">
                     <Textarea
                       placeholder="Custom Generation Instructions/Context (e.g., 'Restore missing sky elements with deep blue gradient')"
                       value={promptContext}
                       onChange={(e) => setPromptContext(e.target.value)}
                       className="bg-black/40 border-white/10 resize-none h-24 text-sm"
                     />
                     <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white" onClick={() => handleAction("AI Generation Request")}>
                       <Cpu className="w-4 h-4 mr-2" /> Run AI Infill ({aiEngine})
                     </Button>
                   </div>
                 </div>

                 <div className="h-px bg-white/5" />

                 {/* Manual Overwrite Drop-Zone */}
                 <div>
                   <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">Manual Overwrite</h3>

                   <label className={`
                     flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors
                     ${isUploading ? 'bg-primary/10 border-primary/50' : 'bg-black/20 border-white/10 hover:bg-black/40 hover:border-white/20'}
                   `}>
                     <div className="flex flex-col items-center justify-center pt-5 pb-6">
                       <UploadCloud className={`w-8 h-8 mb-2 ${isUploading ? 'text-primary animate-pulse' : 'text-muted-foreground'}`} />
                       <p className="text-sm text-muted-foreground font-medium">
                         {isUploading ? 'Uploading...' : 'Drop corrected file here'}
                       </p>
                       <p className="text-xs text-muted-foreground/50 mt-1">Direct overwrite payload</p>
                     </div>
                     <input type="file" className="hidden" onChange={handleFileUpload} disabled={isUploading} />
                   </label>
                 </div>

                 {selectedFile.isAiGenerated && (
                   <Button variant="outline" className="w-full mt-4 border-orange-500/50 text-orange-400 hover:bg-orange-500/10" onClick={() => handleAction("Approve AI Result")}>
                     <CheckCircle className="w-4 h-4 mr-2" /> Approve & Lift Veto
                   </Button>
                 )}

               </div>
            </div>

          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
