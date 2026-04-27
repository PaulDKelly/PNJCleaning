import os
import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sys

# Add the root directory to path so we can import models/dependencies from backend
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "backend", ".env"))

from app import models, security
from app.dependencies import role_required

app = FastAPI(title="Visual Studio - Platform Manager")

# Templates: search both local Studio templates and backend base templates
templates = Jinja2Templates(directory=[
    "builder/templates",
    os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "templates")
])

# Mount static files (sharing backend/app/static for logos/branding)
app.mount("/static", StaticFiles(directory="../backend/app/static"), name="static")

class SaveSchemaRequest(BaseModel):
    module_id: str
    schema: dict

@app.get("/", response_class=HTMLResponse)
def studio_home(request: Request):
    # Pass a mock user to trigger the Admin Sidebar in base.html
    mock_user = {
        "full_name": "Studio Admin",
        "role": "admin"
    }
    return templates.TemplateResponse("visual_builder.html", {
        "request": request,
        "user": mock_user,
        "settings": {"onedrive_link": "#"},
        "config": {"app_name": "Visual Studio", "logo_path": "/static/logo.jpeg"}
    })

@app.post("/save")
async def save_module_to_live_app(req: SaveSchemaRequest):
    module_id = req.module_id.strip().lower().replace(" ", "_")
    
    # Paths to Live App
    live_app_root = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
    live_app_modules_dir = os.path.join(live_app_root, "app", "modules")
    config_path = os.path.join(live_app_root, "config.json")
    
    # 1. Create Module Directory Structure
    module_dir = os.path.join(live_app_modules_dir, module_id)
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)
        
    # Ensure __init__.py exists for the module loader in the live app
    init_file = os.path.join(module_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("")
            
    # 2. Save the published schema.json to the live app
    schema_path = os.path.join(module_dir, "schema.json")
    with open(schema_path, "w") as f:
        json.dump(req.schema, f, indent=4)

    # 3. Auto-Register module in live app's config.json
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_data = json.load(f)
            
            if "modules" not in config_data:
                config_data["modules"] = []
                
            if module_id not in config_data["modules"]:
                config_data["modules"].append(module_id)
                with open(config_path, "w") as f:
                    json.dump(config_data, f, indent=4)
                    print(f"Registered module '{module_id}' in {config_path}")
    except Exception as e:
        print(f"Error auto-registering module: {e}")
        
    return JSONResponse(content={
        "status": "published", 
        "module_id": module_id,
        "path": f"/dynamic-report/{module_id}"
    })

if __name__ == "__main__":
    import uvicorn
    # Studio runs on port 8001
    uvicorn.run(app, host="0.0.0.0", port=8001)
