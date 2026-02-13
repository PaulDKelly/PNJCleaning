import json
import yaml
import os

# 1. Read config.json
# Handle potential PowerShell encoding (UTF-16LE)
content = ""
try:
    with open("config.json", "r", encoding="utf-16") as f:
        content = f.read()
except:
    with open("config.json", "r", encoding="utf-8") as f:
        content = f.read()

config = json.loads(content)

# 2. Modify Config
# Update Image
if 'properties' not in config:
    # Sometimes output might be list?
    if isinstance(config, list):
         config = config[0]

config['properties']['template']['containers'][0]['image'] = "ca3fbe3e88bbacr.azurecr.io/pnj-cleaning-backend:cli-containerapp-20260202091056284595"

# Update Ingress Port
config['properties']['configuration']['ingress']['targetPort'] = 8000

# 3. Write to YAML
with open("app_update.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f)

print("Created app_update.yaml")
