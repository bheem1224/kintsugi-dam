with open("frontend/src/components/layout/Header.tsx", "r") as f:
    content = f.read()

content = content.replace('<SheetTrigger asChild>', '<SheetTrigger>')

with open("frontend/src/components/layout/Header.tsx", "w") as f:
    f.write(content)
