"use client"
import * as React from "react"
import { useForm } from "react-hook-form"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useAuth } from "@/context/AuthContext"
import { toast } from "sonner"
import { Save, Plus, ArrowDown, DatabaseBackup, Cloud, Sparkles, UserCheck, Clock, ShieldAlert } from "lucide-react"

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"

type SchemaField = {
  type: "string" | "int" | "boolean"
  title: string
  description?: string
  default?: unknown
}

type Schema = {
  [key: string]: SchemaField
}

type CategorizedSettings = {
  [category: string]: { key: string, field: SchemaField }[]
}

export default function SettingsPage() {
  const { token, user } = useAuth()
  const [schema, setSchema] = React.useState<Schema | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [saving, setSaving] = React.useState(false)
  const [categories, setCategories] = React.useState<CategorizedSettings>({})

  const form = useForm({
    defaultValues: {} as Record<string, any>
  })

  React.useEffect(() => {
    if (!token) return

    const fetchSchemaAndSettings = async () => {
      try {
        const schemaRes = await fetch("/api/settings/schema", {
          headers: { "Authorization": `Bearer ${token}` }
        })
        if (!schemaRes.ok) throw new Error("Failed to fetch schema")
        const schemaData: Schema = await schemaRes.json()
        setSchema(schemaData)

        const settingsRes = await fetch("/api/settings", {
          headers: { "Authorization": `Bearer ${token}` }
        })
        if (!settingsRes.ok) throw new Error("Failed to fetch settings")
        const settingsData: Record<string, any> = await settingsRes.json()

        // Ensure max_threads exists in form
        if (settingsData.max_threads === undefined) {
            settingsData.max_threads = -1; // Default unlimited
        }

        form.reset(settingsData)

        const cats: CategorizedSettings = {
          "General": [],
          "Remediation": [],
          "AI": [],
          "Network": [],
          "SSO": [],
          "Advanced": []
        }

        Object.entries(schemaData).forEach(([key, field]) => {
          const f = field as SchemaField
          if (key.startsWith("auto_restore") || key.startsWith("retention")) {
            // We handle remediation explicitly in the custom UI, so don't auto-map it here unless it's a generic one
          } else if (key === "max_threads") {
            // Handled via custom QoS Slider in General
          } else if (key.startsWith("ai_") || key.includes("openai") || key.includes("kintsugi_cloud")) {
            cats["AI"].push({ key, field: f })
          } else if (key.includes("webhook") || key.includes("proxy")) {
            cats["Network"].push({ key, field: f })
          } else if (key.startsWith("oidc_") || key.startsWith("saml_")) {
            cats["SSO"].push({ key, field: f })
          } else if (key.includes("directory") || key.includes("path")) {
             cats["General"].push({ key, field: f })
          } else {
             cats["Advanced"].push({ key, field: f })
          }
        })

        Object.keys(cats).forEach(k => {
          if (cats[k].length === 0) delete cats[k]
        })

        setCategories(cats)

      } catch (err) {
        toast.error("Failed to load settings.")
      } finally {
        setLoading(false)
      }
    }

    fetchSchemaAndSettings()
  }, [token, form])

  const onSubmit = async (values: Record<string, any>) => {
    if (!token) return
    setSaving(true)
    try {
      const res = await fetch("/api/settings", {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(values)
      })

      if (!res.ok) {
         const data = await res.json()
         throw new Error(data.detail || "Failed to save settings")
      }

      toast.success("Settings saved successfully.")
    } catch (err: unknown) {
      toast.error((err as Error).message || "Failed to save settings.")
    } finally {
      setSaving(false)
    }
  }

  const isPro = user?.is_pro === true;
  const isStudio = isPro; // Assume Pro = Studio for UI logic based on prompt "Free Tier or Studio Tier"

  if (loading) return <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>

  const categoryKeys = ["General", "Remediation", "AI", "Network", "SSO", "Advanced"].filter(k => k === "Remediation" || categories[k])

  // Custom UI for QoS Slider
  const renderQoSSlider = () => {
     const val = form.watch("max_threads");
     // Map value back to slider index (0 = Low, 1 = Balanced, 2 = Unlimited)
     let sliderValue = 0;
     if (val === 1) sliderValue = 0;
     else if (val > 1 && val <= 5) sliderValue = 1;
     else if (val === -1 || val > 5) sliderValue = 2;

     const handleSliderChange = (v: number | readonly number[]) => { const idx = Array.isArray(v) ? v[0] : v;

         if (idx === 0) form.setValue("max_threads", 1);
         else if (idx === 1) form.setValue("max_threads", 5);
         else form.setValue("max_threads", -1);
     }

     return (
       <Card className="bg-black/40 border-white/10 backdrop-blur-md mb-6">
         <CardHeader>
           <CardTitle>Hardware Extrication QoS</CardTitle>
           <CardDescription>Control how much CPU compute Kintsugi-DAM is allowed to consume for hashing.</CardDescription>
         </CardHeader>
         <CardContent>
           <div className="space-y-6">
              <Slider
                 value={[sliderValue]}
                 max={2}
                 step={1}
                 onValueChange={handleSliderChange}
                 disabled={!isPro}
              />
              <div className="flex justify-between text-sm text-muted-foreground font-medium px-1">
                 <span className={sliderValue === 0 ? "text-primary" : ""}>Low (1 Thread)</span>
                 <span className={sliderValue === 1 ? "text-primary" : ""}>Balanced (1-5 Cores) {isPro ? "" : "🔒"}</span>
                 <span className={sliderValue === 2 ? "text-primary" : ""}>Unlimited (Max) {isStudio ? "" : "🔒"}</span>
              </div>
              {!isPro && (
                 <p className="text-xs text-yellow-500 bg-yellow-500/10 p-2 rounded border border-yellow-500/20">
                   Balanced and Unlimited QoS settings require the Studio Tier.
                 </p>
              )}
           </div>
         </CardContent>
       </Card>
     )
  }

  // Node Component
  const PipelineNode = ({ icon: Icon, title, description }: any) => (
     <div className="bg-card border border-border rounded-xl p-4 flex items-center gap-4 shadow-sm w-full max-w-md mx-auto">
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
           <Icon className="w-5 h-5 text-primary" />
        </div>
        <div>
           <div className="font-semibold text-sm">{title}</div>
           <div className="text-xs text-muted-foreground">{description}</div>
        </div>
     </div>
  );

  // Condition Component
  const ConditionNode = ({ icon: Icon, label, colorClass, children }: any) => (
      <div className={`my-2 p-3 rounded-lg border ${colorClass} bg-background/50 backdrop-blur-sm w-full max-w-sm mx-auto flex flex-col gap-2`}>
         <div className="flex items-center gap-2 text-xs font-semibold">
            <Icon className="w-3.5 h-3.5" />
            {label}
         </div>
         <div className="text-xs">
            {children}
         </div>
      </div>
  );


  // Render Remediation Pipeline
  const renderRemediationPipeline = () => (
      <div className="space-y-8 py-4">
         <div className="text-center space-y-1 mb-8">
            <h2 className="text-2xl font-bold tracking-tight">Programmable Waterfall Pipeline</h2>
            <p className="text-sm text-muted-foreground">Define how Kintsugi-DAM recovers corrupted assets.</p>
         </div>

         <div className="flex flex-col items-center relative">
            <PipelineNode icon={DatabaseBackup} title="Local Snapshot Restore" description="Recover exact bytes from ZFS/BTRFS snapshots." />

            <div className="w-px h-8 bg-border my-2 flex items-center justify-center relative">
               <div className="absolute bg-background p-1 rounded-full border border-border cursor-pointer hover:bg-muted transition-colors">
                  <Plus className="w-3 h-3" />
               </div>
            </div>

            <ConditionNode icon={Clock} label="Custom TTL Override" colorClass="border-blue-500/30 text-blue-500">
               <div className="flex items-center gap-2">
                 <span>Retain original corrupted file for</span>
                 <Input type="number" className="w-16 h-6 text-xs bg-black/40 border-white/10" defaultValue={14} />
                 <span>days.</span>
               </div>
            </ConditionNode>

            <div className="w-px h-8 bg-border my-2 flex items-center justify-center">
                <ArrowDown className="w-4 h-4 text-muted-foreground" />
            </div>

            <PipelineNode icon={Cloud} title="Cloud Recovery Sync" description="Pull clean version from attached S3/B2 storage." />

            <div className="w-px h-8 bg-border my-2 flex items-center justify-center relative">
               <div className="absolute bg-background p-1 rounded-full border border-border cursor-pointer hover:bg-muted transition-colors">
                  <Plus className="w-3 h-3" />
               </div>
            </div>

            <ConditionNode icon={ShieldAlert} label="Require Human Review Gateway" colorClass="border-orange-500/30 text-orange-500">
                <p className="mb-2">Blocks deletion of the source file (TTL: Infinite) until approved in Triage.</p>
                <div className="flex items-center justify-between">
                   <span>Reviewer Role:</span>
                   <Select disabled={!isStudio} defaultValue="any">
                      <SelectTrigger className="w-[140px] h-7 text-xs bg-black/40 border-white/10">
                         <SelectValue placeholder="Select Role" />
                      </SelectTrigger>
                      <SelectContent>
                         <SelectItem value="any">Any User</SelectItem>
                         {isStudio && <SelectItem value="admin">Requires Admin</SelectItem>}
                      </SelectContent>
                   </Select>
                </div>
                {!isStudio && <p className="text-[10px] opacity-70 mt-1">Role filtering requires Studio Tier.</p>}
            </ConditionNode>

            <div className="w-px h-8 bg-border my-2 flex items-center justify-center">
                <ArrowDown className="w-4 h-4 text-muted-foreground" />
            </div>

            <PipelineNode icon={Sparkles} title="Generative AI Infill" description="Synthetically reconstruct missing byte blocks via AI." />
         </div>

      </div>
  );


  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-center bg-card p-6 rounded-xl border border-border shadow-sm">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Configuration</h1>
          <p className="text-muted-foreground mt-1 text-sm">Manage global rules, automation pipelines, and infrastructure.</p>
        </div>
        <Button onClick={form.handleSubmit(onSubmit)} disabled={saving} className="gap-2 shadow-lg shadow-primary/20">
          <Save className="w-4 h-4" />
          {saving ? "Deploying..." : "Commit Changes"}
        </Button>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <Tabs defaultValue="General" className="w-full">
            <TabsList className="mb-6 bg-card border border-border w-full justify-start h-12 p-1 overflow-x-auto flex-nowrap hide-scrollbar">
              {categoryKeys.map(cat => (
                <TabsTrigger key={cat} value={cat} className="rounded-md px-6">{cat}</TabsTrigger>
              ))}
            </TabsList>

            {categoryKeys.map(cat => (
              <TabsContent key={cat} value={cat} className="focus-visible:outline-none focus-visible:ring-0">
                {cat === "General" && renderQoSSlider()}

                {cat === "Remediation" ? (
                   renderRemediationPipeline()
                ) : (
                   categories[cat] && categories[cat].length > 0 && (
                    <Card className="bg-black/40 border-white/10 backdrop-blur-md">
                      <CardHeader>
                        <CardTitle>{cat} Engine</CardTitle>
                        <CardDescription>Adjust native {cat.toLowerCase()} parameters.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        {categories[cat].map(({ key, field }) => (
                          <FormField
                            key={key}
                            control={form.control}
                            name={key}
                            render={({ field: formField }) => (
                              <FormItem className="flex flex-col space-y-2 pb-6 border-b border-white/5 last:border-0 last:pb-0">
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                  <div className="space-y-1 w-full sm:w-2/3">
                                    <FormLabel className="text-base font-medium">{field.title || key}</FormLabel>
                                    {field.description && (
                                      <FormDescription className="text-xs">{field.description}</FormDescription>
                                    )}
                                  </div>

                                  <div className="w-full sm:w-1/3 flex sm:justify-end shrink-0">
                                      {field.type === "boolean" ? (
                                        <FormControl>
                                            <Switch
                                              checked={Boolean(formField.value)}
                                              onCheckedChange={formField.onChange}
                                            />
                                        </FormControl>
                                      ) : (
                                        <FormControl>
                                            <Input
                                              type={field.type === "int" ? "number" : "text"}
                                              {...formField}
                                              value={formField.value !== undefined ? formField.value : ""}
                                              onChange={(e) => {
                                                  const val = e.target.value;
                                                  formField.onChange(field.type === "int" ? (val === "" ? "" : parseInt(val)) : val);
                                              }}
                                              className="bg-white/5 border-white/10 w-full"
                                            />
                                        </FormControl>
                                      )}
                                  </div>
                                </div>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        ))}
                      </CardContent>
                    </Card>
                  )
                )}
              </TabsContent>
            ))}
          </Tabs>
        </form>
      </Form>
    </div>
  )
}
