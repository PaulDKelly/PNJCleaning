from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import get_session, engine
from . import models, security
from jose import jwt
import urllib.parse
from .supabase_client import supabase
import os
import json

app = FastAPI(title="PNJ Extraction Services")

@app.on_event("startup")
def on_startup():
    from .database import init_db
    init_db()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

def get_current_user(request: Request, db: Session = Depends(get_session)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(models.User).filter(models.User.username == username).first()
        return user
    except Exception:
        return None

def login_required(user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    try:
        # Basic summary stats for the dashboard
        total_jobs = db.query(models.Job).count()
        active_engineers = db.query(models.Engineer).count()
        total_clients = db.query(models.Client).count()
        
        recent_jobs = db.query(models.Job).order_by(models.Job.date.desc()).limit(5).all()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "total_jobs": total_jobs,
            "active_engineers": active_engineers,
            "total_clients": total_clients,
            "recent_jobs": recent_jobs,
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

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not security.verify_password(password, user.password):
        return HTMLResponse(content="Invalid username or password", status_code=401)
    
    access_token = security.create_access_token(data={"sub": user.username})
    response = HTMLResponse(content="", status_code=200, headers={"HX-Redirect": "/"})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

    return response
@app.get("/manager-diary", response_class=HTMLResponse)
def management_dashboard(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    # Fetch all jobs for the unified dashboard
    jobs = db.query(models.Job).order_by(models.Job.date.desc()).all()
    
    return templates.TemplateResponse("manager_diary.html", {
        "request": request, 
        "title": "Management Dashboard", 
        "user": user,
        "jobs": jobs
    })

@app.get("/engineer/diary", response_class=HTMLResponse)
def engineer_diary(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    # Filter jobs assigned to the current user (assuming username matches engineer_contact_name)
    jobs = db.query(models.Job).filter(models.Job.engineer_contact_name == user.username).order_by(models.Job.date.desc()).all()
    
    return templates.TemplateResponse("engineer_diary.html", {
        "request": request, 
        "title": "My Jobs Queue", 
        "user": user,
        "jobs": jobs
    })

@app.get("/manager-diary", response_class=HTMLResponse)
def management_dashboard(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    # Fetch all jobs for the unified dashboard
    jobs = db.query(models.Job).order_by(models.Job.date.desc()).all()
    engineers = {e.contact_name: e for e in db.query(models.Engineer).all()}
    
    # Attach WA link to each job object (temporarily)
    for job in jobs:
        eng = engineers.get(job.engineer_contact_name)
        job.wa_link = generate_whatsapp_link(job, eng, request.url.netloc)
    
    return templates.TemplateResponse("manager_diary.html", {
        "request": request,
        "title": "Management Diary",
        "user": user,
        "jobs": jobs
    })

@app.get("/job-allocation", response_class=HTMLResponse)
def job_allocation(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    # Fetch data for dropdowns
    clients = db.query(models.Client).order_by(models.Client.client_name).all()
    engineers = db.query(models.Engineer).order_by(models.Engineer.contact_name).all()
    site_contacts = db.query(models.SiteContact).order_by(models.SiteContact.contact_name).all()
    brands = db.query(models.Brand).order_by(models.Brand.brand_name).all()
    
    return templates.TemplateResponse("job_allocation.html", {
        "request": request, 
        "title": "Job Allocation", 
        "user": user,
        "clients": clients,
        "engineers": engineers,
        "site_contacts": site_contacts,
        "brands": brands
    })

def generate_whatsapp_link(job: models.Job, engineer: models.Engineer, host: str):
    if not engineer or not engineer.phone:
        return None
    
    # Build the direct link for the engineer (Use HTTPS for WhatsApp parsing)
    report_link = f"https://{host}/extraction-report?job_number={job.job_number}"
    
    msg = f"""*PNJ Job Allocation: {job.job_number}*
*Client:* {job.client_name}
*Site:* {job.site_name or 'N/A'}
*Address:* {job.address or 'N/A'}
*Date/Time:* {job.date.strftime('%d/%m/%Y')} @ {job.time.strftime('%H:%M')}
*Priority:* {job.priority}

*Instructions:*
{job.notes or 'Standard extraction clean.'}

{report_link}"""
    
    encoded_msg = urllib.parse.quote(msg)
    # Clean phone number (remove spaces, etc.)
    phone = "".join(filter(str.isdigit, engineer.phone))
    if not phone.startswith('44'):
        if phone.startswith('0'):
            phone = '44' + phone[1:]
        else:
            phone = '44' + phone
            
    return f"https://wa.me/{phone}?text={encoded_msg}"

@app.get("/admin/sites-lookup", response_class=HTMLResponse)
def get_sites_for_client(client_name: str, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    sites = db.query(models.ClientSite).filter(models.ClientSite.client_name == client_name).order_by(models.ClientSite.site_name).all()
    options = "".join([f'<option value="{s.id}">{s.site_name}</option>' for s in sites])
    return HTMLResponse(content=f'<option value="">N/A / Manual Address</option>{options}')

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
    db: Session = Depends(get_session),
    user: models.User = Depends(login_required)
):
    try:
        # Fetch Site details if site_id is provided
        site = None
        if site_id:
            site = db.query(models.ClientSite).filter(models.ClientSite.id == site_id).first()
            
        # 1. Update or create the Job record
        job = db.query(models.Job).filter(models.Job.job_number == job_number).first()
        if not job:
            job = models.Job(job_number=job_number, status="Scheduled")
            db.add(job)
            
        job.date = datetime.strptime(date, '%Y-%m-%d').date()
        job.time = datetime.strptime(time, '%H:%M').time()
        job.priority = priority
        job.client_name = client_name
        job.engineer_contact_name = engineer_name
        job.site_contact_name = site_contact_name
        job.notes = notes
        job.brand = brand_name
        
        if site:
            job.site_name = site.site_name
            job.company = site.site_name # For the report
            job.address = site.address
        else:
            # Fallback for legacy/adhoc
            client = db.query(models.Client).filter(models.Client.client_name == client_name).first()
            if client:
                job.company = client.company or client.client_name
                job.address = client.address
            
        db.commit()
        
        # 2. Get engineer phone for WhatsApp
        engineer = db.query(models.Engineer).filter(models.Engineer.contact_name == engineer_name).first()
        wa_link = generate_whatsapp_link(job, engineer, request.url.netloc)
        
        wa_btn = ""
        if wa_link:
            wa_btn = f"""
            <script>
                // Auto-open WhatsApp dispatch in a new tab
                window.open('{wa_link}', '_blank');
            </script>
            """
        
        return HTMLResponse(content=f"<div class='alert alert-success italic font-bold'>Job successfully allocated & Dispatched!</div>{wa_btn}")
    except Exception as e:
        db.rollback()
        return HTMLResponse(content=f"<div class='alert alert-error'>Error: {str(e)}</div>", status_code=400)

@app.post("/admin/jobs/{job_number}/archive")
def archive_job(job_number: str, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    job = db.query(models.Job).filter(models.Job.job_number == job_number).first()
    if job:
        job.status = "Archived"
        db.commit()
    return HTMLResponse(content="<span class='badge badge-ghost font-bold italic'>Archived</span>")

@app.get("/admin/jobs/archive/search", response_class=HTMLResponse)
def search_archive(q: str = "", db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    query = db.query(models.Job).filter(models.Job.status == "Archived")
    if q:
        query = query.filter(
            (models.Job.job_number.contains(q)) | 
            (models.Job.client_name.contains(q)) |
            (models.Job.site_name.contains(q))
        )
    
    archived_jobs = query.order_by(models.Job.date.desc()).all()
    
    html_rows = ""
    for job in archived_jobs:
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
    
    if not archived_jobs:
        html_rows = "<tr><td colspan='5' class='text-center py-20 text-slate-400 italic'>No matches found in archive.</td></tr>"
        
    return HTMLResponse(content=html_rows)

@app.get("/extraction-report", response_class=HTMLResponse)
def extraction_report(request: Request, job_number: Optional[str] = None, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    # Pre-populate if job_number is provided
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
        # 1. Try to get detailed Job data
        job = db.query(models.Job).filter(models.Job.job_number == job_number).first()
        if job:
            job_info.update({
                "company": job.company or job.client_name,
                "date": job.date,
                "time": job.time,
                "brand": job.brand if hasattr(job, 'brand') else "",
                "address": job.address or "",
                "contact_name": job.site_contact_name or "",
                "contact_phone": job.site_contact_phone or "-"
            })
        else:
            # 2. Fallback to JobSchedule
            schedule = db.query(models.JobSchedule).filter(models.JobSchedule.job_number == job_number).first()
            if schedule:
                job_info.update({
                    "company": schedule.client_name,
                    "date": schedule.date,
                    "time": schedule.time,
                    "brand": schedule.brand or ""
                })
                # Join with Client for address
                client = db.query(models.Client).filter(models.Client.client_name == schedule.client_name).first()
                if client:
                    job_info["company"] = client.company or client.client_name
                    job_info["address"] = client.address or ""
            
    return templates.TemplateResponse("extraction_report.html", {
        "request": request, 
        "title": "Extraction Report", 
        "user": user,
        "job": job_info
    })

@app.post("/extraction-report")
async def submit_extraction_report(
    request: Request,
    db: Session = Depends(get_session),
    user: models.User = Depends(login_required)
):
    try:
        form_data = await request.form()
        
        # 1. Create Main Report
        report = models.ExtractionReport(
            job_number=form_data.get("job_number"),
            company=form_data.get("company"),
            date=datetime.strptime(form_data.get("date"), '%Y-%m-%d').date(),
            time=datetime.now().time(), # Simplification for now
            brand=form_data.get("brand"),
            address=form_data.get("address"),
            contact_name=form_data.get("contact_name"),
            contact_number=form_data.get("contact_number"),
            status="Submitted",
            risk_pre=int(form_data.get("risk_pre")) if form_data.get("risk_pre") else None,
            risk_post=int(form_data.get("risk_post")) if form_data.get("risk_post") else None,
            cleaning_interval_current=form_data.get("cleaning_interval_current"),
            cleaning_interval_recommended=form_data.get("cleaning_interval_recommended"),
            remedial_requirements=form_data.get("remedial_requirements"),
            risk_improvements=form_data.get("risk_improvements"),
            sketch_details=form_data.get("sketch_details"),
            photos_taken=form_data.get("photos_taken"),
            client_signature=form_data.get("client_signature"),
            engineer_signature=form_data.get("engineer_signature")
        )
        db.add(report)
        db.flush() # Get report.id
        
        # 2. Add Micron Readings
        m_descs = form_data.getlist("micron_desc[]")
        m_pres = form_data.getlist("micron_pre[]")
        m_posts = form_data.getlist("micron_post[]")
        
        for i in range(len(m_descs)):
            if m_pres[i] or m_posts[i]:
                reading = models.ExtractionMicronReading(
                    report_id=report.id,
                    location=f"T{i+1}",
                    description=m_descs[i],
                    pre_clean=int(m_pres[i]) if m_pres[i] else None,
                    post_clean=int(m_posts[i]) if m_posts[i] else None
                )
                db.add(reading)
        
        # 3. Add Inspection Items
        i_names = form_data.getlist("item_name[]")
        i_compliances = form_data.getlist("item_compliance[]")
        i_advices = form_data.getlist("item_advice[]")
        
        for i in range(len(i_names)):
            item = models.ExtractionInspectionItem(
                report_id=report.id,
                item_name=i_names[i],
                pass_status=(i_compliances[i] == "Compliant"),
                fail_status=(i_compliances[i] == "Non-Compliant"),
                advice=i_advices[i]
            )
            db.add(item)

        # 4. Add Filter Items
        f_types = form_data.getlist("filter_type[]")
        f_hs = form_data.getlist("filter_h[]")
        f_ws = form_data.getlist("filter_w[]")
        f_ds = form_data.getlist("filter_d[]")
        f_qtys = form_data.getlist("filter_qty[]")
        f_passes = form_data.getlist("filter_pass[]")

        for i in range(len(f_types)):
            if f_qtys[i] and int(f_qtys[i]) > 0:
                f_item = models.ExtractionFilterItem(
                    report_id=report.id,
                    filter_type=f_types[i],
                    height=int(f_hs[i]) if f_hs[i] else None,
                    width=int(f_ws[i]) if f_ws[i] else None,
                    depth=int(f_ds[i]) if f_ds[i] else None,
                    quantity=int(f_qtys[i]),
                    pass_status=(f_passes[i] == "pass"),
                    fail_status=(f_passes[i] == "fail")
                )
                db.add(f_item)
            
        # 5. Process Photo Uploads
        photo_files = form_data.getlist("photos")
        upload_dir = "backend/app/static/uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        for f in photo_files:
            if hasattr(f, 'filename') and f.filename:
                # Use a clear filename convention
                filename = f"{report.job_number}_{datetime.now().timestamp()}_{f.filename}"
                filepath = os.path.join(upload_dir, filename)
                
                # Save the file
                with open(filepath, "wb") as buffer:
                    buffer.write(await f.read())
                    
                # Create DB record
                new_photo = models.ExtractionPhoto(
                    report_id=report.id,
                    photo_type="Site Evidence", # Manager will curate as Before/After
                    photo_path=filepath,
                    inspection_item="Site Survey"
                )
                db.add(new_photo)

        db.commit()
        return HTMLResponse(content="<div class='alert alert-success'>Professional report submitted with photos!</div>")
    except Exception as e:
        db.rollback()
        import traceback
        return HTMLResponse(content=f"<div class='alert alert-error'>Error: {str(e)}<pre>{traceback.format_exc()}</pre></div>", status_code=400)

@app.get("/admin/reports", response_class=HTMLResponse)
def admin_reports(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    # Fetch all submitted reports for review
    reports = db.query(models.ExtractionReport).order_by(models.ExtractionReport.created_at.desc()).all()
    
    return templates.TemplateResponse("admin_report_list.html", {
        "request": request,
        "title": "Admin Report Review",
        "user": user,
        "reports": reports
    })

@app.get("/admin/reports/{report_id}", response_class=HTMLResponse)
def review_report(report_id: int, request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    try:
        report = db.query(models.ExtractionReport).filter(models.ExtractionReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
            
        # Sync Job notes if report remedial_requirements/risk_improvements are still default
        job = db.query(models.Job).filter(models.Job.job_number == report.job_number).first()
        if job and not report.remedial_requirements:
            report.remedial_requirements = job.notes
            db.add(report)
            db.commit()
            db.refresh(report)

        # Fetch related items
        micron_readings = db.query(models.ExtractionMicronReading).filter(models.ExtractionMicronReading.report_id == report_id).all()
        inspection_items = db.query(models.ExtractionInspectionItem).filter(models.ExtractionInspectionItem.report_id == report_id).all()
        filter_items = db.query(models.ExtractionFilterItem).filter(models.ExtractionFilterItem.report_id == report_id).all()
        photos = db.query(models.ExtractionPhoto).filter(models.ExtractionPhoto.report_id == report_id).all()
        
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
        error_details = traceback.format_exc()
        return HTMLResponse(content=f"<h3>Internal Server Error</h3><pre>{error_details}</pre>", status_code=500)

@app.post("/admin/reports/{report_id}/update")
async def update_report(report_id: int, request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    form_data = await request.form()
    report = db.query(models.ExtractionReport).filter(models.ExtractionReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Update main report fields
    report.company = form_data.get("company")
    report.address = form_data.get("address")
    report.risk_pre = int(form_data.get("risk_pre")) if form_data.get("risk_pre") else None
    report.risk_post = int(form_data.get("risk_post")) if form_data.get("risk_post") else None
    report.remedial_requirements = form_data.get("remedial_requirements")
    report.risk_improvements = form_data.get("risk_improvements")
    report.sketch_details = form_data.get("sketch_details")
    
    # Update Micron Readings
    readings = db.query(models.ExtractionMicronReading).filter(models.ExtractionMicronReading.report_id == report_id).all()
    for m in readings:
        pre = form_data.get(f"read_pre_{m.id}")
        post = form_data.get(f"read_post_{m.id}")
        desc = form_data.get(f"read_desc_{m.id}")
        if pre is not None: m.pre_clean = int(pre) if pre else 0
        if post is not None: m.post_clean = int(post) if post else 0
        if desc is not None: m.description = desc
        db.add(m)
        
    # Update Inspection Items
    items = db.query(models.ExtractionInspectionItem).filter(models.ExtractionInspectionItem.report_id == report_id).all()
    for item in items:
        status = form_data.get(f"insp_status_{item.id}")
        advice = form_data.get(f"insp_advice_{item.id}")
        if status == "Pass":
            item.pass_status = True
            item.fail_status = False
        elif status == "Fail":
            item.pass_status = False
            item.fail_status = True
        else:
            item.pass_status = False
            item.fail_status = False
            
        if advice is not None: item.advice = advice
        db.add(item)
        
    db.commit()
    return HTMLResponse(content='<div class="alert alert-success">Report saved successfully!</div>')

@app.post("/admin/reports/{report_id}/photos/delete/{photo_id}")
def delete_report_photo(report_id: int, photo_id: int, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    photo = db.query(models.ExtractionPhoto).filter(models.ExtractionPhoto.id == photo_id).first()
    if photo:
        # We don't delete the physical file yet to be safe, just the record from the report curation
        db.delete(photo)
        db.commit()
    return HTMLResponse(content="") # Empty response removes the element via HTMX

@app.post("/admin/reports/{report_id}/photos/upload")
async def upload_report_photo(report_id: int, request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    form_data = await request.form()
    file = form_data.get("photo_file")
    type = form_data.get("photo_type", "Post-Clean")
    item = form_data.get("photo_item", "Site Overview")
    
    if file and file.filename:
        # Save file to static/uploads
        upload_dir = "backend/app/static/uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())
            
        new_photo = models.ExtractionPhoto(
            report_id=report_id,
            photo_type=type,
            photo_path=filepath,
            inspection_item=item
        )
        db.add(new_photo)
        db.commit()
        
    # Redirect back to the report view (or return a partial if using HTMX)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/admin/reports/{report_id}", status_code=303)

@app.post("/admin/reports/{report_id}/approve")
def approve_report(report_id: int, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    report = db.query(models.ExtractionReport).filter(models.ExtractionReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.status = "Approved"
    db.commit()
    
    return HTMLResponse(content="<div class='alert alert-success'>Report approved and ready for client delivery!</div>")

@app.get("/admin/reports/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    try:
        from . import report_generator
        from fastapi.responses import FileResponse
        import os
        
        report = db.query(models.ExtractionReport).filter(models.ExtractionReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
            
        micron_readings = db.query(models.ExtractionMicronReading).filter(models.ExtractionMicronReading.report_id == report_id).all()
        inspection_items = db.query(models.ExtractionInspectionItem).filter(models.ExtractionInspectionItem.report_id == report_id).all()
        # FIX: Also fetch filter_items and photos
        filter_items = db.query(models.ExtractionFilterItem).filter(models.ExtractionFilterItem.report_id == report_id).all()
        photos = db.query(models.ExtractionPhoto).filter(models.ExtractionPhoto.report_id == report_id).all()
        
        filename = f"PNJ_Report_{report.job_number}.pdf".replace("/", "_")
        # Ensure temp directory exists
        if not os.path.exists("temp_reports"):
            os.makedirs("temp_reports")
            
        output_path = os.path.join("temp_reports", filename)
        
        report_generator.generate_client_pdf(report, micron_readings, inspection_items, filter_items, photos, output_path)
        
        return FileResponse(output_path, media_type='application/pdf', filename=filename)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HTMLResponse(content=f"<h3>Internal Server Error during PDF Generation</h3><pre>{error_details}</pre>", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
@app.get("/admin/manage", response_class=HTMLResponse)
def manage_lists(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    brands = db.query(models.Brand).order_by(models.Brand.brand_name).all()
    clients = db.query(models.Client).order_by(models.Client.client_name).all()
    sites = db.query(models.ClientSite).order_by(models.ClientSite.site_name).all()
    engineers = db.query(models.Engineer).order_by(models.Engineer.contact_name).all()
    admins = db.query(models.User).order_by(models.User.username).all()
    
    return templates.TemplateResponse("manage_lists.html", {
        "request": request,
        "title": "Resource Management",
        "brands": brands,
        "clients": clients,
        "sites": sites,
        "engineers": engineers,
        "admins": admins,
        "user": user
    })

# Brand CRUD
@app.post("/admin/manage/brands/add")
def add_brand(brand_name: str = Form(...), db: Session = Depends(get_session)):
    try:
        brand = models.Brand(brand_name=brand_name)
        db.add(brand)
        db.commit()
    except Exception:
        db.rollback()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/brands/edit/{brand_id}")
def edit_brand(brand_id: int, brand_name: str = Form(...), db: Session = Depends(get_session)):
    brand = db.query(models.Brand).filter(models.Brand.id == brand_id).first()
    if brand:
        brand.brand_name = brand_name
        db.add(brand)
        db.commit()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/brands/{brand_id}")
def delete_brand(brand_id: int, db: Session = Depends(get_session)):
    brand = db.query(models.Brand).filter(models.Brand.id == brand_id).first()
    if brand:
        db.delete(brand)
        db.commit()
    return HTMLResponse(content="")

# Client CRUD
@app.post("/admin/manage/clients/add")
def add_client(client_name: str = Form(...), company: Optional[str] = Form(None), address: Optional[str] = Form(None), db: Session = Depends(get_session)):
    try:
        client = models.Client(client_name=client_name, company=company, address=address)
        db.add(client)
        db.commit()
    except Exception:
        db.rollback()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/clients/edit/{client_name}")
def edit_client(client_name: str, company: Optional[str] = Form(None), address: Optional[str] = Form(None), db: Session = Depends(get_session)):
    client = db.query(models.Client).filter(models.Client.client_name == client_name).first()
    if client:
        client.company = company
        client.address = address
        db.add(client)
        db.commit()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/clients/{client_name}")
def delete_client(client_name: str, db: Session = Depends(get_session)):
    client = db.query(models.Client).filter(models.Client.client_name == client_name).first()
    if client:
        db.delete(client)
        db.commit()
    return HTMLResponse(content="")

# Site CRUD
@app.post("/admin/manage/sites/add")
def add_site(
    client_name: str = Form(...), 
    site_name: str = Form(...), 
    address: Optional[str] = Form(None), 
    brand_name: Optional[str] = Form(None),
    db: Session = Depends(get_session)
):
    try:
        site = models.ClientSite(
            client_name=client_name, 
            site_name=site_name, 
            address=address, 
            brand_name=brand_name
        )
        db.add(site)
        db.commit()
    except Exception:
        db.rollback()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/sites/edit/{site_id}")
def edit_site(
    site_id: int,
    site_name: str = Form(...),
    address: Optional[str] = Form(None),
    brand_name: Optional[str] = Form(None),
    db: Session = Depends(get_session)
):
    site = db.query(models.ClientSite).filter(models.ClientSite.id == site_id).first()
    if site:
        site.site_name = site_name
        site.address = address
        site.brand_name = brand_name
        db.add(site)
        db.commit()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/sites/{site_id}")
def delete_site(site_id: int, db: Session = Depends(get_session)):
    site = db.query(models.ClientSite).filter(models.ClientSite.id == site_id).first()
    if site:
        db.delete(site)
        db.commit()
    return HTMLResponse(content="")

# Engineer CRUD
@app.post("/admin/manage/engineers/add")
def add_engineer(contact_name: str = Form(...), email: str = Form(None), phone: str = Form(None), address: str = Form(None), db: Session = Depends(get_session)):
    try:
        eng = models.Engineer(contact_name=contact_name, email=email, phone=phone, address=address)
        db.add(eng)
        db.commit()
    except Exception:
        db.rollback()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.post("/admin/manage/engineers/edit/{name}")
def edit_engineer(name: str, email: Optional[str] = Form(None), phone: Optional[str] = Form(None), address: Optional[str] = Form(None), db: Session = Depends(get_session)):
    eng = db.query(models.Engineer).filter(models.Engineer.contact_name == name).first()
    if eng:
        eng.email = email
        eng.phone = phone
        eng.address = address
        db.add(eng)
        db.commit()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/engineers/{name}")
def delete_engineer(name: str, db: Session = Depends(get_session)):
    eng = db.query(models.Engineer).filter(models.Engineer.contact_name == name).first()
    if eng:
        db.delete(eng)
        db.commit()
    return HTMLResponse(content="")

# Admin User CRUD
@app.post("/admin/manage/admins/add")
def add_admin(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_session)):
    try:
        hashed_pw = security.get_password_hash(password)
        new_user = models.User(username=username, password=hashed_pw)
        db.add(new_user)
        db.commit()
    except Exception:
        db.rollback()
    return RedirectResponse(url="/admin/manage", status_code=303)

@app.delete("/admin/manage/admins/{user_id}")
def delete_admin(user_id: int, db: Session = Depends(get_session)):
    admin = db.query(models.User).filter(models.User.id == user_id).first()
    if admin:
        db.delete(admin)
        db.commit()
    return HTMLResponse(content="")

# Client Portal System (Phase 9)
@app.get("/portal/{token}", response_class=HTMLResponse)
def client_portal(request: Request, token: str, db: Session = Depends(get_session)):
    client = db.query(models.Client).filter(models.Client.portal_token == token).first()
    if not client or not client.portal_enabled:
        raise HTTPException(status_code=404, detail="Portal not found or disabled")
    
    # Check if a manager is previewing
    current_user = get_current_user(request, db)
    is_admin_preview = current_user is not None
    
    # Fetch all archived/archived jobs for this client
    # Jobs are linked by client_name
    jobs = db.query(models.Job).filter(
        models.Job.client_name == client.client_name,
        models.Job.status == "Archived"
    ).order_by(models.Job.date.desc()).all()
    
    # Also fetch reports directly if any are approved but not yet archived
    # (Optional: Let's stick to Archived for the official portal)
    
    return templates.TemplateResponse("client_portal.html", {
        "request": request,
        "client": client,
        "jobs": jobs,
        "title": f"Client Portal - {client.client_name}",
        "is_admin_preview": is_admin_preview,
        "user": current_user
    })

@app.get("/portal/{token}/report/{job_number}", response_class=HTMLResponse)
def share_report_view(token: str, job_number: str, request: Request, db: Session = Depends(get_session)):
    client = db.query(models.Client).filter(models.Client.portal_token == token).first()
    if not client or not client.portal_enabled:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check if a manager is previewing
    current_user = get_current_user(request, db)
    is_admin_preview = current_user is not None
    
    # Ensure job belongs to client
    job = db.query(models.Job).filter(models.Job.job_number == job_number, models.Job.client_name == client.client_name).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    report = db.query(models.ExtractionReport).filter(models.ExtractionReport.job_number == job_number).first()
    if not report:
         raise HTTPException(status_code=404, detail="Report not found")
         
    # Reuse the review_report logic but simplified for client view (no edit)
    micron_readings = db.query(models.ExtractionMicronReading).filter(models.ExtractionMicronReading.report_id == report.id).all()
    photos = db.query(models.ExtractionPhoto).filter(models.ExtractionPhoto.report_id == report.id).all()
    inspection_items = db.query(models.ExtractionInspectionItem).filter(models.ExtractionInspectionItem.report_id == report.id).all()
    
    return templates.TemplateResponse("report_view_portal.html", {
        "request": request,
        "report": report,
        "micron_readings": micron_readings,
        "photos": photos,
        "inspection_items": inspection_items,
        "client": client,
        "token": token,
        "is_admin_preview": is_admin_preview,
        "user": current_user
    })

@app.get("/portal/{token}/pdf/{job_number}")
def download_pdf_portal(token: str, job_number: str, db: Session = Depends(get_session)):
    client = db.query(models.Client).filter(models.Client.portal_token == token).first()
    if not client or not client.portal_enabled:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    job = db.query(models.Job).filter(models.Job.job_number == job_number, models.Job.client_name == client.client_name).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # This mirrors the admin download route but validates token
    from .report_generator import generate_professional_pdf
    from fastapi.responses import FileResponse
    
    pdf_path = generate_professional_pdf(job_number, db)
    return FileResponse(pdf_path, filename=f"PNJ_Report_{job_number}.pdf", media_type="application/pdf")

@app.get("/admin/portal-preview", response_class=HTMLResponse)
def admin_portal_preview(request: Request, db: Session = Depends(get_session), user: models.User = Depends(login_required)):
    # Fetch all clients to allow picking one
    clients = db.query(models.Client).order_by(models.Client.client_name).all()
    return templates.TemplateResponse("admin_portal_preview.html", {
        "request": request,
        "clients": clients,
        "user": user,
        "title": "Portal Selector - Admin View"
    })
