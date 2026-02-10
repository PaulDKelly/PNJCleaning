from datetime import datetime
from typing import Optional
import os
import json
import uuid
from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import models, security
from jose import jwt
import urllib.parse
from .supabase_client import supabase
import os
import json
import workos
from workos import client as workos_client


app = FastAPI(title="PNJ Extraction Services")
print("PNJ_BACKEND_VERSION: v8-force-flush", flush=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Helper to get user by email using Supabase
def get_user_by_email(email: str):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data:
        return models.User(**res.data[0])
    return None

def get_user_by_username(username: str):
    res = supabase.table("users").select("*").eq("username", username).execute()
    if res.data:
        return models.User(**res.data[0])
    return None

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return get_user_by_email(email)
    except Exception:
        return None

def login_required(user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def role_required(allowed_roles: list):
    def dependency(user: models.User = Depends(login_required)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return dependency

# Dashboard Route
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, user: models.User = Depends(login_required)):
    try:
        # 1. Summary stats
        total_jobs = supabase.table("jobs").select("*", count="exact", head=True).execute().count
        active_engineers = supabase.table("engineers").select("*", count="exact", head=True).execute().count
        total_clients = supabase.table("clients").select("*", count="exact", head=True).execute().count
        
        # 2. Recent jobs (Increased limit to 20 for the new unified view)
        recent_jobs_res = supabase.table("jobs").select("*").order("date", desc=True).limit(20).execute()
        recent_jobs = [models.Job(**j) for j in recent_jobs_res.data]
        
        # 3. All Recent Jobs for "Operation History" (Full history but limited for performance)
        all_jobs_res = supabase.table("jobs").select("*").order("date", desc=True).limit(10).execute()
        all_jobs = [models.Job(**j) for j in all_jobs_res.data]
        
        # 4. Archived Clients
        archived_clients_res = supabase.table("clients").select("*").eq("archived", True).execute()
        archived_clients = [models.Client(**c) for c in archived_clients_res.data]
        
        # 5. Archived Sites
        archived_sites_res = supabase.table("client_sites").select("*").eq("archived", True).execute()
        archived_sites = [models.ClientSite(**s) for s in archived_sites_res.data]
        
        # 6. Engineers (for Leave Booking Modal)
        engineers_res = supabase.table("engineers").select("*").execute()
        engineers = [models.Engineer(**e) for e in engineers_res.data]
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "total_jobs": total_jobs,
            "active_engineers": active_engineers,
            "total_clients": total_clients,
            "recent_jobs": recent_jobs,
            "all_jobs": all_jobs,
            "archived_clients": archived_clients,
            "archived_sites": archived_sites,
            "engineers": engineers,
            "user": user
        })
    except Exception as e:
        import traceback
        print("ERROR IN ROOT ROUTE:")
        traceback.print_exc()
        raise e

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: models.User = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("login.html", {"request": request, "user": user})

# --- WorkOS SSO Integration ---

# Initialize WorkOS
workos_api_key = os.getenv("WORKOS_API_KEY")
workos_client_id = os.getenv("WORKOS_CLIENT_ID")
workos_redirect_uri = os.getenv("WORKOS_REDIRECT_URI")

print(f"DEBUG: WORKOS_CLIENT_ID exists: {bool(workos_client_id)} (Length: {len(workos_client_id) if workos_client_id else 0})")
print(f"DEBUG: WORKOS_API_KEY exists: {bool(workos_api_key)} (Length: {len(workos_api_key) if workos_api_key else 0})")
if workos_api_key:
    print(f"DEBUG: WORKOS_API_KEY prefix: {workos_api_key[:10]}...")

from workos import WorkOSClient
wos = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)

@app.post("/auth/workos")
async def auth_workos(email: str = Form(...)):
    """Initiate WorkOS SSO flow with robust connection lookup"""
    try:
        # 1. Get the domain from the email
        domain = email.split('@')[-1]
        print(f"DEBUG: Initiating SSO for domain: {domain}")
        
        # 2. Find the connection for this domain
        connections = wos.sso.list_connections(domain=domain)
        if not connections.data:
            print(f"ERROR: No WorkOS connection found for domain: {domain}")
            return RedirectResponse(url=f"/login?error=unknown_domain&domain={domain}", status_code=303)
        
        connection_id = connections.data[0].id
        print(f"DEBUG: Found connection {connection_id} for domain {domain}")
        
        # 3. Get the authorization URL
        authorization_url = wos.sso.get_authorization_url(
            connection=connection_id,
            redirect_uri=workos_redirect_uri,
            state={},
        )
        return RedirectResponse(url=authorization_url, status_code=303)
    except Exception as e:
        import traceback
        print(f"WorkOS Auth Error: {e}")
        traceback.print_exc()
        return RedirectResponse(url="/login?error=sso_failed", status_code=303)

@app.post("/auth/google")
async def auth_google():
    """Initiate Google Social Login flow via WorkOS"""
    try:
        # Use 'GoogleOAuth' provider for personal Gmail accounts
        authorization_url = wos.sso.get_authorization_url(
            provider='GoogleOAuth',
            redirect_uri=workos_redirect_uri,
            state={},
        )
        return RedirectResponse(url=authorization_url, status_code=303)
    except Exception as e:
        import traceback
        print(f"WorkOS Google Auth Error: {e}")
        traceback.print_exc()
        return RedirectResponse(url="/login?error=sso_failed", status_code=303)

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str):
    """Handle WorkOS callback and auto-provision users"""
    try:
        # 1. Exchange the code for a profile
        # Version 4.x returns a ProfileAndToken object (Pydantic-based)
        profile_and_token = wos.sso.get_profile_and_token(code)
        profile = profile_and_token.profile
        
        email = profile.email
        if not email:
            print("ERROR: WorkOS SSO: No email returned in profile")
            return RedirectResponse(url="/login?error=no_email")
            
        # 2. Check if user exists
        user = get_user_by_email(email)
        
        if not user:
            # AUTO-PROVISION
            print(f"Auto-provisioning user: {email}")
            first_name = profile.first_name or ""
            last_name = profile.last_name or ""
            username = f"{first_name} {last_name}".strip()
            if not username:
                username = email.split('@')[0]
                
            # Create user with random password (they use SSO)
            random_pw = str(uuid.uuid4())
            hashed_pw = security.get_password_hash(random_pw)
            
            supabase.table("users").insert({
                "username": username,
                "email": email,
                "password": hashed_pw,
                "role": "Admin" # Default role for new SSO users
            }).execute()
            
            user = get_user_by_email(email)
            
        if not user:
            print(f"ERROR: Provisioning failed for {email}")
            return RedirectResponse(url="/login?error=provisioning_failed")

        # 3. Log user in
        access_token = security.create_access_token(data={"sub": user.email})
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response
        
    except Exception as e:
        print(f"WorkOS Callback Error: {e}")
        return RedirectResponse(url="/login?error=callback_failed")

# --- End WorkOS SSO ---

@app.get("/portal/{token}", response_class=HTMLResponse)
def engineer_portal(token: str, request: Request):
    # 1. Validate Token
    try:
        # Check UUID format first to avoid DB error spam
        uuid.UUID(token)
        res = supabase.table("engineers").select("*").eq("access_token", token).execute()
        if not res.data:
            raise HTTPException(status_code=403, detail="Invalid Access Token")
        engineer = models.Engineer(**res.data[0])
    except ValueError:
         raise HTTPException(status_code=403, detail="Invalid Token Format")

    # 2. Fetch Jobs for "Today" Queue (Legacy view)
    today_str = datetime.now().strftime('%Y-%m-%d')
    j_res = supabase.table("jobs").select("*").eq("engineer_contact_name", engineer.contact_name).eq("date", today_str).order("time").execute()
    today_jobs = [models.Job(**j) for j in j_res.data]
    
    # 3. Add WA Links
    for job in today_jobs:
        job.wa_link = generate_whatsapp_link(job, engineer, request.url.netloc)

    return templates.TemplateResponse("engineer_dashboard.html", {
        "request": request,
        "engineer": engineer,
        "token": token,
        "today_jobs": today_jobs
    })

@app.get("/api/engineer/{token}/events")
def get_engineer_events(token: str):
    # 1. Validate
    res = supabase.table("engineers").select("*").eq("access_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Invalid Token")
    engineer = models.Engineer(**res.data[0])
    
    events = []
    
    # 2. Fetch Jobs (Blue)
    # Optimization: Filter by range if passed by FullCalendar start/end params? 
    # For now, fetch all active/recent jobs to keep it simple.
    j_res = supabase.table("jobs").select("*").eq("engineer_contact_name", engineer.contact_name).execute()
    for j in j_res.data:
        job = models.Job(**j)
        # Use ISO string for FullCalendar
        start_dt = f"{job.date}T{job.time}"
        events.append({
            "title": f"{job.client_name} ({job.priority})",
            "start": start_dt,
            "backgroundColor": "#3b82f6", # Blue
            "borderColor": "#2563eb",
            "extendedProps": {
                "location": job.address or job.site_name,
                "status": job.status
            }
        })
        
    # 3. Fetch Leave (Red/Green)
    l_res = supabase.table("leave_requests").select("*").eq("engineer_name", engineer.contact_name).execute()
    for l in l_res.data:
        # FullCalendar expects exclusive end date if allDay=true? 
        # Actually standard date is inclusive for allDay usually implies +1 day for strict rendering, 
        # but let's send standard dates and see.
        color = "#ef4444" # Red (Pending)
        if l['status'] == 'Approved':
            color = "#22c55e" # Green
        elif l['status'] == 'Rejected':
            color = "#94a3b8" # Gray
            
        events.append({
            "title": f"Leave: {l['reason']}",
            "start": l['start_date'],
            "end": l['end_date'], # Note: FullCalendar treats end date as exclusive for all-day events usually
            "color": color,
            "allDay": True
        })
        
    return JSONResponse(content=events)

@app.post("/api/engineer/{token}/leave")
async def submit_leave_request(token: str, request: Request):
    # 1. Validate
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
            <div class='alert alert-success'>
                <span>Request submitted successfully!</span>
            </div>
            <script>
                if(window.calendar) window.calendar.refetchEvents();
                setTimeout(() => {
                    document.getElementById('leave_modal').close();
                    document.getElementById('leave-feedback').innerHTML = ''; // Clear feedback
                }, 1500);
            </script>
        """)
    except Exception as e:
        return HTMLResponse(f"<div class='alert alert-error'>Error: {str(e)}</div>")

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: Optional[str] = Form(None)
):
    print(f"Login attempt for email: {email}")
    if not password:
        return HTMLResponse(content="<div class='alert alert-error'>Password is required</div>", status_code=200)
    user = get_user_by_email(email)
    
    if not user:
        print(f"User with email {email} not found")
        return HTMLResponse(content="<div class='alert alert-error'>User not found</div>", status_code=200)
        
    if not security.verify_password(password, user.password):
        print(f"Password mismatch for user {email}")
        return HTMLResponse(content="<div class='alert alert-error'>Invalid password</div>", status_code=200)
    
    print(f"Login success for {email}")
    access_token = security.create_access_token(data={"sub": user.email})
    response = HTMLResponse(content="", status_code=200, headers={"HX-Redirect": "/"})
    # Secure cookies
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password")
async def handle_forgot_password(request: Request, email: str = Form(...)):
    user = get_user_by_email(email)
    if not user:
        # Don't reveal if user exists or not for security, but for helper bot let's just say success
        return templates.TemplateResponse("forgot_password.html", {
            "request": request, 
            "message": "If an account exists with that email, a reset link has been generated."
        })
    
    # Generate token
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=1)
    
    supabase.table("users").update({
        "reset_token": token,
        "reset_expires": expires.isoformat()
    }).eq("email", email).execute()
    
    # LOG TO CONSOLE (as requested)
    reset_link = f"{request.url.scheme}://{request.url.netloc}/reset-password/{token}"
    print("\n" + "="*50)
    print(f"PASSWORD RESET REQUEST FOR: {email}")
    print(f"LINK: {reset_link}")
    print("="*50 + "\n")
    
    return templates.TemplateResponse("forgot_password.html", {
        "request": request, 
        "message": "A reset link has been generated and logged to the server console."
    })

@app.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    # Verify token
    res = supabase.table("users").select("*").eq("reset_token", token).execute()
    if not res.data:
        return templates.TemplateResponse("placeholder.html", {
            "request": request, "title": "Invalid Token", "message": "The reset link is invalid or has expired."
        })
    
    user_data = res.data[0]
    expires = datetime.fromisoformat(user_data['reset_expires'])
    if datetime.utcnow() > expires:
        return templates.TemplateResponse("placeholder.html", {
            "request": request, "title": "Expired Token", "message": "The reset link has expired."
        })
        
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.post("/reset-password/{token}")
async def handle_reset_password(request: Request, token: str, password: str = Form(...)):
    # Verify token again
    res = supabase.table("users").select("*").eq("reset_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user_data = res.data[0]
    expires = datetime.fromisoformat(user_data['reset_expires'])
    if datetime.utcnow() > expires:
        raise HTTPException(status_code=400, detail="Expired token")
    
    # Update password
    hashed_password = security.get_password_hash(password)
    supabase.table("users").update({
        "password": hashed_password,
        "reset_token": None,
        "reset_expires": None
    }).eq("id", user_data['id']).execute()
    
    return RedirectResponse(url="/login?message=password_updated", status_code=303)

# Add missing import for timedelta
from datetime import timedelta

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


@app.get("/api/admin/events")

def get_admin_events(user: models.User = Depends(login_required)):
    events = []
    
    # 1. Fetch All Jobs
    j_res = supabase.table("jobs").select("*").execute()
    for j in j_res.data:
        job = models.Job(**j)
        # Convert date and time to ISO string format
        start_dt = f"{job.date.isoformat()}T{job.time.strftime('%H:%M:%S')}"
        events.append({
            "title": f"JOB: {job.job_number} ({job.engineer_contact_name})",
            "start": start_dt,
            "backgroundColor": "#3b82f6",
            "extendedProps": {
                "type": "job",
                "engineer": job.engineer_contact_name
            }
        })
        
    # 2. Fetch All Leaves
    l_res = supabase.table("leave_requests").select("*").execute()
    for l in l_res.data:
        leave = models.LeaveRequest(**l)
        color = "#ef4444" # Red
        if leave.status == 'Approved':
            color = "#22c55e" # Green
        elif leave.status == 'Rejected':
            color = "#94a3b8" # Gray
            
        events.append({
            "title": f"{leave.engineer_name}: {leave.reason}",
            "start": str(leave.start_date),
            "end": str(leave.end_date),
            "color": color,
            "allDay": True,
            "extendedProps": {
                "type": "leave",
                "status": leave.status
            }
        })
        
    return JSONResponse(content=events)

@app.get("/admin/partials/leaves", response_class=HTMLResponse)
def get_pending_leaves(request: Request, user: models.User = Depends(login_required)):
    res = supabase.table("leave_requests").select("*").eq("status", "Pending").order("created_at").execute()
    leaves = [models.LeaveRequest(**l) for l in res.data]
    
    html = ""
    if not leaves:
        html = "<div class='text-center py-10 text-slate-400 italic'>No pending requests.</div>"
    else:
        for l in leaves:
            html += f"""
            <div class="card bg-base-100 shadow-sm border border-slate-200 mb-4" id="leave-{l.id}">
                <div class="card-body p-4 flex flex-row justify-between items-center">
                    <div>
                        <div class="font-bold text-lg">{l.engineer_name}</div>
                        <div class="text-sm text-slate-500">{l.reason}</div>
                        <div class="badge badge-warning mt-2">{l.start_date} to {l.end_date}</div>
                    </div>
                    <div class="join">
                        <button hx-post="/admin/leave/{l.id}/approve" hx-target="#leave-{l.id}" hx-swap="outerHTML" class="btn btn-success btn-sm join-item text-white">Approve</button>
                        <button hx-post="/admin/leave/{l.id}/reject" hx-target="#leave-{l.id}" hx-swap="outerHTML" class="btn btn-error btn-sm join-item text-white">Reject</button>
                    </div>
                </div>
            </div>
            """
    return HTMLResponse(html)

@app.post("/admin/leave/{id}/{action}")
def update_leave_status(id: int, action: str, user: models.User = Depends(login_required)):
    if action not in ['approve', 'reject']:
        return HTMLResponse("Invalid Action", status_code=400)
    
    new_status = "Approved" if action == "approve" else "Rejected"
    supabase.table("leave_requests").update({"status": new_status}).eq("id", id).execute()
    
    # Return nothing (or success message) to remove the card from the list
    return HTMLResponse(f"<div class='alert alert-info text-xs'>Request {new_status}</div>")

@app.post("/admin/leave/book", response_class=HTMLResponse)
async def book_leave_for_staff(request: Request, user: models.User = Depends(login_required)):
    form_data = await request.form()
    
    leave_data = {
        "engineer_name": form_data.get("engineer_name"),
        "start_date": form_data.get("start_date"),
        "end_date": form_data.get("end_date"),
        "reason": form_data.get("reason"),
        "status": "Approved"  # Auto-approve manager-initiated leave
    }
    
    try:
        supabase.table("leave_requests").insert(leave_data).execute()
        return HTMLResponse("""
            <div class='alert alert-success'>
                <span>Leave booked successfully!</span>
            </div>
            <script>
                setTimeout(() => {
                    document.getElementById('manager_leave_modal').close();
                    document.getElementById('manager-leave-feedback').innerHTML = '';
                    if(document.getElementById('leave-approval-list')) {
                        htmx.trigger('#leave-approval-list', 'load');
                    }
                }, 1500);
            </script>
        """)
    except Exception as e:
        return HTMLResponse(f"<div class='alert alert-error'>Error: {str(e)}</div>")

@app.get("/manager-diary", response_class=HTMLResponse)
def management_dashboard(request: Request, user: models.User = Depends(login_required)):
    # Fetch all jobs - Date Ascending for Queue
    res = supabase.table("jobs").select("*").order("date", desc=False).execute()
    jobs = [models.Job(**j) for j in res.data]
    
    # Fetch engineers for WA link generation & filter partial
    eng_res = supabase.table("engineers").select("*").execute()
    engineers_dict = {e['contact_name']: models.Engineer(**e) for e in eng_res.data}
    engineer_list = [models.Engineer(**e) for e in eng_res.data]
    
    for job in jobs:
        eng = engineers_dict.get(job.engineer_contact_name)
        if eng:
            job.wa_link = generate_whatsapp_link(job, eng, request.url.netloc)
    
    return templates.TemplateResponse("manager_diary.html", {
        "request": request,
        "title": "Management Diary",
        "user": user,
        "jobs": jobs,
        "engineers": engineer_list
    })

@app.get("/admin/jobs/filter", response_class=HTMLResponse)
def filter_jobs_table(
    request: Request, 
    engineer_name: Optional[str] = None,
    user: models.User = Depends(login_required)
):
    query = supabase.table("jobs").select("*")
    
    if engineer_name:
        query = query.eq("engineer_contact_name", engineer_name)
        
    res = query.order("date", desc=False).execute()
    jobs = [models.Job(**j) for j in res.data]
    
    eng_res = supabase.table("engineers").select("*").execute()
    engineers = {e['contact_name']: models.Engineer(**e) for e in eng_res.data}
    
    for job in jobs:
        eng = engineers.get(job.engineer_contact_name)
        if eng:
            job.wa_link = generate_whatsapp_link(job, eng, request.url.netloc)
            
    return templates.TemplateResponse("partials/job_rows.html", {
        "request": request,
        "jobs": jobs
    })

@app.get("/engineer/diary", response_class=HTMLResponse)
def engineer_diary(request: Request, user: models.User = Depends(login_required)):
    # Filter by engineer name
    res = supabase.table("jobs").select("*").eq("engineer_contact_name", user.username).order("date", desc=True).execute()
    jobs = [models.Job(**j) for j in res.data]
    
    return templates.TemplateResponse("engineer_diary.html", {
        "request": request, 
        "title": "My Jobs Queue", 
        "user": user,
        "jobs": jobs
    })

@app.get("/job-allocation", response_class=HTMLResponse)
def job_allocation(request: Request, user: models.User = Depends(login_required)):
    # Fetch lists
    clients = [models.Client(**c) for c in supabase.table("clients").select("*").order("client_name").execute().data]
    engineers = [models.Engineer(**e) for e in supabase.table("engineers").select("*").order("contact_name").execute().data]
    site_contacts = [models.SiteContact(**s) for s in supabase.table("site_contacts").select("*").order("contact_name").execute().data]
    brands = [models.Brand(**b) for b in supabase.table("brands").select("*").order("brand_name").execute().data]
    
    return templates.TemplateResponse("job_allocation.html", {
        "request": request, 
        "title": "Job Allocation", 
        "user": user,
        "clients": clients,
        "engineers": engineers,
        "site_contacts": site_contacts,
        "brands": brands,
        "today": datetime.now().date().isoformat()
    })

def generate_whatsapp_link(job: models.Job, engineer: models.Engineer, host: str):
    if not engineer or not engineer.phone:
        return None
    
    # Determine base URL (Cloud env var or local request host)
    base_url = os.getenv("PUBLIC_URL")
    if not base_url:
        # If no PUBLIC_URL, we guess based on host. 
        # If it's a domain with a dot, assume HTTPS (cloud), else HTTP (local)
        protocol = "https" if "." in host and not host.startswith("localhost") and not host.startswith("127.0.0.1") else "http"
        base_url = f"{protocol}://{host}"
    
    # Remove trailing slash if present for consistency
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # Persistent Portal Link (Magic Link)
    portal_link = f"{base_url}/portal/{engineer.access_token}" if engineer.access_token else f"{base_url}/portal/login"
    report_link = f"{base_url}/extraction-report?job_number={job.job_number}"
    map_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(job.address)}" if job.address else "N/A"
    
    msg = f"""*PNJ Job Allocation: {job.job_number}*
*Client:* {job.client_name}
*Site:* {job.site_name or 'N/A'}
*Address:* {job.address or 'N/A'}
*Map:* {map_link}
*Date/Time:* {job.date.strftime('%d/%m/%Y')} @ {job.time.strftime('%H:%M')}
*Priority:* {job.priority}

*Instructions:*
{job.notes or 'Standard extraction clean.'}

*Report:*
{report_link}

*Engineer Dashboard:*
{portal_link}"""
    
    encoded_msg = urllib.parse.quote(msg)
    phone = "".join(filter(str.isdigit, engineer.phone))
    if not phone.startswith('44'):
        if phone.startswith('0'):
            phone = '44' + phone[1:]
        else:
            phone = '44' + phone
            
    return f"https://wa.me/{phone}?text={encoded_msg}"

@app.post("/extraction-report/start")
async def start_extraction_report(request: Request, user: models.User = Depends(login_required)):
    form_data = await request.form()
    job_number = form_data.get("job_number")
    if not job_number:
        raise HTTPException(status_code=400, detail="Job number is required")
    
    # Redirect to the report form with the job number pre-filled
    return RedirectResponse(url=f"/extraction-report?job_number={job_number}", status_code=303)

@app.get("/admin/sites-lookup", response_class=HTMLResponse)
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

@app.get("/admin/clients-lookup", response_class=HTMLResponse)
def get_clients_lookup(
    brand_name: Optional[str] = None,
    user: models.User = Depends(login_required)
):
    # If brand_name filtered, we need to find clients that have sites with that brand
    # Supabase join syntax: select("*, client_sites!inner(*)")
    # But simplifies: Get sites with brand, extract client_names, then get clients.
    if brand_name:
        sites = supabase.table("client_sites").select("client_name").eq("brand_name", brand_name).execute().data
        client_names = list(set([s['client_name'] for s in sites]))
        if not client_names:
            return HTMLResponse(content='<option value="">All Clients (None found)</option>')
        # In syntax for multiple values
        res = supabase.table("clients").select("*").in_("client_name", client_names).order("client_name").execute()
    else:
        res = supabase.table("clients").select("*").order("client_name").execute()
    
    clients = [models.Client(**c) for c in res.data]
    options = "".join([f'<option value="{c.client_name}">{c.client_name}</option>' for c in clients])
    return HTMLResponse(content=f'<option value="">All Clients</option>{options}')

@app.get("/admin/manage/clients-table", response_class=HTMLResponse)
def get_clients_table(
    request: Request,
    client_name: Optional[str] = None,
    brand_name: Optional[str] = None,
    site_id: Optional[str] = None,
    user: models.User = Depends(login_required)
):
    # Build query
    # Supabase doesn't easily do deep filtering on unrelated joins in one go efficiently without defined FKs in PostgREST
    # Simulating the previous logic:
    
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
    
    # We need all sites to calculate counts in the template if logic exists there? 
    # Or simplified. Assume template iterates client sites.
    # We'll just pass all sites for now to be safe with existing template logic
    all_sites = supabase.table("client_sites").select("*").execute().data
    # Map sites to objects? Template might expect objects.
    sites_objs = [models.ClientSite(**s) for s in all_sites]

    return templates.TemplateResponse("partials/clients_table_rows.html", {
        "request": request,
        "clients": clients,
        "sites": sites_objs
    })

@app.get("/admin/manage/sites-table", response_class=HTMLResponse)
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

@app.post("/admin/manage/clients/{client_name}/archive")
def archive_client(client_name: str, user: models.User = Depends(login_required)):
    supabase.table("clients").update({"archived": True}).eq("client_name", client_name).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshClients"})

@app.post("/admin/manage/clients/{client_name}/restore")
def restore_client(client_name: str, user: models.User = Depends(login_required)):
    supabase.table("clients").update({"archived": False}).eq("client_name", client_name).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshClients"})

@app.post("/admin/manage/sites/{site_id}/archive")
def archive_site(site_id: int, user: models.User = Depends(login_required)):
    supabase.table("client_sites").update({"archived": True}).eq("id", site_id).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshSites"})

@app.post("/admin/manage/sites/{site_id}/restore")
def restore_site(site_id: int, user: models.User = Depends(login_required)):
    supabase.table("client_sites").update({"archived": False}).eq("id", site_id).execute()
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshSites"})

@app.post("/admin/manage/sites/bulk-archive")
async def bulk_archive_sites(request: Request, user: models.User = Depends(login_required)):
    form = await request.form()
    site_ids = form.getlist("site_ids")
    
    if site_ids:
        # Convert to ints
        ids = [int(i) for i in site_ids]
        supabase.table("client_sites").update({"archived": True}).in_("id", ids).execute()
        
    return HTMLResponse(content="", headers={"HX-Trigger": "refreshSites"})

@app.post("/job-allocation")
def allocate_job(
    request: Request,
    job_number: str = Form(...),
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
        # 0. Validate Date/Time not in past
        requested_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        if requested_dt < datetime.now():
            return HTMLResponse(content=f"<div class='alert alert-error font-bold'>Error: Cannot allocate a job in the past ({requested_dt.strftime('%d/%m/%Y %H:%M')})</div>", status_code=400)

        # Site logic
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
            # Fallback
            c_res = supabase.table("clients").select("*").eq("client_name", client_name).execute()
            if c_res.data:
                client = c_res.data[0]
                company_val = client.get('company') or client['client_name']
                address_val = client.get('address')
        
        # Prepare job data
        job_data = {
            "job_number": job_number,
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
        
        # UPSERT based on job_number
        # Supabase upsert requires unique constraint. job_number is unique.
        supabase.table("jobs").upsert(job_data, on_conflict="job_number").execute()
        
        # WhatsApp logic
        # Get Job back (with ID etc if needed) or just construct object
        res_job = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
        job_obj = models.Job(**res_job.data[0])
        
        res_eng = supabase.table("engineers").select("*").eq("contact_name", engineer_name).execute()
        eng_obj = models.Engineer(**res_eng.data[0]) if res_eng.data else None
        
        wa_link = generate_whatsapp_link(job_obj, eng_obj, request.url.netloc)
        
        wa_btn = ""
        if wa_link:
            wa_btn = f"<script>window.open('{wa_link}', '_blank');</script>"
        
        return HTMLResponse(content=f"<div class='alert alert-success italic font-bold'>Job successfully allocated & Dispatched!</div>{wa_btn}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"<div class='alert alert-error'>Error: {str(e)}</div>", status_code=400)

@app.post("/admin/jobs/{job_number}/archive")
def archive_job(job_number: str, user: models.User = Depends(login_required)):
    supabase.table("jobs").update({"status": "Archived"}).eq("job_number", job_number).execute()
    return HTMLResponse(content="<span class='badge badge-ghost font-bold italic'>Archived</span>")

@app.get("/admin/jobs/archive/search", response_class=HTMLResponse)
def search_archive(q: str = "", user: models.User = Depends(login_required)):
    query = supabase.table("jobs").select("*").eq("status", "Archived")
    
    if q:
        # Supabase 'or' syntax: .or_(f"job_number.ilike.%{q}%,client_name.ilike.%{q}%")
        # Note: syntax is "column.operator.value"
        filter_str = f"job_number.ilike.%{q}%,client_name.ilike.%{q}%,site_name.ilike.%{q}%"
        query = query.or_(filter_str)
    
    res = query.order("date", desc=True).execute()
    jobs = [models.Job(**j) for j in res.data]
    
    html_rows = ""
    for job in jobs:
        html_rows += f"""
        <tr class="opacity-75 hover:opacity-100 transition-opacity">
            <td class="p-4 font-medium text-slate-500">{job.date.strftime('%d %b %Y')}</td>
            <td><span class="badge badge-ghost font-mono text-[10px]">{job.job_number}</span></td>
            <td>
                <div class="font-bold text-slate-600">{job.client_name}</div>
                <div class="text-[9px] uppercase tracking-tighter text-slate-400">{job.site_name or 'N/A'}</div>
            </td>
            <td><span class="badge badge-outline badge-xs font-bold">{job.status}</span></td>
            <td class="text-right">
                <a href="/admin/reports" class="btn btn-ghost btn-xs text-indigo-500 font-bold underline">View Audit</a>
            </td>
        </tr>
        """
    if not jobs:
        html_rows = "<tr><td colspan='5' class='text-center py-20 text-slate-400 italic'>No matches found in archive.</td></tr>"
        
    return HTMLResponse(content=html_rows)

@app.get("/extraction-report", response_class=HTMLResponse)
def extraction_report(request: Request, job_number: Optional[str] = None, user: models.User = Depends(login_required)):
    job_info = {
        "job_number": job_number or "",
        "company": "",
        "date": None,
        "time": None,
        "brand": "",
        "address": "",
        "contact_name": "",
        "contact_phone": "-"
    }
    
    if job_number:
        # Check Job table
        res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
        if res.data:
            job = res.data[0]
            # Parse date/time strings from JSON to Python objects? Pydantic does this if we used models.
            # But here we are passing dict to template. Template expects objects mostly or strings.
            # Supabase returns strings for dates. Jinja might need help or Python datetime objects.
            # Let's convert to proper python objects via Pydantic model
            j_obj = models.Job(**job)
            
            job_info.update({
                "company": j_obj.company or j_obj.client_name,
                "date": j_obj.date,
                "time": j_obj.time,
                "brand": j_obj.brand or "",
                "address": j_obj.address or "",
                "contact_name": j_obj.site_contact_name or "",
                "contact_phone": j_obj.site_contact_phone or "-"
            })
    
    return templates.TemplateResponse("extraction_report.html", {
        "request": request, 
        "title": "Extraction Report", 
        "user": user,
        "job": job_info
    })

@app.post("/extraction-report")
async def submit_extraction_report(request: Request, user: models.User = Depends(login_required)):
    try:
        form_data = await request.form()
        
        # 1. Main Report
        report_data = {
            "job_number": form_data.get("job_number"),
            "company": form_data.get("company"),
            "date": form_data.get("date"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "brand": form_data.get("brand"),
            "address": form_data.get("address"),
            "contact_name": form_data.get("contact_name"),
            "contact_number": form_data.get("contact_number"),
            "status": "Submitted",
            "risk_pre": int(form_data.get("risk_pre")) if form_data.get("risk_pre") else None,
            "risk_post": int(form_data.get("risk_post")) if form_data.get("risk_post") else None,
            "cleaning_interval_current": form_data.get("cleaning_interval_current"),
            "cleaning_interval_recommended": form_data.get("cleaning_interval_recommended"),
            "remedial_requirements": form_data.get("remedial_requirements"),
            "risk_improvements": form_data.get("risk_improvements"),
            "sketch_details": form_data.get("sketch_details"),
            "photos_taken": form_data.get("photos_taken"),
            "client_signature": form_data.get("client_signature"),
            "engineer_signature": form_data.get("engineer_signature")
        }
        
        res = supabase.table("extraction_reports").insert(report_data).execute()
        report_id = res.data[0]['id']
        report_jn = res.data[0]['job_number']
        
        # 2. Microns
        m_descs = form_data.getlist("micron_desc[]")
        m_pres = form_data.getlist("micron_pre[]")
        m_posts = form_data.getlist("micron_post[]")
        
        readings = []
        for i in range(len(m_descs)):
            if m_pres[i] or m_posts[i]:
                readings.append({
                    "report_id": report_id,
                    "location": f"T{i+1}",
                    "description": m_descs[i],
                    "pre_clean": int(m_pres[i]) if m_pres[i] else None,
                    "post_clean": int(m_posts[i]) if m_posts[i] else None
                })
        if readings:
            supabase.table("extraction_micron_readings").insert(readings).execute()
            
        # 3. Inspection Items
        i_names = form_data.getlist("item_name[]")
        i_compliances = form_data.getlist("item_compliance[]")
        i_advices = form_data.getlist("item_advice[]")
        
        items = []
        for i in range(len(i_names)):
            items.append({
                "report_id": report_id,
                "item_name": i_names[i],
                "pass_status": (i_compliances[i] == "Compliant"),
                "fail_status": (i_compliances[i] == "Non-Compliant"),
                "advice": i_advices[i]
            })
        if items:
            supabase.table("extraction_inspection_items").insert(items).execute()
            
        # 4. Filter Items
        f_types = form_data.getlist("filter_type[]")
        f_hs = form_data.getlist("filter_h[]")
        f_ws = form_data.getlist("filter_w[]")
        f_ds = form_data.getlist("filter_d[]")
        f_qtys = form_data.getlist("filter_qty[]")
        f_passes = form_data.getlist("filter_pass[]")
        
        filters = []
        for i in range(len(f_types)):
            if f_qtys[i] and int(f_qtys[i]) > 0:
                filters.append({
                    "report_id": report_id,
                    "filter_type": f_types[i],
                    "height": int(f_hs[i]) if f_hs[i] else None,
                    "width": int(f_ws[i]) if f_ws[i] else None,
                    "depth": int(f_ds[i]) if f_ds[i] else None,
                    "quantity": int(f_qtys[i]),
                    "pass_status": (f_passes[i] == "pass"),
                    "fail_status": (f_passes[i] == "fail")
                })
        if filters:
            supabase.table("extraction_filter_items").insert(filters).execute()
            
        # 5. Photos - Upload to Supabase Storage
        from . import supabase_storage
        
        photo_files = form_data.getlist("photos")
        photos = []
        for f in photo_files:
            if hasattr(f, 'filename') and f.filename:
                # Generate unique filename
                filename = f"{report_jn}_{datetime.now().timestamp()}_{f.filename}"
                storage_path = f"reports/{report_jn}/{filename}"
                
                # Read file content
                file_content = await f.read()
                
                # Upload to Supabase Storage
                photo_url = supabase_storage.upload_file(file_content, storage_path)
                    
                photos.append({
                    "report_id": report_id,
                    "photo_type": "Site Evidence",
                    "photo_path": photo_url,  # Now storing URL instead of local path
                    "inspection_item": "Site Survey"
                })
        if photos:
            supabase.table("extraction_photos").insert(photos).execute()
        
        return HTMLResponse(content="<div class='alert alert-success'>Professional report submitted with photos!</div>")
    except Exception as e:
        import traceback
        return HTMLResponse(content=f"<div class='alert alert-error'>Error: {str(e)}<pre>{traceback.format_exc()}</pre></div>", status_code=400)

@app.get("/admin/reports", response_class=HTMLResponse)
def admin_reports(request: Request, user: models.User = Depends(role_required(["Admin", "Manager", "Viewer"]))):
    res = supabase.table("extraction_reports").select("*").order("created_at", desc=True).execute()
    reports = [models.ExtractionReport(**r) for r in res.data]
    
    return templates.TemplateResponse("admin_report_list.html", {
        "request": request,
        "title": "Admin Report Review",
        "user": user,
        "reports": reports
    })

@app.get("/admin/reports/{report_id}", response_class=HTMLResponse)
def review_report(report_id: int, request: Request, user: models.User = Depends(login_required)):
    try:
        res = supabase.table("extraction_reports").select("*").eq("id", report_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Report not found")
        report = models.ExtractionReport(**res.data[0])
        
        # Sync Job notes
        if not report.remedial_requirements:
            j_res = supabase.table("jobs").select("notes").eq("job_number", report.job_number).execute()
            if j_res.data and j_res.data[0]['notes']:
                 supabase.table("extraction_reports").update({"remedial_requirements": j_res.data[0]['notes']}).eq("id", report_id).execute()
                 report.remedial_requirements = j_res.data[0]['notes']

        # Fetch related
        micron_readings = [models.ExtractionMicronReading(**m) for m in supabase.table("extraction_micron_readings").select("*").eq("report_id", report_id).execute().data]
        inspection_items = [models.ExtractionInspectionItem(**i) for i in supabase.table("extraction_inspection_items").select("*").eq("report_id", report_id).execute().data]
        filter_items = [models.ExtractionFilterItem(**f) for f in supabase.table("extraction_filter_items").select("*").eq("report_id", report_id).execute().data]
        photos = [models.ExtractionPhoto(**p) for p in supabase.table("extraction_photos").select("*").eq("report_id", report_id).execute().data]
        
        # Fetch Job for context
        job = None
        j_res_full = supabase.table("jobs").select("*").eq("job_number", report.job_number).execute()
        if j_res_full.data:
            job = models.Job(**j_res_full.data[0])
        
        return templates.TemplateResponse("admin_report_review.html", {
            "request": request,
            "title": f"Review Report: {report.job_number}",
            "user": user,
            "report": report,
            "micron_readings": micron_readings,
            "inspection_items": inspection_items,
            "filter_items": filter_items,
            "photos": photos,
            "job": job
        })
    except Exception as e:
        import traceback
        return HTMLResponse(content=f"<h3>Internal Server Error</h3><pre>{traceback.format_exc()}</pre>", status_code=500)

@app.post("/admin/reports/{report_id}/update")
async def update_report(report_id: int, request: Request, user: models.User = Depends(login_required)):
    form_data = await request.form()
    
    # Update Report
    update_data = {
        "company": form_data.get("company"),
        "address": form_data.get("address"),
        "risk_pre": int(form_data.get("risk_pre")) if form_data.get("risk_pre") else None,
        "risk_post": int(form_data.get("risk_post")) if form_data.get("risk_post") else None,
        "remedial_requirements": form_data.get("remedial_requirements"),
        "risk_improvements": form_data.get("risk_improvements"),
        "sketch_details": form_data.get("sketch_details")
    }
    supabase.table("extraction_reports").update(update_data).eq("id", report_id).execute()
    
    # Update Readings (Iterate all likely existing ones? Or just fetch and update?)
    # Fetch existing
    readings = supabase.table("extraction_micron_readings").select("id").eq("report_id", report_id).execute().data
    for r in readings:
        rid = r['id']
        pre = form_data.get(f"read_pre_{rid}")
        post = form_data.get(f"read_post_{rid}")
        desc = form_data.get(f"read_desc_{rid}")
        
        r_update = {}
        if pre is not None: r_update['pre_clean'] = int(pre) if pre else 0
        if post is not None: r_update['post_clean'] = int(post) if post else 0
        if desc is not None: r_update['description'] = desc
        
        if r_update:
            supabase.table("extraction_micron_readings").update(r_update).eq("id", rid).execute()
            
    # Update Inspection Items
    items = supabase.table("extraction_inspection_items").select("id").eq("report_id", report_id).execute().data
    for item in items:
        iid = item['id']
        status = form_data.get(f"insp_status_{iid}")
        advice = form_data.get(f"insp_advice_{iid}")
        
        i_update = {}
        if status:
            i_update['pass_status'] = (status == "Pass")
            i_update['fail_status'] = (status == "Fail")
        if advice is not None:
             i_update['advice'] = advice
             
        if i_update:
            supabase.table("extraction_inspection_items").update(i_update).eq("id", iid).execute()
            
    return HTMLResponse(content='<div class="alert alert-success">Report saved successfully!</div>')

@app.post("/admin/reports/{report_id}/photos/delete/{photo_id}")
def delete_report_photo(report_id: int, photo_id: int, user: models.User = Depends(login_required)):
    supabase.table("extraction_photos").delete().eq("id", photo_id).execute()
    return HTMLResponse(content="")

@app.post("/admin/reports/{report_id}/photos/upload")
async def upload_report_photo(report_id: int, request: Request, user: models.User = Depends(login_required)):
    from . import supabase_storage
    
    form_data = await request.form()
    file = form_data.get("photo_file")
    type = form_data.get("photo_type", "Post-Clean")
    item = form_data.get("photo_item", "Site Overview")
    
    if file and file.filename:
        # Get report to determine job number for organizing files
        report_res = supabase.table("extraction_reports").select("job_number").eq("id", report_id).execute()
        job_number = report_res.data[0]['job_number'] if report_res.data else str(report_id)
        
        # Generate unique filename and storage path
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        storage_path = f"reports/{job_number}/{filename}"
        
        # Upload to Supabase Storage
        file_content = await file.read()
        photo_url = supabase_storage.upload_file(file_content, storage_path)
            
        supabase.table("extraction_photos").insert({
            "report_id": report_id,
            "photo_type": type,
            "photo_path": photo_url,  # Now storing URL
            "inspection_item": item
        }).execute()
        
    return RedirectResponse(url=f"/admin/reports/{report_id}", status_code=303)

@app.get("/admin/reports/{report_id}/photos/download")
async def download_report_photos(report_id: int, user: models.User = Depends(login_required)):
    """Generate a ZIP file of all photos for a report and stream it to the user"""
    import io
    import zipfile
    import requests
    from fastapi.responses import StreamingResponse
    
    print(f"DEBUG: Download request for report_id={report_id}", flush=True)
    # 1. Get all photos for this report
    photos_res = supabase.table("extraction_photos").select("*").eq("report_id", report_id).execute()
    if not photos_res.data:
        print(f"DEBUG: No photos found for report_id={report_id}", flush=True)
        return HTMLResponse(content=f"No photos found for report {report_id}. Please upload photos first.", status_code=404)
        
    # 2. Get report info for naming
    report_res = supabase.table("extraction_reports").select("job_number").eq("id", report_id).execute()
    jn = report_res.data[0]['job_number'] if report_res.data else str(report_id)
    
    # 3. Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, photo in enumerate(photos_res.data):
            url = photo['photo_path']
            try:
                # Download from Supabase Storage
                response = requests.get(url)
                if response.status_code == 200:
                    # Determine filename
                    ext = url.split('.')[-1].split('?')[0] # Basic extension extraction
                    if len(ext) > 4: ext = 'jpg'
                    fname = f"{jn}_photo_{i+1}_{photo['photo_type'].replace(' ', '_')}.{ext}"
                    zip_file.writestr(fname, response.content)
            except Exception as e:
                print(f"Error adding photo to ZIP: {e}")
                
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer, 
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename=PNJ_{jn}_Photos.zip"}
    )

@app.post("/admin/reports/{report_id}/raise-invoice", response_class=HTMLResponse)
async def raise_invoice(report_id: int, user: models.User = Depends(login_required)):
    # 1. Get Job Info from Report
    report_res = supabase.table("extraction_reports").select("*").eq("id", report_id).execute()
    if not report_res.data:
        return HTMLResponse("<span class='text-error'>Report not found</span>")
    
    report = models.ExtractionReport(**report_res.data[0])
    
    # Find associated Job (Simple lookup by job_number for now, ideally by ID)
    job_res = supabase.table("jobs").select("*").eq("job_number", report.job_number).execute()
    if not job_res.data:
        return HTMLResponse("<span class='text-error'>Job not found</span>")
        
    job = models.Job(**job_res.data[0])
    
    # 2. Call Sage Mock
    from .sage_integration import sage_client
    result = await sage_client.create_invoice(job)
    
    # 3. Update Status on Screen
    if result.get("success"):
        # Ideally record this in DB: invoice_raised=True, sage_invoice_id=...
        # For Test Mode, just show the success badge
        return HTMLResponse(f"""
            <div class="alert alert-success shadow-lg">
                <div>
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <div>
                        <div class="font-bold">Invoice Raised!</div>
                        <div class="text-xs">Sage Ref: {result['invoice_number']}</div>
                    </div>
                </div>
            </div>
        """)
    else:
        return HTMLResponse(f"<span class='text-error'>Starting Invoice Failed</span>")

@app.post("/admin/reports/{report_id}/approve")
def approve_report(report_id: int, user: models.User = Depends(login_required)):
    supabase.table("extraction_reports").update({"status": "Approved"}).eq("id", report_id).execute()
    return HTMLResponse(content="<span class='badge badge-success'>Approved</span>")

# Admin Management Panel Routes
@app.get("/admin/manage", response_class=HTMLResponse)
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
    
    # Default settings if not in DB
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

@app.post("/admin/manage/settings")
def update_settings(request: Request, user: models.User = Depends(role_required(["Admin"]))):
    import asyncio
    form_data = asyncio.run(request.form())
    
    # Update settings in DB
    for key, value in form_data.items():
        # Using upsert logic (check if exists first since Supabase Python client upsert can be tricky with keys)
        check_res = supabase.table("system_settings").select("*").eq("key", key).execute()
        if check_res.data:
            supabase.table("system_settings").update({"value": value}).eq("key", key).execute()
        else:
            supabase.table("system_settings").insert({"key": key, "value": value}).execute()
            
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/clients/add")
def add_client(client_name: str = Form(...), company: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    import secrets
    portal_token = secrets.token_urlsafe(32)
    supabase.table("clients").insert({
        "client_name": client_name,
        "company": company,
        "address": address,
        "portal_token": portal_token
    }).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/clients/edit/{client_name}")
def edit_client(client_name: str, company: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("clients").update({
        "company": company,
        "address": address
    }).eq("client_name", client_name).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/sites/add")
def add_site(client_name: str = Form(...), site_name: str = Form(...), address: str = Form(...), brand_name: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("client_sites").insert({
        "client_name": client_name,
        "site_name": site_name,
        "address": address,
        "brand_name": brand_name if brand_name else None
    }).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/sites/edit/{site_id}")
def edit_site(site_id: int, site_name: str = Form(...), address: str = Form(...), brand_name: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("client_sites").update({
        "site_name": site_name,
        "address": address,
        "brand_name": brand_name if brand_name else None
    }).eq("id", site_id).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/brands/add")
def add_brand(brand_name: str = Form(...), user: models.User = Depends(login_required)):
    supabase.table("brands").insert({"brand_name": brand_name}).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/brands/edit/{brand_id}")
def edit_brand(brand_id: int, brand_name: str = Form(...), user: models.User = Depends(login_required)):
    supabase.table("brands").update({"brand_name": brand_name}).eq("id", brand_id).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/brands/{brand_id}")
def delete_brand(brand_id: int, user: models.User = Depends(login_required)):
    supabase.table("brands").delete().eq("id", brand_id).execute()
    return HTMLResponse(content="")

@app.post("/admin/manage/engineers/add")
def add_engineer(contact_name: str = Form(...), email: str = Form(None), phone: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("engineers").insert({
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "address": address
    }).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/engineers/edit/{contact_name}")
def edit_engineer(contact_name: str, email: str = Form(None), phone: str = Form(None), address: str = Form(None), user: models.User = Depends(login_required)):
    supabase.table("engineers").update({
        "email": email,
        "phone": phone,
        "address": address
    }).eq("contact_name", contact_name).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/engineers/{contact_name}")
def delete_engineer(contact_name: str, user: models.User = Depends(login_required)):
    supabase.table("engineers").delete().eq("contact_name", contact_name).execute()
    return HTMLResponse(content="")

@app.post("/admin/manage/admins/add")
def add_admin(username: str = Form(...), password: str = Form(...), user: models.User = Depends(login_required)):
    hashed_password = security.get_password_hash(password)
    supabase.table("users").insert({
        "username": username,
        "password": hashed_password
    }).execute()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/admins/{admin_id}")
def delete_admin(admin_id: int, user: models.User = Depends(login_required)):
    supabase.table("users").delete().eq("id", admin_id).execute()
    return HTMLResponse(content="")



# Client Portal Routes
@app.get("/client-portal/{token}", response_class=HTMLResponse)
def client_portal(token: str, request: Request):
    """Public client portal - no login required"""
    # Find client by portal token
    client_res = supabase.table("clients").select("*").eq("portal_token", token).execute()
    
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    
    client = models.Client(**client_res.data[0])
    
    # Get all archived/approved jobs for this client
    jobs_res = supabase.table("jobs").select("*").eq("client_name", client.client_name).eq("status", "Archived").order("date", desc=True).execute()
    jobs = [models.Job(**j) for j in jobs_res.data] if jobs_res.data else []
    
    return templates.TemplateResponse("client_portal.html", {
        "request": request,
        "client": client,
        "jobs": jobs,
        "is_admin_preview": False
    })

@app.get("/admin/portal-preview", response_class=HTMLResponse)
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

@app.get("/admin/portal-preview/{client_name}", response_class=HTMLResponse)
def admin_portal_preview_client(client_name: str, request: Request, user: models.User = Depends(login_required)):
    """Admin preview of specific client portal"""
    client_res = supabase.table("clients").select("*").eq("client_name", client_name).execute()
    
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = models.Client(**client_res.data[0])
    
    # Get all archived jobs for this client
    jobs_res = supabase.table("jobs").select("*").eq("client_name", client.client_name).eq("status", "Archived").order("date", desc=True).execute()
    jobs = [models.Job(**j) for j in jobs_res.data] if jobs_res.data else []
    
    return templates.TemplateResponse("client_portal.html", {
        "request": request,
        "client": client,
        "jobs": jobs,
        "is_admin_preview": True,
        "user": user
    })

@app.get("/client-portal/{token}/report/{job_number}", response_class=HTMLResponse)
def portal_view_report(token: str, job_number: str, request: Request):
    """View report in client portal"""
    # Verify token
    client_res = supabase.table("clients").select("*").eq("portal_token", token).execute()
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    
    client = models.Client(**client_res.data[0])
    
    # Get report
    report_res = supabase.table("extraction_reports").select("*").eq("job_number", job_number).execute()
    if not report_res.data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = models.ExtractionReport(**report_res.data[0])
    
    # Verify this report belongs to this client
    job_res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
    if not job_res.data or job_res.data[0]['client_name'] != client.client_name:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Fetch related data
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
        "client": client
    })

@app.get("/client-portal/{token}/pdf/{job_number}")
def portal_download_pdf(token: str, job_number: str):
    """Download PDF report from client portal"""
    # Verify token
    client_res = supabase.table("clients").select("*").eq("portal_token", token).execute()
    if not client_res.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    
    client = models.Client(**client_res.data[0])
    
    # Verify job belongs to client
    job_res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
    if not job_res.data or job_res.data[0]['client_name'] != client.client_name:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Generate PDF from report data
    # For now, return a placeholder response
    return HTMLResponse(content="<h1>PDF Generation Coming Soon</h1><p>This feature will generate a downloadable PDF report.</p>")

# User Management (IAM) Routes
@app.post("/admin/manage/users/add")
async def add_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("Admin"),
    user: models.User = Depends(login_required)
):
    # Only admins can add users
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Access denied")
        
    # Check if user exists
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

@app.post("/admin/manage/users/edit/{user_id}")
async def edit_user(
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: Optional[str] = Form(None),
    role: str = Form("Admin"),
    user: models.User = Depends(login_required)
):
    # Only admins can edit users
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Access denied")
        
    update_data = {
        "username": username,
        "email": email,
        "role": role
    }
    if password:
        update_data["password"] = security.get_password_hash(password)
        
    supabase.table("users").update(update_data).eq("id", user_id).execute()
    return RedirectResponse(url="/admin/manage?success=user_updated", status_code=303)

@app.delete("/admin/manage/users/{user_id}")
def delete_user(user_id: int, user: models.User = Depends(login_required)):
    # Only admins can delete users
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Access denied")
        
    # Prevent self-deletion
    if user.id == user_id:
        return HTMLResponse(content="<div class='alert alert-warning'>Cannot delete yourself!</div>", status_code=400)
        
    supabase.table("users").delete().eq("id", user_id).execute()
    return HTMLResponse(content="")
