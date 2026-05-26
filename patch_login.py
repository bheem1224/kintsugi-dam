import re

with open("frontend/src/app/login/page.tsx", "r") as f:
    content = f.read()

# Add react-hook-form imports
imports_to_add = """
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
"""
content = content.replace('import { useRouter } from "next/navigation"', 'import { useRouter } from "next/navigation"\n' + imports_to_add)

# Add isShaking state
state_to_add = """
  const [isShaking, setIsShaking] = React.useState(false)

  const loginSchema = z.object({
    username: z.string().min(1, "Username is required"),
    password: z.string().min(1, "Password is required"),
  })

  type LoginFormValues = z.infer<typeof loginSchema>

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  })
"""
content = content.replace('const router = useRouter()', 'const router = useRouter()\n' + state_to_add)

# Replace handleLogin function
handle_login_old = """  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const formData = new URLSearchParams()
      formData.append("username", username)
      formData.append("password", password)

      const res = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        localStorage.setItem("token", data.access_token)
        if (setupRequired) {
          paginate(2)
        } else {
          login(data.access_token)
        }
      } else {
        const data = await res.json()
        setError(data.detail || "Authentication failed")
      }
    } catch (err) {
      setError("Network error. Please ensure the backend is running.")
    } finally {
      setLoading(false)
    }
  }"""

handle_login_new = """  const handleLoginSubmit = async (values: LoginFormValues) => {
    setError("")
    setLoading(true)

    try {
      const formData = new URLSearchParams()
      formData.append("username", values.username)
      formData.append("password", values.password)

      const res = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        localStorage.setItem("token", data.access_token)
        if (setupRequired) {
          paginate(2)
        } else {
          login(data.access_token)
          router.push("/")
        }
      } else {
        if (res.status === 403) {
           const data = await res.json()
           if (data.error === "ip_restricted") {
              setIsShaking(true)
              setTimeout(() => setIsShaking(false), 500)
              toast.error("Access Denied: You must be on the local studio network to log into this account.", {
                style: { backgroundColor: 'red', color: 'white', border: 'none' }
              })
              setError("Access Denied: IP Restricted.")
              setLoading(false)
              return
           }
        }
        const data = await res.json()
        setError(data.detail || "Invalid credentials")
      }
    } catch (err) {
      setError("Network error. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  // Wrapper for the non-react-hook-form wizard submission
  const handleLogin = async () => {
     handleLoginSubmit({ username, password });
  }
"""

content = content.replace(handle_login_old, handle_login_new)

# Replace the Card form area
form_old = """              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2"><label className="text-sm font-medium">Username</label><input className="w-full bg-white/5 border border-white/10 rounded-md p-2" value={username} onChange={(e) => setUsername(e.target.value)} required /></div>
                <div className="space-y-2"><label className="text-sm font-medium">Password</label><input className="w-full bg-white/5 border border-white/10 rounded-md p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
                {error && <div className="text-xs text-red-500">{error}</div>}
                <Button type="submit" className="w-full transition-all hover:-translate-y-0.5 hover:shadow-lg" disabled={loading}>{loading ? "Authenticating..." : "Sign In"}</Button>
              </form>"""

form_new = """              <Form {...form}>
                <form onSubmit={form.handleSubmit(handleLoginSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="username"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Username</FormLabel>
                        <FormControl>
                          <Input className="w-full bg-white/5 border border-white/10 rounded-md p-2" {...field} onChange={(e) => { field.onChange(e); setUsername(e.target.value) }} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Password</FormLabel>
                        <FormControl>
                          <Input type="password" className="w-full bg-white/5 border border-white/10 rounded-md p-2" {...field} onChange={(e) => { field.onChange(e); setPassword(e.target.value) }} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  {error && <div className="text-xs text-red-500">{error}</div>}
                  <Button type="submit" className="w-full transition-all hover:-translate-y-0.5 hover:shadow-lg" disabled={loading}>{loading ? "Authenticating..." : "Sign In"}</Button>
                </form>
              </Form>"""

content = content.replace(form_old, form_new)

# Add shake animation to card wrapper
card_wrapper_old = """          <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl">"""
card_wrapper_new = """          <motion.div
            animate={isShaking ? { x: [-10, 10, -10, 10, -5, 5, -2, 2, 0] } : {}}
            transition={{ duration: 0.5 }}
          >
            <Card className="shadow-2xl border-white/10 bg-black/50 backdrop-blur-xl">"""

card_end_old = """          </Card>
        </div>"""
card_end_new = """          </Card>
          </motion.div>
        </div>"""

content = content.replace(card_wrapper_old, card_wrapper_new, 1) # Only replace the first one (non-setup)
content = content.replace(card_end_old, card_end_new, 1)

with open("frontend/src/app/login/page.tsx", "w") as f:
    f.write(content)

print("Patch applied")
