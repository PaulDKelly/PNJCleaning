import json
import importlib
import os
from fastapi import FastAPI

def load_modules(app: FastAPI):
    """
    Dynamically loads domain modules listed in config.json.
    Each module should have a router.py with a 'router' object.
    """
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    
    try:
        if not os.path.exists(config_path):
            print(f"Configuration file not found: {config_path}", flush=True)
            return
            
        # Use utf-8-sig to handle optional BOM
        with open(config_path, "r", encoding="utf-8-sig") as f:
            config = json.load(f)
            
        enabled_modules = config.get("modules", [])
        print(f"MODULAR_ENGINE: Attempting to load: {enabled_modules}", flush=True)
        
        for module_name in enabled_modules:
            try:
                module_path = f"app.modules.{module_name}.router"
                module = importlib.import_module(module_path)
                
                if hasattr(module, "router"):
                    app.include_router(module.router, tags=[module_name.capitalize()])
                    print(f"MODULAR_ENGINE: Loaded module: {module_name}", flush=True)
                else:
                    print(f"MODULAR_ENGINE: Module {module_name} has no router", flush=True)
                    
            except Exception as e:
                print(f"MODULAR_ENGINE: Error loading {module_name}: {str(e)}", flush=True)
                
    except Exception as e:
        print(f"MODULAR_ENGINE: Fatal error: {str(e)}", flush=True)
