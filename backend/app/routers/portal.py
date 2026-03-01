from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse

from .. import models
from ..supabase_client import supabase
from ..dependencies import templates, login_required

router = APIRouter()

@router.get("/client-portal/{token}", response_class=HTMLResponse)
def client_portal(token: str, request: Request):
    """Public client portal - no login required"""
    client_res = supabase.table("clients").select("*").eq("portal_token", token).execute()
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    client = models.Client(**client_res.data[0])
    jobs_res = supabase.table("jobs").select("*").eq("client_name", client.client_name).eq("status", "Archived").order("date", desc=True).execute()
    jobs = [models.Job(**j) for j in jobs_res.data] if jobs_res.data else []
    return templates.TemplateResponse("client_portal.html", {
        "request": request,
        "client": client,
        "jobs": jobs,
        "is_admin_preview": False
    })

@router.get("/admin/portal-preview", response_class=HTMLResponse)
def admin_portal_preview(request: Request, user: models.User = Depends(login_required)):
    """Admin page to preview client portals"""
    clients_res = supabase.table("clients").select("*").order("client_name").execute()
    clients = [models.Client(**c) for c in clients_res.data] if clients_res.data else []
    return templates.TemplateResponse("admin_portal_preview.html", {
        "request": request,
        "title": "Portal Preview",
        "user": user,
        "clients": clients
    })

@router.get("/admin/portal-preview/{client_name}", response_class=HTMLResponse)
def admin_portal_preview_client(client_name: str, request: Request, user: models.User = Depends(login_required)):
    """Admin preview of specific client portal"""
    client_res = supabase.table("clients").select("*").eq("client_name", client_name).execute()
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Client not found")
    client = models.Client(**client_res.data[0])
    jobs_res = supabase.table("jobs").select("*").eq("client_name", client.client_name).eq("status", "Archived").order("date", desc=True).execute()
    jobs = [models.Job(**j) for j in jobs_res.data] if jobs_res.data else []
    return templates.TemplateResponse("client_portal.html", {
        "request": request,
        "client": client,
        "jobs": jobs,
        "is_admin_preview": True,
        "user": user
    })

@router.get("/client-portal/{token}/report/{job_number}", response_class=HTMLResponse)
def portal_view_report(token: str, job_number: str, request: Request):
    """View report in client portal"""
    client_res = supabase.table("clients").select("*").eq("portal_token", token).execute()
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    client = models.Client(**client_res.data[0])
    
    report_res = supabase.table("extraction_reports").select("*").eq("job_number", job_number).execute()
    if not report_res.data:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        report = models.ExtractionReport(**report_res.data[0])
    except Exception:
        fallback = dict(report_res.data[0])
        # Prevent template crashes on malformed legacy values.
        fallback["date"] = None
        fallback["time"] = None
        report = models.ExtractionReport(**fallback)
    
    job_res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
    if not job_res.data or job_res.data[0]['client_name'] != client.client_name:
        raise HTTPException(status_code=403, detail="Access denied")
    
    micron_readings = [models.ExtractionMicronReading(**m) for m in supabase.table("extraction_micron_readings").select("*").eq("report_id", report.id).execute().data]
    inspection_items = [models.ExtractionInspectionItem(**i) for i in supabase.table("extraction_inspection_items").select("*").eq("report_id", report.id).execute().data]
    filter_items = [models.ExtractionFilterItem(**f) for f in supabase.table("extraction_filter_items").select("*").eq("report_id", report.id).execute().data]
    photos = [models.ExtractionPhoto(**p) for p in supabase.table("extraction_photos").select("*").eq("report_id", report.id).execute().data]
    
    return templates.TemplateResponse("report_view_portal.html", {
        "request": request,
        "report": report,
        "micron_readings": micron_readings,
        "inspection_items": inspection_items,
        "filter_items": filter_items,
        "photos": photos,
        "client": client,
        "token": token,
        "is_admin_preview": False
    })

@router.get("/client-portal/{token}/pdf/{job_number}")
def portal_download_pdf(token: str, job_number: str):
    """Download PDF report from client portal"""
    client_res = supabase.table("clients").select("*").eq("portal_token", token).execute()
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    client = models.Client(**client_res.data[0])
    job_res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
    if not job_res.data or job_res.data[0]['client_name'] != client.client_name:
        raise HTTPException(status_code=403, detail="Access denied")
    return HTMLResponse(content="<h1>PDF Generation Coming Soon</h1><p>This feature will generate a downloadable PDF report.</p>")
