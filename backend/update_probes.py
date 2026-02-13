import json
import yaml
import subprocess

# 1. Fetch current config
try:
    subprocess.run("az containerapp show -n pnj-cleaning-backend -g rg-pnj-cleaning -o json > config_probes.json", shell=True, check=True)
except:
    print("Failed to fetch config")
    exit(1)

content = ""
try:
    with open("config_probes.json", "r", encoding="utf-16") as f:
        content = f.read()
except:
    with open("config_probes.json", "r", encoding="utf-8") as f:
        content = f.read()

config = json.loads(content)

# 2. Modify Config
if 'properties' not in config:
    if isinstance(config, list):
         config = config[0]

container = config['properties']['template']['containers'][0]

# Define Probes
probes = [
    {
        "type": "Liveness",
        "httpGet": {
            "path": "/login",
            "port": 8000,
            "scheme": "HTTP"
        },
        "periodSeconds": 10,
        "failureThreshold": 3,
        "timeoutSeconds": 2
    },
    {
        "type": "Readiness",
        "httpGet": {
            "path": "/login",
            "port": 8000,
            "scheme": "HTTP"
        },
        "periodSeconds": 10,
        "failureThreshold": 3,
        "timeoutSeconds": 2
    },
    {
        "type": "Startup",
        "httpGet": {
            "path": "/login",
            "port": 8000,
            "scheme": "HTTP"
        },
        "periodSeconds": 10,
        "failureThreshold": 3,
        "timeoutSeconds": 2
    }
]

container['probes'] = probes

# Ensure Image is set (sometimes lost in partial updates if not careful, though usually fine)
container['image'] = "ca3fbe3e88bbacr.azurecr.io/pnj-cleaning-backend:cli-containerapp-20260202091056284595"

# Ensure Ingress is correct
if 'ingress' in config['properties']['configuration']:
    config['properties']['configuration']['ingress']['targetPort'] = 8000

# 3. Write to YAML
with open("app_probes.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f)

print("Created app_probes.yaml")
