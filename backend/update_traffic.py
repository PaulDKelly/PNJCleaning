import json
import yaml
import subprocess

# 1. Fetch current config
try:
    subprocess.run("az containerapp show -n pnj-cleaning-backend -g rg-pnj-cleaning -o json > config_traffic.json", shell=True, check=True)
except:
    print("Failed to fetch config")
    exit(1)

content = ""
try:
    with open("config_traffic.json", "r", encoding="utf-16") as f:
        content = f.read()
except:
    with open("config_traffic.json", "r", encoding="utf-8") as f:
        content = f.read()

config = json.loads(content)

# 2. Modify Config
if 'properties' not in config:
    if isinstance(config, list):
         config = config[0]

# Set Traffic to explicit revision
# We know the revision is pnj-cleaning-backend--0000004
# But let's find the latest just in case or hardcode if we are sure.
# We will hardcode to the one we saw in logs: pnj-cleaning-backend--0000004

config['properties']['configuration']['ingress']['traffic'] = [
    {
        "revisionName": "pnj-cleaning-backend--0000004",
        "weight": 100
    }
]

# Ensure latestRevision is NOT set (it acts as a floating label otherwise)
# Actually, the API usually allows specific revision + weight.

# 3. Write to YAML
with open("app_traffic.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f)

print("Created app_traffic.yaml")
