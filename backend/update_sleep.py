import json
import yaml
import os

# 1. Read config.json (generated from `show`)
# We assume config.json exists from previous step or we regenerate it.
# Let's try to read 'config.json' if it exists, else fetch.
# Actually, let's just use the known structure for a minimal update or fetch fresh.
import subprocess
try:
    # re-fetch to be safe
    subprocess.run("az containerapp show -n pnj-cleaning-backend -g rg-pnj-cleaning -o json > config_sleep.json", shell=True, check=True)
except:
    pass

content = ""
try:
    with open("config_sleep.json", "r", encoding="utf-16") as f:
        content = f.read()
except:
    with open("config_sleep.json", "r", encoding="utf-8") as f:
        content = f.read()

config = json.loads(content)

# 2. Modify Config
if 'properties' not in config:
    if isinstance(config, list):
         config = config[0]

# Ensure we use the backend image
config['properties']['template']['containers'][0]['image'] = "ca3fbe3e88bbacr.azurecr.io/pnj-cleaning-backend:cli-containerapp-20260202091056284595"

# Override Command
config['properties']['template']['containers'][0]['command'] = ["/bin/sh", "-c", "while true; do echo hello; sleep 10; done"]

# Ensure args are empty if they were set
if 'args' in config['properties']['template']['containers'][0]:
    del config['properties']['template']['containers'][0]['args']

# Ingress: keeping external but port shouldn't matter as we sleep.
# Ingress: DISABLE to avoid probing issues during sleep
config['properties']['configuration']['ingress'] = None
# Or strict disable if needed, but None usually removes it.
# Actually, better to remove the key or set to minimal.
if 'ingress' in config['properties']['configuration']:
    del config['properties']['configuration']['ingress']


# 3. Write to YAML
with open("app_sleep.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f)

print("Created app_sleep.yaml")
