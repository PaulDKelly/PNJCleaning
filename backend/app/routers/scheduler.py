from datetime import datetime
import re
import json
import html
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from postgrest.exceptions import APIError

from .. import models
from ..supabase_client import supabase
from ..dependencies import templates, login_required, role_required
from ..utils import generate_whatsapp_link, generate_whatsapp_app_link, get_report_link

router = APIRouter()


def _job_engineers_select():
    return supabase.table("job_engineers").select("*")


def _get_job_engineer_rows(job_numbers: List[str]):
    if not job_numbers:
        return []
    try:
        return _job_engineers_select().in_("job_number", job_numbers).execute().data or []
    except Exception as exc:
        print(f"Warning: job_engineers lookup unavailable; falling back to lead engineer only: {exc}")
        return []


def _attach_engineer_team(jobs: List[models.Job]) -> List[models.Job]:
    rows = _get_job_engineer_rows([job.job_number for job in jobs])
    team_by_job = {}
    role_by_job_engineer = {}
    for row in rows:
        job_number = row.get("job_number")
        engineer_name = row.get("engineer_contact_name")
        if not job_number or not engineer_name:
            continue
        team_by_job.setdefault(job_number, []).append(engineer_name)
        role_by_job_engineer[(job_number, engineer_name)] = row.get("engineer_role") or "Contributing"

    for job in jobs:
        team = team_by_job.get(job.job_number) or []
        if job.engineer_contact_name and job.engineer_contact_name not in team:
            team.insert(0, job.engineer_contact_name)
        team.sort(key=lambda engineer_name: (
            0 if engineer_name == job.engineer_contact_name else
            2 if role_by_job_engineer.get((job.job_number, engineer_name)) == "Supervisor" else
            1
        ))
        job.engineer_team = team
        job.contributing_engineer_names = [
            engineer_name for engineer_name in team
            if role_by_job_engineer.get((job.job_number, engineer_name)) == "Contributing"
        ]
        job.supervisor_name = next(
            (
                engineer_name for engineer_name in team
                if role_by_job_engineer.get((job.job_number, engineer_name)) == "Supervisor"
            ),
            None
        )
        if job.engineer_contact_name:
            job.engineer_role = role_by_job_engineer.get((job.job_number, job.engineer_contact_name), "Lead")
    return jobs


def _get_jobs_for_engineer(engineer_name: str, date: Optional[str] = None) -> List[models.Job]:
    jobs_by_number = {}

    query = supabase.table("jobs").select("*").eq("engineer_contact_name", engineer_name)
    if date:
        query = query.eq("date", date)
    lead_res = query.order("time" if date else "date").execute()
    for row in lead_res.data or []:
        jobs_by_number[row.get("job_number")] = row

    try:
        assignment_res = supabase.table("job_engineers").select("job_number,engineer_role").eq("engineer_contact_name", engineer_name).execute()
        assigned_numbers = [row["job_number"] for row in (assignment_res.data or []) if row.get("job_number")]
        if assigned_numbers:
            assigned_query = supabase.table("jobs").select("*").in_("job_number", assigned_numbers)
            if date:
                assigned_query = assigned_query.eq("date", date)
            assigned_res = assigned_query.order("time" if date else "date").execute()
            for row in assigned_res.data or []:
                jobs_by_number[row.get("job_number")] = row
    except Exception as exc:
        print(f"Warning: job_engineers lookup unavailable for engineer portal: {exc}")

    jobs = [models.Job(**row) for row in jobs_by_number.values() if row]
    jobs.sort(key=lambda job: (job.date, job.time))
    return _attach_engineer_team(jobs)


def _sync_job_engineers(
    job_number: str,
    lead_engineer: str,
    contributing_engineers: List[str],
    supervisor_name: Optional[str] = None
):
    seen = set()
    assignments = []
    assignment_candidates = (
        [(lead_engineer, "Lead")]
        + [(name, "Contributing") for name in contributing_engineers]
        + [(supervisor_name, "Supervisor")]
    )
    for engineer_name, role in assignment_candidates:
        cleaned_name = (engineer_name or "").strip()
        if not cleaned_name or cleaned_name in seen:
            continue
        seen.add(cleaned_name)
        assignments.append({
            "job_number": job_number,
            "engineer_contact_name": cleaned_name,
            "engineer_role": role
        })

    if not assignments:
        return

    try:
        supabase.table("job_engineers").delete().eq("job_number", job_number).execute()
        supabase.table("job_engineers").insert(assignments).execute()
    except Exception as exc:
        print(f"Warning: job_engineers sync unavailable; job remains assigned to lead only: {exc}")


def _get_engineers_by_name(names: List[str]):
    cleaned_names = []
    seen = set()
    for name in names:
        cleaned_name = (name or "").strip()
        if cleaned_name and cleaned_name not in seen:
            seen.add(cleaned_name)
            cleaned_names.append(cleaned_name)
    if not cleaned_names:
        return []
    res = supabase.table("engineers").select("*").in_("contact_name", cleaned_names).execute()
    engineers = [models.Engineer(**row) for row in (res.data or [])]
    by_name = {engineer.contact_name: engineer for engineer in engineers}
    return [by_name[name] for name in cleaned_names if name in by_name]


def _normalise_assignment_names(
    lead_engineer: str,
    contributing_engineers: Optional[List[str]] = None,
    supervisor_name: Optional[str] = None
):
    lead_engineer = (lead_engineer or "").strip()
    supervisor_name = (supervisor_name or "").strip()
    if supervisor_name == lead_engineer:
        supervisor_name = ""

    contributors = []
    seen = {lead_engineer} if lead_engineer else set()
    if supervisor_name:
        seen.add(supervisor_name)

    for name in contributing_engineers or []:
        cleaned_name = (name or "").strip()
        if cleaned_name and cleaned_name not in seen:
            seen.add(cleaned_name)
            contributors.append(cleaned_name)

    assigned_names = [lead_engineer] + contributors + ([supervisor_name] if supervisor_name else [])
    return lead_engineer, contributors, supervisor_name, [name for name in assigned_names if name]


def _get_slot_conflicts(date: str, time: str, engineer_names: List[str], exclude_job_number: Optional[str] = None):
    engineer_names = [name for name in dict.fromkeys([name for name in engineer_names if name])]
    if not date or not time or not engineer_names:
        return []

    jobs_res = (
        supabase.table("jobs")
        .select("*")
        .eq("date", date)
        .eq("time", time)
        .neq("status", "Archived")
        .execute()
    )
    jobs = [models.Job(**row) for row in (jobs_res.data or []) if row.get("job_number") != exclude_job_number]
    jobs = _attach_engineer_team(jobs)

    conflicts = []
    wanted = set(engineer_names)
    for job in jobs:
        assigned = set(job.engineer_team or ([job.engineer_contact_name] if job.engineer_contact_name else []))
        overlapping = sorted(wanted.intersection(assigned))
        if overlapping:
            conflicts.append({
                "job_number": job.job_number,
                "client_name": job.client_name,
                "engineers": overlapping
            })
    return conflicts


def _format_slot_conflict(conflicts):
    items = "".join([
        f"<li>{html.escape(', '.join(conflict['engineers']))} already has {html.escape(conflict['job_number'])} ({html.escape(conflict['client_name'] or 'Unknown client')})</li>"
        for conflict in conflicts
    ])
    return (
        "<div class='alert alert-error text-sm'>"
        "<div>"
        "<div class='font-bold'>Engineer time slot clash</div>"
        f"<ul class='list-disc ml-4'>{items}</ul>"
        "</div>"
        "</div>"
    )


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
    today_jobs = _get_jobs_for_engineer(engineer.contact_name, date=today_str)
    
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
    for job in _get_jobs_for_engineer(engineer.contact_name):
        start_dt = f"{job.date}T{job.time}"
        if job.engineer_contact_name == engineer.contact_name:
            role = "Lead"
        elif job.supervisor_name == engineer.contact_name:
            role = "Supervisor"
        else:
            role = "Contributing"
        events.append({
            "title": f"{job.client_name} ({role})",
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
    jobs = _attach_engineer_team([models.Job(**j) for j in (j_res.data or [])])
    for job in jobs:
        start_dt = f"{job.date}T{job.time}"
        # Color coding: orange for breakdown jobs, blue for regular not completed, green for completed
        if job.job_type == "Breakdown/Callout":
            bg_color = "#f97316"  # orange
        elif job.status != "Completed":
            bg_color = "#3b82f6"  # blue
        else:
            bg_color = "#10b981"  # green
        team = job.engineer_team or ([job.engineer_contact_name] if job.engineer_contact_name else [])
        events.append({
            "id": job.id,
            "title": f"[{', '.join(team) if team else 'Unassigned'}] {job.client_name}",
            "start": start_dt,
            "backgroundColor": bg_color,
            "extendedProps": { "location": job.address, "engineer": ", ".join(team) if team else job.engineer_contact_name }
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
    jobs_res = supabase.table("jobs").select("*").order("date").order("time").execute()
    jobs = _attach_engineer_team([models.Job(**j) for j in (jobs_res.data or [])])
    return templates.TemplateResponse("manager_diary.html", {"request": request, "engineers": engineers, "jobs": jobs, "user": user})


@router.get("/admin/jobs/filter", response_class=HTMLResponse)
def filter_admin_jobs(request: Request, engineer_name: str = "", user: models.User = Depends(login_required)):
    engineers_res = supabase.table("engineers").select("*").order("contact_name").execute()
    engineers = [models.Engineer(**e) for e in (engineers_res.data or [])]
    if engineer_name:
        jobs = _get_jobs_for_engineer(engineer_name)
    else:
        jobs_res = supabase.table("jobs").select("*").order("date").order("time").execute()
        jobs = _attach_engineer_team([models.Job(**j) for j in (jobs_res.data or [])])
    return templates.TemplateResponse("partials/job_rows.html", {"request": request, "jobs": jobs, "engineers": engineers})

@router.get("/engineer-diary", response_class=HTMLResponse)
def engineer_diary(request: Request, user: models.User = Depends(login_required)):
    # Fetch jobs where the user is the assigned engineer (check both username and email for robustness)
    # Using multiple queries because Supabase OR syntax is a bit specific via postgrest
    # But clean way with .or_ or multiple .eq
    query = supabase.table("jobs").select("*")
    
    # Check for engineer_contact_name matching username OR engineer_email matching user email
    jobs_by_number = {}
    res = query.or_(f"engineer_contact_name.eq.{user.username},engineer_email.eq.{user.email}").order("date").order("time").execute()
    for row in res.data or []:
        jobs_by_number[row.get("job_number")] = row
    try:
        assignment_res = supabase.table("job_engineers").select("job_number").eq("engineer_contact_name", user.username).execute()
        assigned_numbers = [row["job_number"] for row in (assignment_res.data or []) if row.get("job_number")]
        if assigned_numbers:
            assigned_res = supabase.table("jobs").select("*").in_("job_number", assigned_numbers).execute()
            for row in assigned_res.data or []:
                jobs_by_number[row.get("job_number")] = row
    except Exception as exc:
        print(f"Warning: job_engineers lookup unavailable for user diary: {exc}")
    jobs = _attach_engineer_team([models.Job(**j) for j in jobs_by_number.values() if j])
    
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
    context = _get_job_allocation_context(request, user)
    return templates.TemplateResponse("job_allocation.html", context)


def _get_job_allocation_context(request: Request, user: models.User, editing_job: Optional[models.Job] = None):
    brands_res = supabase.table("brands").select("*").execute()
    brands = brands_res.data if brands_res.data else []
    
    clients_res = supabase.table("clients").select("*").eq("archived", False).order("client_name").execute()
    clients = clients_res.data if clients_res.data else []
    
    engineers_res = supabase.table("engineers").select("*").order("contact_name").execute()
    engineers = engineers_res.data if engineers_res.data else []
    
    contacts_res = supabase.table("site_contacts").select("*").order("contact_name").execute()
    site_contacts = contacts_res.data if contacts_res.data else []

    try:
        sub_contractors_res = supabase.table("sub_contractors").select("*").eq("archived", False).order("client_name").order("sub_contractor_name").execute()
        sub_contractors = sub_contractors_res.data if sub_contractors_res.data else []
    except Exception:
        sub_contractors = []
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    next_job_number = _get_next_job_number()
    
    return {
        "request": request, 
        "user": user,
        "brands": brands,
        "clients": clients,
        "engineers": engineers,
        "site_contacts": site_contacts,
        "sub_contractors": sub_contractors,
        "today": today_str,
        "next_job_number": next_job_number,
        "editing_job": editing_job
    }


@router.get("/job-allocation/{job_number}/edit", response_class=HTMLResponse)
def edit_job_allocation_page(job_number: str, request: Request, user: models.User = Depends(role_required(["Admin", "Manager"]))):
    job_res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
    if not job_res.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = _attach_engineer_team([models.Job(**job_res.data[0])])[0]
    if job.status in {"Submitted", "Completed", "Archived"}:
        return RedirectResponse(url=f"/admin/reports/job/{job_number}", status_code=303)
    context = _get_job_allocation_context(request, user, editing_job=job)
    return templates.TemplateResponse("job_allocation.html", context)

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
    sub_contractor_id: Optional[int] = Form(None),
    site_id: Optional[int] = Form(None),
    brand_name: Optional[str] = Form(None),
    engineer_name: str = Form(...),
    contributing_engineer_names: Optional[List[str]] = Form(None),
    supervisor_name: Optional[str] = Form(None),
    site_contact_name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    user: models.User = Depends(login_required)
):
    engineer_name, contributing_engineer_names, supervisor_name, allocation_names = _normalise_assignment_names(
        engineer_name,
        contributing_engineer_names,
        supervisor_name
    )
    print(f"JOB ALLOCATION REQUEST: date={date}, time={time}, job_type={job_type}, client={client_name}, engineer={engineer_name}, contributors={contributing_engineer_names}, supervisor={supervisor_name}")
    try:
        requested_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        print(f"Parsed datetime: {requested_dt}")
        if requested_dt < datetime.now():
            print("ERROR: Job in the past")
            return HTMLResponse(content=f"<div class='alert alert-error font-bold'>Error: Cannot allocate a job in the past ({requested_dt.strftime('%d/%m/%Y %H:%M')})</div>")

        conflicts = _get_slot_conflicts(date, time, allocation_names)
        if conflicts:
            return HTMLResponse(content=_format_slot_conflict(conflicts))

        site_name_val = None
        company_val = None
        address_val = None
        proxy_sub_contractor_id_val = None
        proxy_sub_contractor_name_val = None
        
        brand_name_val = (brand_name or "").strip() or None
        if site_id:
            s_res = supabase.table("client_sites").select("*").eq("id", site_id).execute()
            if s_res.data:
                site = s_res.data[0]
                site_name_val = site["site_name"]
                address_val = site.get("address")
                brand_name_val = site.get("brand_name")

        c_res = supabase.table("clients").select("*").eq("client_name", client_name).execute()
        if c_res.data:
            client = c_res.data[0]
            company_val = client.get("company") or client["client_name"]
            if not address_val:
                address_val = client.get("address")

        if sub_contractor_id:
            try:
                sub_res = supabase.table("sub_contractors").select("*").eq("id", sub_contractor_id).eq("archived", False).execute()
                if sub_res.data:
                    subcontractor = sub_res.data[0]
                    proxy_sub_contractor_id_val = subcontractor.get("id")
                    proxy_sub_contractor_name_val = subcontractor.get("sub_contractor_name")
                    company_val = subcontractor.get("company") or subcontractor.get("sub_contractor_name") or company_val
            except Exception:
                print("Warning: sub_contractors lookup unavailable; proceeding without sub-contractor")

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
                "brand": brand_name_val,
                "site_name": site_name_val,
                "company": company_val,
                "address": address_val,
                "proxy_sub_contractor_id": proxy_sub_contractor_id_val,
                "proxy_sub_contractor_name": proxy_sub_contractor_name_val,
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
                        content=f"<div class='alert alert-error'>Error: Job number {requested_job_number} already exists.</div>"
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
                    "brand": brand_name_val,
                    "site_name": site_name_val,
                    "company": company_val,
                    "address": address_val,
                    "proxy_sub_contractor_id": proxy_sub_contractor_id_val,
                    "proxy_sub_contractor_name": proxy_sub_contractor_name_val,
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
        _sync_job_engineers(created_job_number, engineer_name, contributing_engineer_names, supervisor_name)
        assigned_engineer_names = [engineer_name] + contributing_engineer_names
        dispatch_recipient_names = assigned_engineer_names + ([supervisor_name] if supervisor_name else [])
        assigned_engineers = _get_engineers_by_name(dispatch_recipient_names)
        job_obj.engineer_team = dispatch_recipient_names
        job_obj.contributing_engineer_names = contributing_engineer_names
        job_obj.supervisor_name = supervisor_name or None
        report_link = get_report_link(job_obj, request.url.netloc)

        wa_action_html = ""
        wa_links = []
        wa_missing = []
        found_engineer_names = {engineer.contact_name for engineer in assigned_engineers}
        for recipient_name in dispatch_recipient_names:
            if recipient_name not in found_engineer_names:
                wa_missing.append(f"{recipient_name} (not found in engineers)")
        for assigned_engineer in assigned_engineers:
            link = generate_whatsapp_link(job_obj, assigned_engineer, request.url.netloc)
            app_link = generate_whatsapp_app_link(job_obj, assigned_engineer, request.url.netloc)
            if link:
                if assigned_engineer.contact_name == engineer_name:
                    role = "Lead"
                elif supervisor_name and assigned_engineer.contact_name == supervisor_name:
                    role = "Supervisor"
                else:
                    role = "Contributing"
                wa_links.append({
                    "name": assigned_engineer.contact_name,
                    "role": role,
                    "web": link,
                    "app": app_link
                })
            else:
                wa_missing.append(f"{assigned_engineer.contact_name} (missing or invalid phone)")

        if wa_links or wa_missing:
            wa_buttons = []
            for index, link in enumerate(wa_links, start=1):
                name = html.escape(link["name"])
                role = html.escape(link["role"])
                wa_buttons.append(
                    "<a class='btn btn-sm btn-success justify-start' "
                    f"href='{html.escape(link['web'])}' target='_blank' rel='noopener'>"
                    f"{index}. WhatsApp {name} ({role})"
                    "</a>"
                )
            missing_html = ""
            if wa_missing:
                missing_items = "".join([
                    f"<li>{html.escape(item)}</li>"
                    for item in wa_missing
                ])
                missing_html = (
                    "<div class='alert alert-warning mt-3 text-sm'>"
                    "<div>"
                    "<div class='font-bold'>Some WhatsApp drafts could not be created</div>"
                    f"<ul class='list-disc ml-4'>{missing_items}</ul>"
                    "</div>"
                    "</div>"
                )
            wa_action_html = (
                "<div class='divider text-[10px] uppercase tracking-widest text-slate-400 font-black'>Dispatch Messages</div>"
                "<div class='alert alert-info text-sm'>"
                "<div>"
                "<div class='font-bold'>WhatsApp dispatch required</div>"
                "<div>Open each WhatsApp draft below and press send for every assigned person.</div>"
                "</div>"
                "</div>"
                "<div class='mt-3 grid grid-cols-1 md:grid-cols-2 gap-2'>"
                + "".join(wa_buttons) +
                "</div>"
                f"{missing_html}"
            )

        next_job_number = _get_next_job_number()
        print(f"SUCCESS: Job {created_job_number} allocated successfully")
        team_label = ", ".join(assigned_engineer_names)
        supervisor_label = f" Supervisor: {supervisor_name}." if supervisor_name else ""
        return HTMLResponse(content=(
            f"<div class='alert alert-success italic font-bold'>"
            f"Job {created_job_number} successfully allocated to {team_label}!{supervisor_label}"
            f"</div>"
            f"<div class='mt-3 flex flex-wrap gap-2'>"
            f"<a class='btn btn-sm btn-outline btn-success' href='{report_link}' target='_blank' rel='noopener'>Open Blank Report</a>"
            f"</div>"
            f"{wa_action_html}"
            f"<script>"
            f"const jobInput = document.getElementById('job-number-input');"
            f"if (jobInput) jobInput.value = '{next_job_number}';"
            f"const overrideToggle = document.getElementById('job-number-override-toggle');"
            f"if (overrideToggle) overrideToggle.checked = false;"
            f"if (jobInput) jobInput.setAttribute('readonly', 'readonly');"
            f"</script>"
        ))
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return HTMLResponse(content=f"<div class='alert alert-error'>Error: {str(e)}</div>")


@router.post("/admin/jobs/{job_number}/edit", response_class=HTMLResponse)
async def edit_job(job_number: str, request: Request, user: models.User = Depends(role_required(["Admin", "Manager"]))):
    form_data = await request.form()
    job_res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
    if not job_res.data:
        return HTMLResponse("<div class='alert alert-error text-sm'>Job not found.</div>")

    existing_job = models.Job(**job_res.data[0])
    if existing_job.status in {"Submitted", "Completed", "Archived"}:
        return HTMLResponse("<div class='alert alert-error text-sm'>Submitted, completed, or archived jobs cannot be edited here.</div>")

    date = form_data.get("date")
    time = form_data.get("time")
    priority = form_data.get("priority") or existing_job.priority
    engineer_name = form_data.get("engineer_name") or existing_job.engineer_contact_name
    contributing_engineer_names = form_data.getlist("contributing_engineer_names")
    supervisor_name = form_data.get("supervisor_name")
    notes = form_data.get("notes")

    engineer_name, contributing_engineer_names, supervisor_name, allocation_names = _normalise_assignment_names(
        engineer_name,
        contributing_engineer_names,
        supervisor_name
    )

    conflicts = _get_slot_conflicts(date, time, allocation_names, exclude_job_number=job_number)
    if conflicts:
        return HTMLResponse(content=_format_slot_conflict(conflicts))

    supabase.table("jobs").update({
        "date": date,
        "time": time,
        "priority": priority,
        "engineer_contact_name": engineer_name,
        "notes": notes
    }).eq("job_number", job_number).execute()
    _sync_job_engineers(job_number, engineer_name, contributing_engineer_names, supervisor_name)

    return HTMLResponse(
        "<div class='alert alert-success text-sm font-bold'>Job updated.</div>"
        "<script>"
        "setTimeout(() => {"
        "  if (document.getElementById('job-rows')) {"
        "    htmx.ajax('GET', '/admin/jobs/filter', { target: '#job-rows' });"
        "    const dialog = document.currentScript?.closest('dialog');"
        "    if (dialog) dialog.close();"
        "  }"
        "}, 500);"
        "</script>"
    )


@router.post("/admin/jobs/{job_number}/archive")
def archive_job(job_number: str, user: models.User = Depends(role_required(["Admin", "Manager"]))):
    supabase.table("jobs").update({"status": "Archived"}).eq("job_number", job_number).execute()
    return HTMLResponse(content="")


@router.delete("/admin/jobs/{job_number}", response_class=HTMLResponse)
def delete_job(job_number: str, user: models.User = Depends(role_required(["Admin"]))):
    job_res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
    if not job_res.data:
        return HTMLResponse("<div class='alert alert-error text-sm'>Job not found.</div>")

    job = models.Job(**job_res.data[0])
    if job.status in {"Submitted", "Completed", "Archived"}:
        return HTMLResponse("<div class='alert alert-error text-sm'>Submitted, completed, or archived jobs cannot be deleted. Archive them instead.</div>")

    reports_res = supabase.table("extraction_reports").select("id").eq("job_number", job_number).limit(1).execute()
    if reports_res.data:
        return HTMLResponse("<div class='alert alert-error text-sm'>This job already has report evidence and cannot be deleted. Archive it instead.</div>")

    try:
        supabase.table("job_engineers").delete().eq("job_number", job_number).execute()
    except Exception as exc:
        print(f"Warning: job_engineers cleanup failed during job delete: {exc}")
    try:
        supabase.table("job_contributions").delete().eq("job_number", job_number).execute()
    except Exception as exc:
        print(f"Warning: job_contributions cleanup failed during job delete: {exc}")

    supabase.table("jobs").delete().eq("job_number", job_number).execute()
    return HTMLResponse(content="")

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
