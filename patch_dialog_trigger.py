with open("frontend/src/app/fleet/components/RegistrationWizard.tsx", "r") as f:
    content = f.read()

content = content.replace('<DialogTrigger asChild>', '<DialogTrigger>')
content = content.replace('</DialogTrigger>', '</DialogTrigger>')

with open("frontend/src/app/fleet/components/RegistrationWizard.tsx", "w") as f:
    f.write(content)
