import yaml

config = {
    "properties": {
        "managedEnvironmentId": "", # Will be filled by CLI if we omit or passed by arg? Actually better to let CLI handle env binding or look it up.
        # For 'create --yaml', we usually provide the full body.
        # But 'az containerapp create --yaml' expects the structure.
        # Easier: generate the body and use 'az containerapp create --yaml'?
        # Actually 'az containerapp create' with yaml might require the Environment ID.
        
        "configuration": {
            "ingress": {
                "external": True,
                "targetPort": 8000,
                "transport": "auto",
                "traffic": [
                    {
                        "weight": 100,
                        "latestRevision": True
                    }
                ]
            },
            "activeRevisionsMode": "Single"
        },
        "template": {
            "containers": [
                {
                    "image": "ca3fbe3e88bbacr.azurecr.io/pnj-cleaning-backend:cli-containerapp-20260202091056284595",
                    "name": "pnj-backend-web",
                    "env": [
                        {"name": "SUPABASE_URL", "value": "https://ruaseemcgxvbcjazhhfw.supabase.co"},
                        {"name": "SUPABASE_KEY", "value": "sb_publishable_dPA9xqq4yyGg6869fCuMLA_tCXIKXOu"},
                        {"name": "SECRET_KEY", "value": "supersecretkeyforpnjcleaning"}
                    ],
                    "probes": [
                        {
                            "type": "Liveness",
                            "httpGet": {"path": "/login", "port": 8000, "scheme": "HTTP"},
                            "periodSeconds": 10, "failureThreshold": 3, "timeoutSeconds": 2
                        },
                        {
                            "type": "Readiness",
                            "httpGet": {"path": "/login", "port": 8000, "scheme": "HTTP"},
                            "periodSeconds": 10, "failureThreshold": 3, "timeoutSeconds": 2
                        },
                        {
                            "type": "Startup",
                            "httpGet": {"path": "/login", "port": 8000, "scheme": "HTTP"},
                            "periodSeconds": 10, "failureThreshold": 3, "timeoutSeconds": 2
                        }
                    ]
                }
            ],
            "scale": {
                "minReplicas": 1,
                "maxReplicas": 10
            }
        }
    }
}

# We need to look up the Environment ID first to be safe, or just pass --environment to the CLI and hope it merges?
# If we use --yaml, we usually need to specify everything or the CLI merges.
# Let's try to just output the properties part or the 'container-app' structure.
# Reference: https://learn.microsoft.com/en-us/azure/container-apps/azure-resource-manager-api-spec

wrapper = {
    "location": "uksouth",
    "properties": config["properties"]
}

with open("app_fresh.yaml", "w") as f:
    yaml.dump(wrapper, f)

print("Created app_fresh.yaml")
