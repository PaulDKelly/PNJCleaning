from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import models, security
from ..supabase_client import supabase
from ..dependencies import templates, login_required, role_required, get_user_by_email

router = APIRouter()

@router.get("/admin/manage", response_class=HTMLResponse)
def admin_manage(request: Request, user: models.User = Depends(role_required(["Admin", "Manager"]))):
    """Admin management panel for clients, sites, brands, engineers, and admins"""
    clients_res = supabase.table("clients").select("*").execute()
    clients = [models.Client(**c) for c in clients_res.data] if clients_res.data else []
    
    sites_res = supabase.table("client_sites").select("*").execute()
    sites = [models.ClientSite(**s) for s in sites_res.data] if sites_res.data else []
    
    brands_res = supabase.table("brands").select("*").execute()
    brands = [models.Brand(**b) for b in brands_res.data] if brands_res.data else []
    
    engineers_res = supabase.table("engineers").select("*").execute()
    engineers = [models.Engineer(**e) for e in engineers_res.data] if engineers_res.data else []
    
    admins_res = supabase.table("users").select("*").execute()
    admins = [models.User(**a) for a in admins_res.data] if admins_res.data else []
    
    settings_res = supabase.table("system_settings").select("*").execute()
    settings_dict = {s['key']: s['value'] for s in settings_res.data} if settings_res.data else {}
    
    settings = {
        "onedrive_link": settings_dict.get("onedrive_link", "https://onedrive.live.com")
    }
    
    return templates.TemplateResponse("manage_lists.html", {
        "request": request,
        "title": "Administrators Panel",
        "user": user,
        "clients": clients,
        "sites": sites,
        "brands": brands,
        "engineers": engineers,
        "admins": admins,
        "settings": settings
    })

@router.post("/admin/manage/settings")
async def update_settings(request: Request, user: models.User = Depends(role_required(["Admin"]))):
    form_data = await request.form()
    for key, value in form_data.items():
        check_res = supabase.table("system_settings").select("*").eq("key", key).execute()
        if check_res.data:
            supabase.table("system_settings").update({"value": value}).eq("key", key).execute()
        else:
            supabase.table("system_settings").insert({"key": key, "value": value}).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.post("/admin/manage/users/add")
async def add_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("Admin"),
    user: models.User = Depends(login_required)
):
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Access denied")
    existing = get_user_by_email(email)
    if existing:
        return RedirectResponse(url="/admin/manage?error=email_exists", status_code=303)
    
    hashed_password = security.get_password_hash(password)
    supabase.table("users").insert({
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": role
    }).execute()
    return RedirectResponse(url="/admin/manage?success=user_added", status_code=303)

@router.post("/admin/manage/users/edit/{user_id}")
async def edit_user(
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: Optional[str] = Form(None),
    role: str = Form("Admin"),
    user: models.User = Depends(login_required)
):
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Access denied")
    update_data = {"username": username, "email": email, "role": role}
    if password:
        update_data["password"] = security.get_password_hash(password)
    supabase.table("users").update(update_data).eq("id", user_id).execute()
    return RedirectResponse(url="/admin/manage?success=user_updated", status_code=303)

@router.delete("/admin/manage/users/{user_id}")
def delete_user(user_id: int, user: models.User = Depends(login_required)):
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if user.id == user_id:
        return HTMLResponse(content="<div class='alert alert-warning'>Cannot delete yourself!</div>", status_code=400)
    supabase.table("users").delete().eq("id", user_id).execute()
    return HTMLResponse(content="")
