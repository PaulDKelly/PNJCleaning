import json
import yaml
import subprocess

# 1. Fetch current config
try:
    subprocess.run("az containerapp show -n pnj-backend-web -g rg-pnj-cleaning -o json > config_fresh.json", shell=True, check=True)
except:
    print("Failed to fetch")
    exit(1)

content = ""
try:
    with open("config_fresh.json", "r", encoding="utf-16") as f:
        content = f.read()
except:
    with open("config_fresh.json", "r", encoding="utf-8") as f:
        content = f.read()

config = json.loads(content)
if isinstance(config, list): config = config[0]

# 2. Apply Fixes

# A. Env Vars
container = config['properties']['template']['containers'][0]
container['env'] = [
    {"name": "SUPABASE_URL", "value": "https://ruaseemcgxvbcjazhhfw.supabase.co"},
    {"name": "SUPABASE_KEY", "value": "sb_publishable_dPA9xqq4yyGg6869fCuMLA_tCXIKXOu"},
    {"name": "SECRET_KEY", "value": "supersecretkeyforpnjcleaning"}
]

# B. Probes
probe_def = {
    "type": "Liveness", # Will be overwritten by type
    "httpGet": {"path": "/login", "port": 8000, "scheme": "HTTP"},
    "periodSeconds": 10, "failureThreshold": 3, "timeoutSeconds": 2
}
container['probes'] = [
    dict(probe_def, type="Liveness"),
    dict(probe_def, type="Readiness"),
    dict(probe_def, type="Startup")
]

# C. Scaling
if 'scale' not in config['properties']['template'] or config['properties']['template']['scale'] is None:
    config['properties']['template']['scale'] = {}
config['properties']['template']['scale']['minReplicas'] = 1

# D. Ingress
if 'ingress' not in config['properties']['configuration'] or config['properties']['configuration']['ingress'] is None:
    config['properties']['configuration']['ingress'] = {}
config['properties']['configuration']['ingress']['targetPort'] = 8000

# 3. Save
with open("app_fix.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f)
print("Created app_fix.yaml")
