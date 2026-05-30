import re

with open("frontend/src/app/page.tsx", "r") as f:
    content = f.read()

# Remove the duplicated variable assignment
content = content.replace("  const { stats, loading } = useSystem()", "  const { loading } = useSystem()")

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(content)
