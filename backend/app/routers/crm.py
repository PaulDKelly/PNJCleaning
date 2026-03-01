import secrets
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import models
from ..supabase_client import supabase
from ..dependencies import templates, login_required

router = APIRouter()

@router.get("/admin/sites-lookup", response_class=HTMLResponse)
def get_sites_for_client(
    client_name: Optional[str] = None, 
    brand_name: Optional[str] = None,
    user: models.User = Depends(login_required)
):
    query = supabase.table("client_sites").select("*").eq("archived", False)
    if client_name:
        query = query.eq("client_name", client_name)
    if brand_name:
        query = query.eq("brand_name", brand_name)
    res = query.order("site_name").execute()
    sites = [models.ClientSite(**s) for s in res.data]
    options = "".join([f'<option value="{s.id}">{s.site_name}</option>' for s in sites])
    return HTMLResponse(content=f'<option value="">Select a Site (Optional)</option>{options}')

@router.get("/admin/clients-lookup", response_class=HTMLResponse)
def get_clients_lookup(
    brand_name: Optional[str] = None,
    user: models.User = Depends(login_required)
):
    if brand_name:
        sites = supabase.table("client_sites").select("client_name").eq("brand_name", brand_name).execute().data
        client_names = list(set([s['client_name'] for s in sites]))
        if not client_names:
            return HTMLResponse(content='<option value="">All Clients (None found)</option>')
        res = supabase.table("clients").select("*").in_("client_name", client_names).order("client_name").execute()
    else:
        res = supabase.table("clients").select("*").order("client_name").execute()
    clients = [models.Client(**c) for c in res.data]
    options = "".join([f'<option value="{c.client_name}">{c.client_name}</option>' for c in clients])
    return HTMLResponse(content=f'<option value="">All Clients</option>{options}')

@router.get("/admin/manage/clients-table", response_class=HTMLResponse)
def get_clients_table(
    request: Request,
    client_name: Optional[str] = None,
    brand_name: Optional[str] = None,
    site_id: Optional[str] = None,
    user: models.User = Depends(login_required)
):
    target_client_names = None
    if site_id and site_id.isdigit():
        site_res = supabase.table("client_sites").select("client_name").eq("id", int(site_id)).execute()
        if site_res.data:
            target_client_names = [site_res.data[0]['client_name']]
    elif brand_name:
        sites = supabase.table("client_sites").select("client_name").eq("brand_name", brand_name).execute().data
        target_client_names = list(set([s['client_name'] for s in sites]))
        
    query = supabase.table("clients").select("*")
    if client_name:
        query = query.eq("client_name", client_name)
    if target_client_names is not None:
        query = query.in_("client_name", target_client_names)
        
    res = query.order("client_name").execute()
    clients = [models.Client(**c) for c in res.data]
    all_sites = supabase.table("client_sites").select("*").execute().data
    sites_objs = [models.ClientSite(**s) for s in all_sites]

    return templates.TemplateResponse("partials/clients_table_rows.html", {
        "request": request,
        "clients": clients,
        "sites": sites_objs
    })

@router.get("/admin/manage/sites-table", response_class=HTMLResponse)
def get_sites_table(
    request: Request,
    client_name: Optional[str] = None, 
    brand_name: Optional[str] = None,
    show_archived: bool = False,
    user: models.User = Depends(login_required)
):
    query = supabase.table("client_sites").select("*")
    if client_name:
        query = query.eq("client_name", client_name)
    if brand_name:
        query = query.eq("brand_name", brand_name)
    if not show_archived:
        query = query.eq("archived", False)
        
    res = query.order("site_name").execute()
    sites = [models.ClientSite(**s) for s in res.data]
    brands_res = supabase.table("brands").select("*").execute()
    brands = [models.Brand(**b) for b in brands_res.data]
    
    return templates.TemplateResponse("partials/sites_table_rows.html", {
        "request": request,
        "sites": sites,
        "brands": brands
    })

@router.post("/admin/manage/clients/{client_name}/archive")
def archive_client(client_name: str, user: models.User = Depends(login_required)):
    supabase.table("clients").update({"archived": True}).eq("client_name", client_name).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshClients"})

@router.post("/admin/manage/clients/{client_name}/restore")
def restore_client(client_name: str, user: models.User = Depends(login_required)):
    supabase.table("clients").update({"archived": False}).eq("client_name", client_name).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshClients"})

@router.post("/admin/manage/sites/{site_id}/archive")
def archive_site(site_id: int, user: models.User = Depends(login_required)):
    supabase.table("client_sites").update({"archived": True}).eq("id", site_id).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshSites"})

@router.post("/admin/manage/sites/{site_id}/restore")
def restore_site(site_id: int, user: models.User = Depends(login_required)):
    supabase.table("client_sites").update({"archived": False}).eq("id", site_id).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshSites"})

@router.post("/admin/manage/sites/bulk-archive")
async def bulk_archive_sites(request: Request, user: models.User = Depends(login_required)):
    form = await request.form()
    site_ids = form.getlist("site_ids")
    if site_ids:
        ids = [int(i) for i in site_ids]
        supabase.table("client_sites").update({"archived": True}).in_("id", ids).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshSites"})

@router.post("/admin/manage/clients/add")
def add_client(client_name: str = Form(...), company: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    portal_token = secrets.token_urlsafe(32)
    supabase.table("clients").insert({
        "client_name": client_name,
        "company": company,
        "address": address,
        "portal_token": portal_token
    }).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.post("/admin/manage/clients/edit/{client_name}")
def edit_client(client_name: str, company: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("clients").update({
        "company": company,
        "address": address
    }).eq("client_name", client_name).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.post("/admin/manage/sites/add")
def add_site(client_name: str = Form(...), site_name: str = Form(...), address: str = Form(...), brand_name: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("client_sites").insert({
        "client_name": client_name,
        "site_name": site_name,
        "address": address,
        "brand_name": brand_name if brand_name else None
    }).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.post("/admin/manage/sites/edit/{site_id}")
def edit_site(site_id: int, site_name: str = Form(...), address: str = Form(...), brand_name: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("client_sites").update({
        "site_name": site_name,
        "address": address,
        "brand_name": brand_name if brand_name else None
    }).eq("id", site_id).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.post("/admin/manage/brands/add")
def add_brand(brand_name: str = Form(...), user: models.User = Depends(login_required)):
    supabase.table("brands").insert({"brand_name": brand_name}).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.post("/admin/manage/brands/edit/{brand_id}")
def edit_brand(brand_id: int, brand_name: str = Form(...), user: models.User = Depends(login_required)):
    supabase.table("brands").update({"brand_name": brand_name}).eq("id", brand_id).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.delete("/admin/manage/brands/{brand_id}")
def delete_brand(brand_id: int, user: models.User = Depends(login_required)):
    supabase.table("brands").delete().eq("id", brand_id).execute()
    return HTMLResponse(content="")

@router.post("/admin/manage/engineers/add")
def add_engineer(contact_name: str = Form(...), email: str = Form(None), phone: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("engineers").insert({
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "address": address
    }).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.post("/admin/manage/engineers/edit/{contact_name}")
def edit_engineer(contact_name: str, email: str = Form(None), phone: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("engineers").update({
        "email": email,
        "phone": phone,
        "address": address
    }).eq("contact_name", contact_name).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@router.delete("/admin/manage/engineers/{contact_name}")
def delete_engineer(contact_name: str, user: models.User = Depends(login_required)):
    supabase.table("engineers").delete().eq("contact_name", contact_name).execute()
    return HTMLResponse(content="")
