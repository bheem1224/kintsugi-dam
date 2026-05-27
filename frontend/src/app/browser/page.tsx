"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FolderSearch, Folder, Image as ImageIcon, ChevronRight, Scan, Trash2, Edit2, Copy, ArrowRightLeft, FileWarning, ShieldCheck, Bug, Activity, File, Lock, History } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useToast } from "@/hooks/use-toast"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
  ContextMenuShortcut,
} from "@/components/ui/context-menu"

type FSItem = {
  name: string;
  type: string;
  path: string;
  size?: number;
  status?: "clean" | "warning" | "rotten"; // Mocked for UI if backend doesn't provide
}

export default function BrowserPage() {
  const { user, token } = useAuth()
  const [currentPath, setCurrentPath] = React.useState("/media")
  const [items, setItems] = React.useState<FSItem[]>([])
  const [loading, setLoading] = React.useState(true)
  const [pathHistory, setPathHistory] = React.useState<string[]>(["/media"])
  const { toast } = useToast()

  const rootFolders = [
    { name: "media", path: "/media", icon: <Folder className="w-4 h-4 text-primary" /> },
    { name: "watch", path: "/watch", icon: <Activity className="w-4 h-4 text-blue-400" /> },
    { name: "quarantine", path: "/quarantine", icon: <Lock className="w-4 h-4 text-orange-400" /> },
  ]

  // Mock processing state for the Task Progress Hub
  const [isProcessing, setIsProcessing] = React.useState(true);
  const [processingFile, setProcessingFile] = React.useState("DSC_0492_RAW.cr2");
  const [processingProgress, setProcessingProgress] = React.useState(42);

  React.useEffect(() => {
    // Simulate progress
    if (isProcessing) {
      const interval = setInterval(() => {
        setProcessingProgress(p => {
          if (p >= 100) {
            setProcessingFile("VID_2023_01.mp4");
            return 0;
          }
          return p + 5;
        })
      }, 800)
      return () => clearInterval(interval)
    }
  }, [isProcessing])

  React.useEffect(() => {
    // Fetch mock data for the selected path
    setLoading(true);
    setTimeout(() => {
      let mockItems: FSItem[] = [];
      if (currentPath === "/media") {
        mockItems = [
          { name: "vacation_2023", type: "directory", path: "/media/vacation_2023" },
          { name: "family_photos", type: "directory", path: "/media/family_photos" },
          { name: "IMG_001.jpg", type: "file", path: "/media/IMG_001.jpg", size: 4500000, status: "clean" },
          { name: "IMG_002.jpg", type: "file", path: "/media/IMG_002.jpg", size: 3200000, status: "clean" },
          { name: "IMG_003_corrupt.jpg", type: "file", path: "/media/IMG_003_corrupt.jpg", size: 1200000, status: "rotten" },
          { name: "IMG_004_truncated.jpg", type: "file", path: "/media/IMG_004_truncated.jpg", size: 500000, status: "warning" },
        ];
      } else if (currentPath === "/watch") {
         mockItems = [
          { name: "new_upload_01.mp4", type: "file", path: "/watch/new_upload_01.mp4", size: 14500000, status: "clean" },
          { name: "DSC_0492_RAW.cr2", type: "file", path: "/watch/DSC_0492_RAW.cr2", size: 28000000, status: "clean" },
        ];
      } else if (currentPath === "/quarantine") {
         mockItems = [
          { name: "infected_payload.bin", type: "file", path: "/quarantine/infected_payload.bin", size: 1024, status: "rotten" },
          { name: "ransomware_note.txt", type: "file", path: "/quarantine/ransomware_note.txt", size: 512, status: "rotten" },
        ];
      } else {
        mockItems = [
          { name: "photo_1.jpg", type: "file", path: `${currentPath}/photo_1.jpg`, size: 2000000, status: "clean" },
          { name: "photo_2.jpg", type: "file", path: `${currentPath}/photo_2.jpg`, size: 2200000, status: "clean" },
        ];
      }
      setItems(mockItems);
      setLoading(false);
    }, 300);
  }, [currentPath]);

  const handleNavigate = (newPath: string) => {
    setCurrentPath(newPath)
    if (!pathHistory.includes(newPath)) {
      setPathHistory([...pathHistory, newPath])
    }
  }

  const formatSize = (bytes?: number) => {
    if (!bytes) return "--";
    const mb = bytes / (1024 * 1024);
    return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
  }

  const handleContextAction = (action: string, file: FSItem) => {
    toast({
      title: `Action: ${action}`,
      description: `Target: ${file.name}`,
    });
  }

  return (
    <div className="flex flex-col h-full overflow-hidden pb-safe">
      <div className="px-6 py-4 flex items-center justify-between border-b border-border/50 shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">File Browser</h1>
          <p className="text-sm text-muted-foreground mt-1">Native Unraid Share Explorer</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-md border border-white/5">
           <FolderSearch className="w-4 h-4" />
           <span className="font-mono">{currentPath}</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT PANE: Directory Tree */}
        <div className="w-64 border-r border-border/50 flex flex-col bg-card/30">
          <ScrollArea className="flex-1 py-4">
             <div className="px-4 mb-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Server Shares</p>
             </div>
             <div className="space-y-1 px-2">
               {rootFolders.map((folder) => (
                 <button
                   key={folder.path}
                   onClick={() => handleNavigate(folder.path)}
                   className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                     currentPath.startsWith(folder.path)
                       ? "bg-primary/20 text-primary"
                       : "text-muted-foreground hover:bg-white/5 hover:text-white"
                   }`}
                 >
                   {folder.icon}
                   {folder.name}
                 </button>
               ))}
             </div>

             {/* Nested mock directories for /media */}
             {currentPath.startsWith("/media") && (
               <div className="pl-6 pr-2 mt-1 space-y-1 border-l border-white/10 ml-4">
                  <button
                    onClick={() => handleNavigate("/media/vacation_2023")}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors ${currentPath === "/media/vacation_2023" ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-white"}`}
                  >
                    <Folder className="w-3.5 h-3.5" /> vacation_2023
                  </button>
                  <button
                    onClick={() => handleNavigate("/media/family_photos")}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors ${currentPath === "/media/family_photos" ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-white"}`}
                  >
                    <Folder className="w-3.5 h-3.5" /> family_photos
                  </button>
               </div>
             )}
          </ScrollArea>

          {/* Bottom Left Sidebar Widget: Task Progress Hub */}
          <div className="p-4 border-t border-border/50 bg-black/40">
             <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Task</p>
                <Activity className="w-3 h-3 text-primary animate-pulse" />
             </div>
             <div className="bg-card/50 border border-white/5 rounded-lg p-3">
                <p className="text-xs text-white/90 font-medium truncate mb-2" title={processingFile}>
                  {processingFile}
                </p>
                <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                   <div
                     className="bg-primary h-full transition-all duration-300 ease-linear rounded-full"
                     style={{ width: `${processingProgress}%` }}
                   />
                </div>
                <div className="flex items-center justify-between mt-2">
                   <span className="text-[10px] text-muted-foreground">Hashing Payload</span>
                   <span className="text-[10px] font-mono text-primary">{processingProgress}%</span>
                </div>
             </div>
          </div>
        </div>

        {/* RIGHT PANE: Asset Grid */}
        <div className="flex-1 flex flex-col bg-black/20">
          <ScrollArea className="flex-1 p-6">
             {loading ? (
               <div className="flex items-center justify-center h-full text-muted-foreground">
                 Loading directory contents...
               </div>
             ) : items.length === 0 ? (
               <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-4">
                 <FolderSearch className="w-12 h-12 opacity-20" />
                 <p>Directory is empty</p>
               </div>
             ) : (
               <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                 {items.map((item) => (
                   item.type === "directory" ? (
                     <div
                       key={item.name}
                       className="group cursor-pointer flex flex-col items-center justify-center p-4 bg-card/30 border border-white/5 rounded-xl hover:bg-card/60 transition-colors"
                       onClick={() => handleNavigate(item.path)}
                     >
                       <Folder className="w-12 h-12 text-primary/70 group-hover:text-primary transition-colors mb-2" />
                       <p className="text-sm font-medium text-center truncate w-full px-2" title={item.name}>{item.name}</p>
                     </div>
                   ) : (
                     <ContextMenu key={item.name}>
                       <ContextMenuTrigger>
                         <div className="relative group cursor-context-menu flex flex-col p-2 bg-card/30 border border-white/5 rounded-xl hover:bg-card/60 transition-colors h-full">
                           {/* Status Dot */}
                           <div className="absolute top-3 right-3 z-10">
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger>
                                    <div className={`w-3 h-3 rounded-full border border-black/50 shadow-sm ${
                                      item.status === 'rotten' ? 'bg-destructive' :
                                      item.status === 'warning' ? 'bg-yellow-500' : 'bg-emerald-500'
                                    }`} />
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>{item.status === 'rotten' ? 'Bit-Rot Detected' : item.status === 'warning' ? 'Truncated/Warning' : 'Clean'}</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                           </div>

                           {/* Thumbnail Mock */}
                           <div className="aspect-square bg-black/40 rounded-lg mb-2 flex items-center justify-center overflow-hidden border border-white/5 group-hover:border-white/10 transition-colors">
                              {item.name.endsWith('.jpg') || item.name.endsWith('.cr2') ? (
                                <ImageIcon className="w-8 h-8 text-muted-foreground/30" />
                              ) : (
                                <File className="w-8 h-8 text-muted-foreground/30" />
                              )}
                           </div>

                           <div className="mt-auto">
                             <p className="text-xs font-medium truncate w-full text-white/90" title={item.name}>{item.name}</p>
                             <p className="text-[10px] text-muted-foreground mt-0.5">{formatSize(item.size)}</p>
                           </div>
                         </div>
                       </ContextMenuTrigger>
                       <ContextMenuContent className="w-64 bg-card/95 backdrop-blur-md border-white/10">
                         <ContextMenuItem onClick={() => handleContextAction("Scan File for Bit-Rot", item)} className="gap-2 cursor-pointer">
                           <Scan className="w-4 h-4 text-primary" /> Scan File for Bit-Rot
                         </ContextMenuItem>
                         <ContextMenuSeparator className="bg-white/5" />
                         <ContextMenuItem onClick={() => handleContextAction("Copy Absolute Path", item)} className="gap-2 cursor-pointer">
                           <Copy className="w-4 h-4" /> Copy Absolute Path
                         </ContextMenuItem>
                         <ContextMenuItem onClick={() => handleContextAction("Move File Asset", item)} className="gap-2 cursor-pointer">
                           <ArrowRightLeft className="w-4 h-4" /> Move File Asset
                         </ContextMenuItem>
                         <ContextMenuItem onClick={() => handleContextAction("Rename File", item)} className="gap-2 cursor-pointer">
                           <Edit2 className="w-4 h-4" /> Rename File
                         </ContextMenuItem>
                         <ContextMenuSeparator className="bg-white/5" />
                         <ContextMenuItem onClick={() => handleContextAction("Delete File", item)} className="gap-2 text-destructive focus:bg-destructive/10 focus:text-destructive cursor-pointer">
                           <Trash2 className="w-4 h-4" /> Delete File
                           <ContextMenuShortcut>⌫</ContextMenuShortcut>
                         </ContextMenuItem>
                       </ContextMenuContent>
                     </ContextMenu>
                   )
                 ))}
               </div>
             )}
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}
