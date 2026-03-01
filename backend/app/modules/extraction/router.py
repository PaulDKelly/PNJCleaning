import io
import zipfile
import requests
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

from ... import models
from ...supabase_client import supabase
from ...dependencies import templates, login_required, role_required
from ... import supabase_storage

router = APIRouter()

@router.post("/extraction-report/start")
async def start_extraction_report(request: Request, user: models.User = Depends(login_required)):
    form_data = await request.form()
    job_number = form_data.get("job_number")
    if not job_number:
        raise HTTPException(status_code=400, detail="Job number is required")
    return RedirectResponse(url=f"/extraction-report?job_number={job_number}", status_code=303)

@router.get("/extraction-report", response_class=HTMLResponse)
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
        res = supabase.table("jobs").select("*").eq("job_number", job_number).execute()
        if res.data:
            j_obj = models.Job(**res.data[0])
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

@router.post("/extraction-report")
async def submit_extraction_report(request: Request, user: models.User = Depends(login_required)):
    try:
        form_data = await request.form()
        report_jn = form_data.get("job_number")
        
        # Handle Sketch Photo
        sketch_photo = form_data.get("sketch_photo")
        sketch_photo_url = None
        if hasattr(sketch_photo, 'filename') and sketch_photo.filename:
            filename = f"sketch_{report_jn}_{datetime.now().timestamp()}_{sketch_photo.filename}"
            storage_path = f"reports/{report_jn}/{filename}"
            file_content = await sketch_photo.read()
            sketch_photo_url = supabase_storage.upload_file(file_content, storage_path)

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
            "sketch_photo_path": sketch_photo_url,
            "photos_taken": form_data.get("photos_taken"),
            "client_signature": form_data.get("client_signature"),
            "engineer_signature": form_data.get("engineer_signature")
        }
        
        res = supabase.table("extraction_reports").insert(report_data).execute()
        report_id = res.data[0]['id']
        
        # Microns
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
            
        # Inspection Items
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
            
        # Filter Items
        f_types = form_data.getlist("filter_type[]")
        f_qtys = form_data.getlist("filter_qty[]")
        f_passes = form_data.getlist("filter_pass[]")
        filters = []
        for i in range(len(f_types)):
            if f_qtys[i] and int(f_qtys[i]) > 0:
                filters.append({
                    "report_id": report_id,
                    "filter_type": f_types[i],
                    "quantity": int(f_qtys[i]),
                    "pass_status": (f_passes[i] == "pass"),
                    "fail_status": (f_passes[i] == "fail")
                })
        if filters:
            supabase.table("extraction_filter_items").insert(filters).execute()
            
        # Photos
        photo_files = form_data.getlist("photos")
        photos = []
        for f in photo_files:
            if hasattr(f, 'filename') and f.filename:
                filename = f"{report_jn}_{datetime.now().timestamp()}_{f.filename}"
                storage_path = f"reports/{report_jn}/{filename}"
                file_content = await f.read()
                photo_url = supabase_storage.upload_file(file_content, storage_path)
                photos.append({
                    "report_id": report_id,
                    "photo_type": "Site Evidence",
                    "photo_path": photo_url,
                    "inspection_item": "Site Survey"
                })
        if photos:
            supabase.table("extraction_photos").insert(photos).execute()
        
        return HTMLResponse(content="<div class='alert alert-success'>Professional report submitted with photos!</div>")
    except Exception as e:
        return HTMLResponse(content=f"<div class='alert alert-error'>Error: {str(e)}</div>", status_code=400)

@router.get("/admin/reports", response_class=HTMLResponse)
def admin_reports(request: Request, user: models.User = Depends(role_required(["Admin", "Manager", "Viewer"]))):
    res = supabase.table("extraction_reports").select("*").order("created_at", desc=True).execute()
    reports = []
    for r in (res.data or []):
        try:
            reports.append(models.ExtractionReport(**r))
        except Exception:
            # Keep page resilient to legacy/malformed rows instead of 500-ing the whole list.
            fallback = dict(r)
            created_at_raw = fallback.get("created_at")
            fallback["created_at"] = None
            if isinstance(created_at_raw, str):
                try:
                    fallback["created_at"] = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                except Exception:
                    fallback["created_at"] = None
            reports.append(models.ExtractionReport(**fallback))
    return templates.TemplateResponse("admin_report_list.html", {
        "request": request,
        "title": "Admin Report Review",
        "user": user,
        "reports": reports
    })

@router.get("/admin/reports/{report_id}", response_class=HTMLResponse)
def review_report(report_id: int, request: Request, user: models.User = Depends(login_required)):
    res = supabase.table("extraction_reports").select("*").eq("id", report_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Report not found")
    report = models.ExtractionReport(**res.data[0])
    
    micron_readings = [models.ExtractionMicronReading(**m) for m in supabase.table("extraction_micron_readings").select("*").eq("report_id", report_id).execute().data]
    inspection_items = [models.ExtractionInspectionItem(**i) for i in supabase.table("extraction_inspection_items").select("*").eq("report_id", report_id).execute().data]
    filter_items = [models.ExtractionFilterItem(**f) for f in supabase.table("extraction_filter_items").select("*").eq("report_id", report_id).execute().data]
    photos = [models.ExtractionPhoto(**p) for p in supabase.table("extraction_photos").select("*").eq("report_id", report_id).execute().data]
    
    job = None
    j_res = supabase.table("jobs").select("*").eq("job_number", report.job_number).execute()
    if j_res.data:
        job = models.Job(**j_res.data[0])
    
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

@router.post("/admin/reports/{report_id}/update")
async def update_report(report_id: int, request: Request, user: models.User = Depends(login_required)):
    form_data = await request.form()
    update_data = {
        "company": form_data.get("company"),
        "address": form_data.get("address"),
        "risk_pre": int(form_data.get("risk_pre")) if form_data.get("risk_pre") else None,
        "risk_post": int(form_data.get("risk_post")) if form_data.get("risk_post") else None,
        "remedial_requirements": form_data.get("remedial_requirements"),
        "risk_improvements": form_data.get("risk_improvements")
    }

    sketch_photo = form_data.get("sketch_photo")
    if hasattr(sketch_photo, "filename") and sketch_photo.filename:
        report_res = supabase.table("extraction_reports").select("job_number").eq("id", report_id).execute()
        report_jn = report_res.data[0]["job_number"] if report_res.data else str(report_id)
        filename = f"sketch_{report_jn}_{datetime.now().timestamp()}_{sketch_photo.filename}"
        storage_path = f"reports/{report_jn}/{filename}"
        file_content = await sketch_photo.read()
        update_data["sketch_photo_path"] = supabase_storage.upload_file(file_content, storage_path)

    supabase.table("extraction_reports").update(update_data).eq("id", report_id).execute()
    
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
            
    items = supabase.table("extraction_inspection_items").select("id").eq("report_id", report_id).execute().data
    for item in items:
        iid = item['id']
        status = form_data.get(f"insp_status_{iid}")
        advice = form_data.get(f"insp_advice_{iid}")
        i_update = {}
        if status:
            i_update['pass_status'] = (status == "Pass")
            i_update['fail_status'] = (status == "Fail")
        if advice is not None: i_update['advice'] = advice
        if i_update:
            supabase.table("extraction_inspection_items").update(i_update).eq("id", iid).execute()
            
    return HTMLResponse(content='<div class="alert alert-success">Report saved successfully!</div>')

@router.post("/admin/reports/{report_id}/photos/delete/{photo_id}")
def delete_report_photo(report_id: int, photo_id: int, user: models.User = Depends(login_required)):
    supabase.table("extraction_photos").delete().eq("id", photo_id).execute()
    return HTMLResponse(content="")

@router.post("/admin/reports/{report_id}/photos/upload")
async def upload_report_photo(report_id: int, request: Request, user: models.User = Depends(login_required)):
    form_data = await request.form()
    file = form_data.get("photo_file")
    type = form_data.get("photo_type", "Post-Clean")
    item = form_data.get("photo_item", "Site Overview")
    
    if file and file.filename:
        report_res = supabase.table("extraction_reports").select("job_number").eq("id", report_id).execute()
        job_number = report_res.data[0]['job_number'] if report_res.data else str(report_id)
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        storage_path = f"reports/{job_number}/{filename}"
        file_content = await file.read()
        photo_url = supabase_storage.upload_file(file_content, storage_path)
        supabase.table("extraction_photos").insert({
            "report_id": report_id,
            "photo_type": type,
            "photo_path": photo_url,
            "inspection_item": item
        }).execute()
        
    return RedirectResponse(url=f"/admin/reports/{report_id}", status_code=303)

@router.get("/admin/reports/{report_id}/photos/download")
async def download_report_photos(report_id: int, user: models.User = Depends(login_required)):
    photos_res = supabase.table("extraction_photos").select("*").eq("report_id", report_id).execute()
    if not photos_res.data:
        return HTMLResponse(content="No photos found.", status_code=404)
        
    report_res = supabase.table("extraction_reports").select("job_number").eq("id", report_id).execute()
    jn = report_res.data[0]['job_number'] if report_res.data else str(report_id)
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, photo in enumerate(photos_res.data):
            url = photo['photo_path']
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    ext = url.split('.')[-1].split('?')[0]
                    if len(ext) > 4: ext = 'jpg'
                    fname = f"{jn}_photo_{i+1}_{photo['photo_type'].replace(' ', '_')}.{ext}"
                    zip_file.writestr(fname, response.content)
            except Exception as e:
                print(f"Error adding photo: {e}")
                
    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=PNJ_{jn}_Photos.zip"})

@router.post("/admin/reports/{report_id}/raise-invoice")
async def raise_invoice(report_id: int, user: models.User = Depends(login_required)):
    report_res = supabase.table("extraction_reports").select("*").eq("id", report_id).execute()
    if not report_res.data: return HTMLResponse("<span class='text-error'>Report not found</span>")
    report = models.ExtractionReport(**report_res.data[0])
    job_res = supabase.table("jobs").select("*").eq("job_number", report.job_number).execute()
    if not job_res.data: return HTMLResponse("<span class='text-error'>Job not found</span>")
    job = models.Job(**job_res.data[0])
    
    from ...sage_integration import sage_client
    result = await sage_client.create_invoice(job)
    
    if result.get("success"):
        return HTMLResponse(f"""<div class="alert alert-success">Invoice Raised! Sage Ref: {result['invoice_number']}</div>""")
    else:
        return HTMLResponse(f"<span class='text-error'>Starting Invoice Failed</span>")

@router.post("/admin/reports/{report_id}/approve")
def approve_report(report_id: int, user: models.User = Depends(login_required)):
    supabase.table("extraction_reports").update({"status": "Approved"}).eq("id", report_id).execute()
    return HTMLResponse(content="<span class='badge badge-success'>Approved</span>")
