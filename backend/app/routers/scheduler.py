from datetime import datetime
import re
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .. import models
from ..supabase_client import supabase
from ..dependencies import templates, login_required, role_required
from ..utils import generate_whatsapp_link

router = APIRouter()


def _get_next_job_number() -> str:
    """Generate the next sequential PNJ job number: pnj0001, pnj0002, ..."""
    res = supabase.table("jobs").select("job_number").execute()
    max_num = 0
    pattern = re.compile(r"^pnj(\d+)$", re.IGNORECASE)

    for row in (res.data or []):
        job_no = (row.get("job_number") or "").strip()
        match = pattern.match(job_no)
        if match:
            max_num = max(max_num, int(match.group(1)))

    return f"pnj{max_num + 1:04d}"

@router.get("/portal/{token}", response_class=HTMLResponse)
def engineer_portal(token: str, request: Request):
    try:
        import uuid
        uuid.UUID(token)
        res = supabase.table("engineers").select("*").eq("access_token", token).execute()
        if not res.data:
            raise HTTPException(status_code=403, detail="Invalid Access Token")
        engineer = models.Engineer(**res.data[0])
    except ValueError:
         raise HTTPException(status_code=403, detail="Invalid Token Format")

    today_str = datetime.now().strftime('%Y-%m-%d')
    j_res = supabase.table("jobs").select("*").eq("engineer_contact_name", engineer.contact_name).eq("date", today_str).order("time").execute()
    today_jobs = [models.Job(**j) for j in j_res.data]
    
    for job in today_jobs:
        job.wa_link = generate_whatsapp_link(job, engineer, request.url.netloc)

    return templates.TemplateResponse("engineer_dashboard.html", {
        "request": request,
        "engineer": engineer,
        "token": token,
        "today_jobs": today_jobs
    })

@router.get("/api/engineer/{token}/events")
def get_engineer_events(token: str):
    res = supabase.table("engineers").select("*").eq("access_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Invalid Token")
    engineer = models.Engineer(**res.data[0])
    
    events = []
    j_res = supabase.table("jobs").select("*").eq("engineer_contact_name", engineer.contact_name).execute()
    for j in j_res.data:
        job = models.Job(**j)
        start_dt = f"{job.date}T{job.time}"
        events.append({
            "title": f"{job.client_name} ({job.priority})",
            "start": start_dt,
            "backgroundColor": "#3b82f6",
            "borderColor": "#2563eb",
            "extendedProps": {
                "location": job.address or job.site_name,
                "status": job.status
            }
        })
        
    l_res = supabase.table("leave_requests").select("*").eq("engineer_name", engineer.contact_name).execute()
    for l in l_res.data:
        color = "#ef4444"
        if l['status'] == 'Approved':
            color = "#22c55e"
        elif l['status'] == 'Rejected':
            color = "#94a3b8"
            
        events.append({
            "title": f"Leave: {l['reason']}",
            "start": l['start_date'],
            "end": l['end_date'],
            "color": color,
            "allDay": True
        })
    return JSONResponse(content=events)

@router.post("/api/engineer/{token}/leave")
async def submit_leave_request(token: str, request: Request):
    res = supabase.table("engineers").select("*").eq("access_token", token).execute()
    if not res.data:
        return HTMLResponse("<div class='alert alert-error'>Invalid Token</div>")
    engineer = models.Engineer(**res.data[0])
    
    form_data = await request.form()
    leave_data = {
        "engineer_name": engineer.contact_name,
        "start_date": form_data.get("start_date"),
        "end_date": form_data.get("end_date"),
        "reason": form_data.get("reason"),
        "status": "Pending"
    }
    
    try:
        supabase.table("leave_requests").insert(leave_data).execute()
        return HTMLResponse("""
            <div class='alert alert-success'><span>Request submitted successfully!</span></div>
            <script>
                if(window.calendar) window.calendar.refetchEvents();
                setTimeout(() => { document.getElementById('leave_modal').close(); document.getElementById('leave-feedback').innerHTML = ''; }, 1500);
            </script>
        """)
    except Exception as e:
        return HTMLResponse(f"<div class='alert alert-error'>Error: {str(e)}</div>")

@router.get("/api/admin/events")
def get_admin_events(user: models.User = Depends(login_required)):
    events = []
    j_res = supabase.table("jobs").select("*").execute()
    for j in j_res.data:
        job = models.Job(**j)
        start_dt = f"{job.date}T{job.time}"
        events.append({
            "id": job.id,
            "title": f"[{job.engineer_contact_name}] {job.client_name}",
            "start": start_dt,
            "backgroundColor": "#3b82f6" if job.status != "Completed" else "#10b981",
            "extendedProps": { "location": job.address, "engineer": job.engineer_contact_name }
        })
    return JSONResponse(content=events)

@router.get("/admin/leaves/pending")
def get_pending_leaves(request: Request, user: models.User = Depends(login_required)):
    res = supabase.table("leave_requests").select("*").eq("status", "Pending").execute()
    leaves = [models.LeaveRequest(**l) for l in res.data]
    return templates.TemplateResponse("partials/pending_leaves.html", {"request": request, "leaves": leaves})

@router.post("/admin/leaves/{id}/{action}")
def update_leave_status(id: int, action: str, user: models.User = Depends(login_required)):
    status_map = {"approve": "Approved", "reject": "Rejected"}
    new_status = status_map.get(action, "Pending")
    supabase.table("leave_requests").update({"status": new_status}).eq("id", id).execute()
    return HTMLResponse(f"<span>{new_status}</span>")

@router.post("/admin/book-leave")
async def book_leave_for_staff(request: Request, user: models.User = Depends(login_required)):
    form_data = await request.form()
    leave_data = {
        "engineer_name": form_data.get("engineer_name"),
        "start_date": form_data.get("start_date"),
        "end_date": form_data.get("end_date"),
        "reason": form_data.get("reason"),
        "status": "Approved"
    }
    supabase.table("leave_requests").insert(leave_data).execute()
    return RedirectResponse(url="/management", status_code=303)

@router.get("/management", response_class=HTMLResponse)
def management_dashboard(request: Request, user: models.User = Depends(role_required(["Admin", "Manager"]))):
    engineers_res = supabase.table("engineers").select("*").execute()
    engineers = [models.Engineer(**e) for e in engineers_res.data]
    return templates.TemplateResponse("manager_diary.html", {"request": request, "engineers": engineers, "user": user})

@router.get("/engineer-diary", response_class=HTMLResponse)
def engineer_diary(request: Request, user: models.User = Depends(login_required)):
    # Fetch jobs where the user is the assigned engineer (check both username and email for robustness)
    # Using multiple queries because Supabase OR syntax is a bit specific via postgrest
    # But clean way with .or_ or multiple .eq
    query = supabase.table("jobs").select("*")
    
    # Check for engineer_contact_name matching username OR engineer_email matching user email
    res = query.or_(f"engineer_contact_name.eq.{user.username},engineer_email.eq.{user.email}").order("date").order("time").execute()
    jobs = [models.Job(**j) for j in res.data] if res.data else []
    
    return templates.TemplateResponse("engineer_diary.html", {
        "request": request, 
        "user": user,
        "jobs": jobs
    })

@router.get("/engineer/diary")
def engineer_diary_redirect():
    return RedirectResponse(url="/engineer-diary")

@router.get("/job-allocation", response_class=HTMLResponse)
def job_allocation_page(request: Request, user: models.User = Depends(login_required)):
    # Fetch data for dropdowns
    brands_res = supabase.table("brands").select("*").execute()
    brands = brands_res.data if brands_res.data else []
    
    clients_res = supabase.table("clients").select("*").eq("archived", False).order("client_name").execute()
    clients = clients_res.data if clients_res.data else []
    
    engineers_res = supabase.table("engineers").select("*").order("contact_name").execute()
    engineers = engineers_res.data if engineers_res.data else []
    
    contacts_res = supabase.table("site_contacts").select("*").order("contact_name").execute()
    site_contacts = contacts_res.data if contacts_res.data else []
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    next_job_number = _get_next_job_number()
    
    return templates.TemplateResponse("job_allocation.html", {
        "request": request, 
        "user": user,
        "brands": brands,
        "clients": clients,
        "engineers": engineers,
        "site_contacts": site_contacts,
        "today": today_str,
        "next_job_number": next_job_number
    })

@router.post("/job-allocation")
async def allocate_job(
    request: Request,
    date: str = Form(...),
    time: str = Form(...),
    priority: str = Form(...),
    client_name: str = Form(...),
    site_id: Optional[int] = Form(None),
    brand_name: Optional[str] = Form(None),
    engineer_name: str = Form(...),
    site_contact_name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    user: models.User = Depends(login_required)
):
    try:
        requested_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        if requested_dt < datetime.now():
            return HTMLResponse(content=f"<div class='alert alert-error font-bold'>Error: Cannot allocate a job in the past ({requested_dt.strftime('%d/%m/%Y %H:%M')})</div>", status_code=400)

        site_name_val = None
        company_val = None
        address_val = None
        
        if site_id:
            s_res = supabase.table("client_sites").select("*").eq("id", site_id).execute()
            if s_res.data:
                site = s_res.data[0]
                site_name_val = site['site_name']
                company_val = site['site_name']
                address_val = site['address']
        
        if not site_name_val:
            c_res = supabase.table("clients").select("*").eq("client_name", client_name).execute()
            if c_res.data:
                client = c_res.data[0]
                company_val = client.get('company') or client['client_name']
                address_val = client.get('address')
        
        created_job_number = None
        for _ in range(3):
            next_job_number = _get_next_job_number()
            job_data = {
                "job_number": next_job_number,
                "date": date,
                "time": time,
                "priority": priority,
                "client_name": client_name,
                "engineer_contact_name": engineer_name,
                "site_contact_name": site_contact_name,
                "notes": notes,
                "brand": brand_name,
                "site_name": site_name_val,
                "company": company_val,
                "address": address_val,
                "status": "Scheduled"
            }
            try:
                supabase.table("jobs").insert(job_data).execute()
                created_job_number = next_job_number
                break
            except Exception as e:
                if "duplicate" in str(e).lower():
                    continue
                raise

        if not created_job_number:
            raise Exception("Could not allocate a unique PNJ job number after multiple attempts.")

        res_job = supabase.table("jobs").select("*").eq("job_number", created_job_number).execute()
        job_obj = models.Job(**res_job.data[0])
        res_eng = supabase.table("engineers").select("*").eq("contact_name", engineer_name).execute()
        eng_obj = models.Engineer(**res_eng.data[0]) if res_eng.data else None
        wa_link = generate_whatsapp_link(job_obj, eng_obj, request.url.netloc)
        wa_btn = f"<script>window.open('{wa_link}', '_blank');</script>" if wa_link else ""

        next_job_number = _get_next_job_number()
        return HTMLResponse(content=(
            f"<div class='alert alert-success italic font-bold'>"
            f"Job {created_job_number} successfully allocated & Dispatched!"
            f"</div>"
            f"<script>"
            f"const jobInput = document.getElementById('job-number-input');"
            f"if (jobInput) jobInput.value = '{next_job_number}';"
            f"</script>"
            f"{wa_btn}"
        ))
    except Exception as e:
        return HTMLResponse(content=f"<div class='alert alert-error'>Error: {str(e)}</div>", status_code=400)

@router.post("/admin/jobs/{job_number}/archive")
def archive_job(job_number: str, user: models.User = Depends(login_required)):
    supabase.table("jobs").update({"status": "Archived"}).eq("job_number", job_number).execute()
    return HTMLResponse(content="<span class='badge badge-ghost font-bold italic'>Archived</span>")

@router.get("/admin/jobs/archive/search", response_class=HTMLResponse)
def search_archive(q: str = "", user: models.User = Depends(login_required)):
    query = supabase.table("jobs").select("*").eq("status", "Archived")
    if q:
        filter_str = f"job_number.ilike.%{q}%,client_name.ilike.%{q}%,site_name.ilike.%{q}%"
        query = query.or_(filter_str)
    res = query.order("date", desc=True).execute()
    jobs = [models.Job(**j) for j in res.data]
    
    html_rows = "".join([f"""<tr class="opacity-75 hover:opacity-100 transition-opacity">
        <td class="p-4 font-medium text-slate-500">{j.date.strftime('%d %b %Y')}</td>
        <td><span class="badge badge-ghost font-mono text-[10px]">{j.job_number}</span></td>
        <td><div class="font-bold text-slate-600">{j.client_name}</div><div class="text-[9px] uppercase tracking-tighter text-slate-400">{j.site_name or 'N/A'}</div></td>
        <td><span class="badge badge-outline badge-xs font-bold">{j.status}</span></td>
        <td class="text-right"><a href="/admin/reports" class="btn btn-ghost btn-xs text-indigo-500 font-bold underline">View Audit</a></td>
    </tr>""" for j in jobs])
    return HTMLResponse(content=html_rows or "<tr><td colspan='5' class='text-center py-20 text-slate-400 italic'>No matches found in archive.</td></tr>")
