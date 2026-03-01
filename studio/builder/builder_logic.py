import os
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .. import models
from ..dependencies import templates, role_required

router = APIRouter()

class SaveSchemaRequest(BaseModel):
    module_id: str
    schema: dict

@router.get("/admin/builder", response_class=HTMLResponse)
def visual_builder(request: Request, user: models.User = Depends(role_required(["Admin"]))):
    return templates.TemplateResponse("visual_builder.html", {
        "request": request,
        "user": user
    })

@router.post("/admin/builder/save")
async def save_module_schema(
    req: SaveSchemaRequest,
    user: models.User = Depends(role_required(["Admin"]))
):
    module_id = req.module_id.strip().lower().replace(" ", "_")
    module_dir = os.path.join(os.path.dirname(__file__), "..", "modules", module_id)
    
    # Create module directory if it doesn't exist
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)
        
    # Create __init__.py and a default empty router if needed
    # (Phase 3 will automate complex router logic, for now we just need the folder + schema)
    init_file = os.path.join(module_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("")
            
    # Save schema.json
    schema_path = os.path.join(module_dir, "schema.json")
    with open(schema_path, "w") as f:
        json.dump(req.schema, f, indent=4)
        
    return JSONResponse(content={"status": "success", "module_id": module_id})
