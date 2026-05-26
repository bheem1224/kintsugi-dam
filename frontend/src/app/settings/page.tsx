"use client"
import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useAuth } from "@/context/AuthContext"
import { toast } from "sonner"
import { Save } from "lucide-react"

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
  const { token } = useAuth()
  const [schema, setSchema] = React.useState<Schema | null>(null)
  const [values, setValues] = React.useState<Record<string, unknown>>({})
  const [loading, setLoading] = React.useState(true)
  const [saving, setSaving] = React.useState(false)
  const [categories, setCategories] = React.useState<CategorizedSettings>({})

  React.useEffect(() => {
    if (!token) return

    const fetchSchemaAndSettings = async () => {
      try {
        // Fetch schema
        const schemaRes = await fetch("/api/settings/schema", {
          headers: { "Authorization": `Bearer ${token}` }
        })
        if (!schemaRes.ok) throw new Error("Failed to fetch schema")
        const schemaData: Schema = await schemaRes.json()
        setSchema(schemaData)

        // Fetch current settings
        const settingsRes = await fetch("/api/settings", {
          headers: { "Authorization": `Bearer ${token}` }
        })
        if (!settingsRes.ok) throw new Error("Failed to fetch settings")
        const settingsData: Record<string, unknown> = await settingsRes.json()
        setValues(settingsData)

        // Group into categories
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
            cats["Remediation"].push({ key, field: f })
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

        // Remove empty categories
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
  }, [token])

  const handleSave = async () => {
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

  const handleChange = (key: string, value: unknown) => {
    setValues(prev => ({ ...prev, [key]: value }))
  }

  if (loading) return <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>

  const categoryKeys = Object.keys(categories)

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
          <p className="text-muted-foreground mt-2">Manage your Kintsugi-DAM configuration.</p>
        </div>
        <Button onClick={handleSave} disabled={saving} className="gap-2">
          <Save className="w-4 h-4" />
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </div>

      <Tabs defaultValue={categoryKeys[0]} className="w-full">
        <TabsList className="mb-4">
          {categoryKeys.map(cat => (
            <TabsTrigger key={cat} value={cat}>{cat}</TabsTrigger>
          ))}
        </TabsList>

        {categoryKeys.map(cat => (
          <TabsContent key={cat} value={cat}>
            <Card className="bg-black/40 border-white/10 backdrop-blur-md">
              <CardHeader>
                <CardTitle>{cat} Configuration</CardTitle>
                <CardDescription>Adjust settings related to {cat.toLowerCase()}.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {categories[cat].map(({ key, field }) => (
                  <div key={key} className="flex flex-col space-y-2 pb-4 border-b border-white/5 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-base font-medium">{field.title || key}</Label>
                        {field.description && (
                          <p className="text-sm text-muted-foreground">{field.description}</p>
                        )}
                      </div>

                      {field.type === "boolean" ? (
                        <Switch
                          checked={values[key] === true}
                          onCheckedChange={(c) => handleChange(key, c)}
                        />
                      ) : (
                        <div className="w-1/2">
                          <Input
                            type={field.type === "int" ? "number" : "text"}
                            value={values[key] !== undefined ? (values[key] as string | number) : ((field.default || "") as string | number)}
                            onChange={(e) => handleChange(key, field.type === "int" ? parseInt(e.target.value) : e.target.value)}
                            className="bg-white/5 border-white/10"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
