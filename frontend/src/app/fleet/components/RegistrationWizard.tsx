import * as React from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { toast } from "sonner"
import { Copy, Server, Globe, Download, AlertTriangle } from "lucide-react"

export function RegistrationWizard({ token }: { token: string | null }) {
  const [open, setOpen] = React.useState(false)
  const [step, setStep] = React.useState(1)
  const [deploymentType, setDeploymentType] = React.useState("local")
  const [loading, setLoading] = React.useState(false)
  const [certData, setCertData] = React.useState<{ certificate: string, private_key: string, node_id: string } | null>(null)

  const handleNext = () => setStep(s => s + 1)
  const handleBack = () => setStep(s => s - 1)

  const handleRegister = async () => {
    if (!token) return
    setLoading(true)
    try {
      const res = await fetch("/api/fleet/register", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          is_local_only: deploymentType === "local"
        })
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Failed to register node")
      }

      const data = await res.json()
      setCertData(data)
      setStep(4)
    } catch (err: unknown) {
      toast.error((err as Error).message || "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  const downloadCerts = () => {
    if (!certData) return
    const zipContent = `Certificate:\n${certData.certificate}\n\nPrivate Key:\n${certData.private_key}\n\nNode ID: ${certData.node_id}`
    const blob = new Blob([zipContent], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `kintsugi-node-${certData.node_id}-certs.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success("Copied to clipboard")
  }

  // Reset wizard on close
  React.useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setStep(1)
        setDeploymentType("local")
        setCertData(null)
      }, 300)
    }
  }, [open])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button>Register New Node</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] bg-black/90 border-white/10 backdrop-blur-xl">
        <DialogHeader>
          <DialogTitle>Fleet Node Registration</DialogTitle>
          <DialogDescription>
            Deploy a new Kintsugi-DAM node to your cluster.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {step === 1 && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium">Step 1: Deployment Type</h3>
              <RadioGroup value={deploymentType} onValueChange={setDeploymentType} className="gap-4">
                <div className={`flex items-start space-x-3 space-y-0 rounded-md border p-4 ${deploymentType === "local" ? "border-primary bg-primary/5" : "border-white/10"}`}>
                  <RadioGroupItem value="local" id="local" className="mt-1" />
                  <Label htmlFor="local" className="flex flex-col cursor-pointer">
                    <span className="flex items-center text-base font-semibold"><Server className="w-4 h-4 mr-2" /> Local Node (Location Locked)</span>
                    <span className="font-normal text-muted-foreground mt-1">
                      Best for NAS devices on the same secure studio network. Does not require complex mTLS reverse proxying.
                    </span>
                  </Label>
                </div>
                <div className={`flex items-start space-x-3 space-y-0 rounded-md border p-4 ${deploymentType === "remote" ? "border-primary bg-primary/5" : "border-white/10"}`}>
                  <RadioGroupItem value="remote" id="remote" className="mt-1" />
                  <Label htmlFor="remote" className="flex flex-col cursor-pointer">
                    <span className="flex items-center text-base font-semibold"><Globe className="w-4 h-4 mr-2" /> Remote Node (External)</span>
                    <span className="font-normal text-muted-foreground mt-1">
                      For cloud nodes or remote studios. Requires configuring your reverse proxy to forward mTLS client certificates.
                    </span>
                  </Label>
                </div>
              </RadioGroup>
            </div>
          )}

          {step === 2 && deploymentType === "remote" && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Step 2: Proxy Configuration</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Since this is a remote node, you must configure your reverse proxy to forward the client certificate details to the main server.
              </p>

              <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label className="font-semibold">Nginx Proxy Manager</Label>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(`proxy_set_header X-SSL-Client-SHA1 $ssl_client_fingerprint;
proxy_set_header X-SSL-Client-DN $ssl_client_s_dn;
proxy_set_header X-SSL-Client-Verify $ssl_client_verify;`)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                  <pre className="bg-white/5 p-3 rounded-md text-xs font-mono border border-white/10 overflow-x-auto">
{`proxy_set_header X-SSL-Client-SHA1 $ssl_client_fingerprint;
proxy_set_header X-SSL-Client-DN $ssl_client_s_dn;
proxy_set_header X-SSL-Client-Verify $ssl_client_verify;`}
                  </pre>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label className="font-semibold">Caddy</Label>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(`header_up X-SSL-Client-SHA1 {tls_client_fingerprint}
header_up X-SSL-Client-DN {tls_client_subject}
header_up X-SSL-Client-Verify {tls_client_verify}`)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                  <pre className="bg-white/5 p-3 rounded-md text-xs font-mono border border-white/10 overflow-x-auto">
{`header_up X-SSL-Client-SHA1 {tls_client_fingerprint}
header_up X-SSL-Client-DN {tls_client_subject}
header_up X-SSL-Client-Verify {tls_client_verify}`}
                  </pre>
                </div>

                 <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label className="font-semibold">Cloudflare Tunnels</Label>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(`Requires Cloudflare mTLS. The backend will read: Cf-Client-Cert-Der-Base64`)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                  <pre className="bg-white/5 p-3 rounded-md text-xs font-mono border border-white/10 overflow-x-auto">
{`Requires Cloudflare mTLS. The backend will read: Cf-Client-Cert-Der-Base64`}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {(step === 2 && deploymentType === "local") || step === 3 ? (
            <div className="space-y-6 text-center py-8">
              <Server className="w-16 h-16 mx-auto text-primary opacity-80" />
              <h3 className="text-xl font-bold">Ready to Provision</h3>
              <p className="text-muted-foreground">
                Click below to generate the cryptographic identity for this node.
              </p>
            </div>
          ) : null}

          {step === 4 && certData && (
            <div className="space-y-4">
              <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-md flex gap-3">
                <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-semibold text-red-500">Warning: One-time view</p>
                  <p className="text-muted-foreground mt-1">This certificate and private key will only be shown once and cannot be retrieved later. Download it now.</p>
                </div>
              </div>

              <div className="space-y-2">
                 <Label>Node ID</Label>
                 <Input readOnly value={certData.node_id} className="bg-white/5 font-mono text-xs" />
              </div>

              <div className="pt-4 flex justify-center">
                <Button onClick={downloadCerts} size="lg" className="gap-2">
                  <Download className="w-4 h-4" /> Download Certificate Bundle
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-between mt-4">
          {step > 1 && step < 4 ? (
            <Button variant="outline" onClick={handleBack} disabled={loading}>Back</Button>
          ) : <div></div>}

          {step === 1 && (
            <Button onClick={deploymentType === "local" ? () => setStep(3) : handleNext}>Next</Button>
          )}

          {step === 2 && deploymentType === "remote" && (
            <Button onClick={handleNext}>Next</Button>
          )}

          {((step === 2 && deploymentType === "local") || step === 3) && (
            <Button onClick={handleRegister} disabled={loading}>
              {loading ? "Provisioning..." : "Provision Node"}
            </Button>
          )}

          {step === 4 && (
            <Button onClick={() => setOpen(false)} variant="outline">Done</Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
