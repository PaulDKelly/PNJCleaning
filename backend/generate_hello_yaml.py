import yaml

config = {
    "name": "pnj-backend-web",
    "location": "uksouth",
    "properties": {
        "configuration": {
            "ingress": {
                "external": True,
                "targetPort": 80, # Hello world uses 80
                "transport": "auto"
            },
            "activeRevisionsMode": "Single"
        },
        "template": {
            "containers": [
                {
                    "image": "mcr.microsoft.com/k8s/samples/helloworld:latest",
                    "name": "pnj-backend-web", # must match?
                    "resources": {"cpu": 0.5, "memory": "1.0Gi"}
                }
            ],
            "scale": {
                "minReplicas": 1
            }
        }
    }
}

with open("app_hello.yaml", "w") as f:
    yaml.dump(config, f)
print("Created app_hello.yaml")
