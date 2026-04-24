import re

with open('frontend/src/app/page.tsx', 'r') as f:
    content = f.read()

# Add CheckCircle to lucide-react imports
if 'CheckCircle' not in content:
    content = content.replace('ShieldAlert, Cpu', 'ShieldAlert, Cpu, CheckCircle')

# Replace the empty state UI
old_empty_state = """      {corruptedFiles.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed">
          <p className="text-lg font-medium">All clear</p>
          <p className="text-sm text-muted-foreground mt-1">No corrupted files detected in the active library.</p>
        </div>
      ) : ("""

new_empty_state = """      {corruptedFiles.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed">
          <CheckCircle className="w-12 h-12 text-primary mb-4" />
          <p className="text-lg font-medium">All clear</p>
          <p className="text-sm text-muted-foreground mt-1">No corrupted files detected in the active library.</p>
        </div>
      ) : ("""

content = content.replace(old_empty_state, new_empty_state)

with open('frontend/src/app/page.tsx', 'w') as f:
    f.write(content)

print("Updated page.tsx")
