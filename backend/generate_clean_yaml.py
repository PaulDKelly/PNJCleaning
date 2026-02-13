import json
import yaml

# 1. Fetch
# We assume config_fresh.json exists (from previous step 931)
# Or we can read it again? Let's assume it's there or read it.
# Actually let's just use the file logic.

try:
    with open("config_fresh.json", "r", encoding="utf-8") as f:
        content = f.read()
except:
    with open("config_fresh.json", "r", encoding="utf-16") as f:
        content = f.read()

config = json.loads(content)
if isinstance(config, list): config = config[0]

# 2. Extract specific sections we want to update
# Instead of sending the whole object (which has read-only fields), let's construct a minimal update object.
# 'az containerapp update --yaml' usually wants:
# {
#   "name": ...,
#   "properties": { ... }
# }

new_config = {
    "name": config.get("name"),
    "location": config.get("location"),
    "properties": {
        "configuration": config['properties']['configuration'],
        "template": config['properties']['template'],
        "environmentId": config['properties'].get("environmentId")
    }
}

# 3. Patch

# A. Env Vars in Template
container = new_config['properties']['template']['containers'][0]
container['env'] = [
    {"name": "SUPABASE_URL", "value": "https://ruaseemcgxvbcjazhhfw.supabase.co"},
    {"name": "SUPABASE_KEY", "value": "sb_publishable_dPA9xqq4yyGg6869fCuMLA_tCXIKXOu"},
    {"name": "SECRET_KEY", "value": "supersecretkeyforpnjcleaning"}
]

# B. Probes
probe_def = {
    "type": "Liveness",
    "httpGet": {"path": "/login", "port": 8000, "scheme": "HTTP"},
    "periodSeconds": 10, "failureThreshold": 3, "timeoutSeconds": 2
}
container['probes'] = [
    dict(probe_def, type="Liveness"),
    dict(probe_def, type="Readiness"),
    dict(probe_def, type="Startup")
]

# C. Scaling
if 'scale' not in new_config['properties']['template'] or new_config['properties']['template']['scale'] is None:
    new_config['properties']['template']['scale'] = {}
new_config['properties']['template']['scale']['minReplicas'] = 1

# D. Ingress
if 'ingress' not in new_config['properties']['configuration'] or new_config['properties']['configuration']['ingress'] is None:
    new_config['properties']['configuration']['ingress'] = {}
new_config['properties']['configuration']['ingress']['targetPort'] = 8000
new_config['properties']['configuration']['ingress']['external'] = True # Ensure external

# 4. Save
with open("app_clean.yaml", "w", encoding="utf-8") as f:
    yaml.dump(new_config, f)

print("Created app_clean.yaml")
