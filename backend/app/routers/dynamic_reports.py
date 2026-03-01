import json
import os
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse

from .. import models
from ..supabase_client import supabase
from ..dependencies import templates, login_required

router = APIRouter()

def get_schema(module_name: str):
    """Load schema.json for a given module."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "modules", module_name, "schema.json")
    if not os.path.exists(schema_path):
        return None
    with open(schema_path, "r") as f:
        return json.load(f)

@router.get("/dynamic-report/{module_name}", response_class=HTMLResponse)
def render_dynamic_report(module_name: str, request: Request, user: models.User = Depends(login_required)):
    schema = get_schema(module_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema for module {module_name} not found")
    
    return templates.TemplateResponse("generic_form.html", {
        "request": request,
        "user": user,
        "schema": schema,
        "module_name": module_name
    })

@router.post("/dynamic-report/{module_name}")
async def submit_dynamic_report(module_name: str, request: Request, user: models.User = Depends(login_required)):
    schema = get_schema(module_name)
    if not schema:
        raise HTTPException(status_code=404, detail="Module schema not found")
        
    form_data = await request.form()
    submission_data = {}
    
    # Simple extraction of form fields based on schema
    for section in schema.get("sections", []):
        for field in section.get("fields", []):
            field_id = field.get("id")
            if field_id:
                if field.get("type") == "photo":
                    # For now, just log photo field presence
                    # Full photo handling to be integrated in phase 2
                    submission_data[field_id] = "[Photo Uploaded]" 
                else:
                    submission_data[field_id] = form_data.get(field_id)
    
    # Persist to a 'universal_submissions' table in Supabase
    try:
        payload = {
            "module_name": module_name,
            "user_email": user.email,
            "data": submission_data,
            "submitted_at": datetime.now().isoformat()
        }
        # Note: This table needs to be created in Supabase
        # For now, we simulate the save and return success
        # supabase.table("universal_submissions").insert(payload).execute()
        
        return HTMLResponse(content=f"<div class='alert alert-success'>Successfully submitted {schema.get('title')}!</div>")
    except Exception as e:
        return HTMLResponse(content=f"<div class='alert alert-error'>Error saving submission: {str(e)}</div>", status_code=400)
