import re

with open("frontend/src/app/layout.tsx", "r") as f:
    content = f.read()

# Add <Toaster /> inside body
if "<Toaster />" not in content:
    content = content.replace("</body>", "  <Toaster />\n      </body>")
    content = content.replace('import { Toaster } from "@/components/ui/toaster"', 'import { Toaster } from "@/components/ui/sonner"')

with open("frontend/src/app/layout.tsx", "w") as f:
    f.write(content)

print("Toaster added to layout")
