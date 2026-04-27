from datetime import datetime
import re
import json
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from postgrest.exceptions import APIError

from .. import models
from ..supabase_client import supabase
from ..dependencies import templates, login_required, role_required
from ..utils import generate_whatsapp_link, generate_whatsapp_app_link, get_report_link

router = APIRouter()


def _get_next_job_number() -> str:
    """Generate the first available PNJ number (fills gaps, starts at pnj0001)."""
    res = supabase.table("jobs").select("job_number").execute()
    used_nums = set()
    pattern = re.compile(r"^pnj(\d+)$", re.IGNORECASE)

    for row in (res.data or []):
        job_no = (row.get("job_number") or "").strip()
        match = pattern.match(job_no)
        if match:
            used_nums.add(int(match.group(1)))

    next_num = 1
    while next_num in used_nums:
        next_num += 1

    return f"pnj{next_num:04d}"


def _insert_job(job_data: dict):
    """Insert a job, retrying without job_type if the live schema cache is stale."""
    try:
        return supabase.table("jobs").insert(job_data).execute()
    except APIError as exc:
        error_text = str(exc)
        if "Could not find the 'job_type' column of 'jobs' in the schema cache" not in error_text:
            raise
        fallback_job_data = dict(job_data)
        fallback_job_data.pop("job_type", None)
        if job_data.get("job_type") == "Breakdown/Callout":
            existing_notes = (fallback_job_data.get("notes") or "").strip()
            fallback_job_data["notes"] = f"[CALL OUT] {existing_notes}".strip()
        print("Warning: jobs.job_type missing from schema cache; retrying insert without job_type")
        return supabase.table("jobs").insert(fallback_job_data).execute()

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
        # Color coding: orange for breakdown jobs, blue for regular not completed, green for completed
        if job.job_type == "Breakdown/Callout":
            bg_color = "#f97316"  # orange
        elif job.status != "Completed":
            bg_color = "#3b82f6"  # blue
        else:
            bg_color = "#10b981"  # green
        events.append({
            "id": job.id,
            "title": f"[{job.engineer_contact_name}] {job.client_name}",
            "start": start_dt,
            "backgroundColor": bg_color,
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
    job_number: Optional[str] = Form(None),
    manual_job_override: Optional[str] = Form(None),
    date: str = Form(...),
    time: str = Form(...),
    priority: str = Form(...),
    job_type: str = Form("Extraction"),
    client_name: str = Form(...),
    site_id: Optional[int] = Form(None),
    brand_name: Optional[str] = Form(None),
    engineer_name: str = Form(...),
    site_contact_name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    user: models.User = Depends(login_required)
):
    print(f"JOB ALLOCATION REQUEST: date={date}, time={time}, job_type={job_type}, client={client_name}, engineer={engineer_name}")
    try:
        requested_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        print(f"Parsed datetime: {requested_dt}")
        if requested_dt < datetime.now():
            print("ERROR: Job in the past")
            return HTMLResponse(content=f"<div class='alert alert-error font-bold'>Error: Cannot allocate a job in the past ({requested_dt.strftime('%d/%m/%Y %H:%M')})</div>", status_code=400)

        site_name_val = None
        company_val = None
        address_val = None
        
        if site_id:
            s_res = supabase.table("client_sites").select("*").eq("id", site_id).execute()
            if s_res.data:
                site = s_res.data[0]
                site_name_val = site["site_name"]
                address_val = site.get("address")

        c_res = supabase.table("clients").select("*").eq("client_name", client_name).execute()
        if c_res.data:
            client = c_res.data[0]
            company_val = client.get("company") or client["client_name"]
            if not address_val:
                address_val = client.get("address")

        created_job_number = None
        manual_override_enabled = (manual_job_override == "1")
        allowed_job_types = {"Extraction", "Breakdown/Callout"}
        job_type = job_type if job_type in allowed_job_types else "Extraction"
        print(f"Job type after validation: {job_type}")
        requested_job_number = (job_number or "").strip()

        if manual_override_enabled and requested_job_number:
            job_data = {
                "job_number": requested_job_number,
                "date": date,
                "time": time,
                "priority": priority,
                "job_type": job_type,
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
                # Refresh schema cache
                supabase.table("jobs").select("*").limit(1).execute()
                result = _insert_job(job_data)
                created_job_number = requested_job_number
            except Exception as e:
                if "duplicate" in str(e).lower():
                    return HTMLResponse(
                        content=f"<div class='alert alert-error'>Error: Job number {requested_job_number} already exists.</div>",
                        status_code=400
                    )
                raise
        else:
            for _ in range(3):
                next_job_number = _get_next_job_number()
                job_data = {
                    "job_number": next_job_number,
                    "date": date,
                    "time": time,
                    "priority": priority,
                    "job_type": job_type,
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
                    # Refresh schema cache
                    supabase.table("jobs").select("*").limit(1).execute()
                    result = _insert_job(job_data)
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
        job_obj.job_type = job_type
        res_eng = supabase.table("engineers").select("*").eq("contact_name", engineer_name).execute()
        eng_obj = models.Engineer(**res_eng.data[0]) if res_eng.data else None
        wa_web_link = generate_whatsapp_link(job_obj, eng_obj, request.url.netloc)
        wa_app_link = generate_whatsapp_app_link(job_obj, eng_obj, request.url.netloc)
        report_link = get_report_link(job_obj, request.url.netloc)

        wa_dispatch = ""
        wa_action_html = ""
        if wa_web_link:
            app_js = json.dumps(wa_app_link) if wa_app_link else "null"
            web_js = json.dumps(wa_web_link)
            wa_action_html = f"<a class='btn btn-sm btn-success' href='{wa_web_link}' target='_blank' rel='noopener'>Open WhatsApp</a>"
            wa_dispatch = (
                "<script>"
                f"const waApp = {app_js};"
                f"const waWeb = {web_js};"
                "if (waApp) {"
                "  window.location.href = waApp;"
                "  setTimeout(() => { window.open(waWeb, '_blank'); }, 1200);"
                "} else {"
                "  window.open(waWeb, '_blank');"
                "}"
                "</script>"
            )

        next_job_number = _get_next_job_number()
        print(f"SUCCESS: Job {created_job_number} allocated successfully")
        return HTMLResponse(content=(
            f"<div class='alert alert-success italic font-bold'>"
            f"Job {created_job_number} successfully allocated & Dispatched!"
            f"</div>"
            f"<div class='mt-3 flex flex-wrap gap-2'>"
            f"<a class='btn btn-sm btn-outline btn-success' href='{report_link}' target='_blank' rel='noopener'>Open Blank Report</a>"
            f"{wa_action_html}"
            f"</div>"
            f"<script>"
            f"const jobInput = document.getElementById('job-number-input');"
            f"if (jobInput) jobInput.value = '{next_job_number}';"
            f"const overrideToggle = document.getElementById('job-number-override-toggle');"
            f"if (overrideToggle) overrideToggle.checked = false;"
            f"if (jobInput) jobInput.setAttribute('readonly', 'readonly');"
            f"</script>"
            f"{wa_dispatch}"
        ))
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
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
