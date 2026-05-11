import json
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

    try:
        sub_contractors_res = supabase.table("sub_contractors").select("*").order("client_name").order("sub_contractor_name").execute()
        sub_contractors = [models.SubContractor(**s) for s in sub_contractors_res.data] if sub_contractors_res.data else []
    except Exception:
        sub_contractors = []
    
    admins_res = supabase.table("users").select("*").execute()
    admins = [models.User(**a) for a in admins_res.data] if admins_res.data else []
    
    settings_res = supabase.table("system_settings").select("*").execute()
    settings_dict = {s['key']: s['value'] for s in settings_res.data} if settings_res.data else {}
    
    try:
        report_notification_settings = json.loads(settings_dict.get("report_notification_recipients", "[]"))
    except json.JSONDecodeError:
        report_notification_settings = []
    notification_by_user_id = {
        int(item.get("user_id")): item for item in report_notification_settings if str(item.get("user_id", "")).isdigit()
    }

    settings = {
        "onedrive_link": settings_dict.get("onedrive_link", "https://onedrive.live.com"),
        "report_notifications": notification_by_user_id
    }
    
    return templates.TemplateResponse("manage_lists.html", {
        "request": request,
        "title": "Administrators Panel",
        "user": user,
        "clients": clients,
        "sites": sites,
        "brands": brands,
        "engineers": engineers,
        "sub_contractors": sub_contractors,
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


@router.post("/admin/manage/notification-settings")
async def update_notification_settings(request: Request, user: models.User = Depends(role_required(["Admin"]))):
    form_data = await request.form()
    selected_user_ids = set(form_data.getlist("notify_user_id"))
    recipients = []

    for raw_user_id in selected_user_ids:
        if not str(raw_user_id).isdigit():
            continue
        recipients.append({
            "user_id": int(raw_user_id),
            "email": form_data.get(f"notify_email_{raw_user_id}") == "1",
            "whatsapp": form_data.get(f"notify_whatsapp_{raw_user_id}") == "1",
            "whatsapp_number": (form_data.get(f"notify_whatsapp_number_{raw_user_id}") or "").strip()
        })

    payload = json.dumps(recipients)
    check_res = supabase.table("system_settings").select("*").eq("key", "report_notification_recipients").execute()
    if check_res.data:
        supabase.table("system_settings").update({"value": payload}).eq("key", "report_notification_recipients").execute()
    else:
        supabase.table("system_settings").insert({"key": "report_notification_recipients", "value": payload}).execute()

    return RedirectResponse(url="/admin/manage?success=notifications_updated", status_code=303)

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
    normalized_email = (email or "").strip().lower()
    existing = get_user_by_email(normalized_email)
    if existing:
        return RedirectResponse(url="/admin/manage?error=email_exists", status_code=303)
    
    hashed_password = security.get_password_hash(password)
    supabase.table("users").insert({
        "username": username,
        "email": normalized_email,
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
    update_data = {"username": username, "email": (email or "").strip().lower(), "role": role}
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
