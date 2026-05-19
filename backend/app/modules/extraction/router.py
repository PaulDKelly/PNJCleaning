import io
import json
import os
import smtplib
import tempfile
import threading
import zipfile
import requests
import re
import html
from email.message import EmailMessage
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from postgrest.exceptions import APIError

from ... import models
from ...supabase_client import supabase
from ...dependencies import templates, login_required, role_required, get_current_user
from ... import supabase_storage
from ...utils import _normalize_uk_phone

router = APIRouter()

MEDIA_ROW_LIMIT = 20


def _get_engineer_by_token(token: Optional[str]):
    if not token:
        return None
    res = supabase.table("engineers").select("*").eq("access_token", token).execute()
    if res.data:
        return models.Engineer(**res.data[0])
    return None


def _engineer_can_access_job(engineer: Optional[models.Engineer], job_number: Optional[str]) -> bool:
    if not engineer or not job_number:
        return True
    res = supabase.table("jobs").select("engineer_contact_name").eq("job_number", job_number).execute()
    if not res.data:
        return False
    if (res.data[0].get("engineer_contact_name") or "") == engineer.contact_name:
        return True
    try:
        assignment_res = (
            supabase.table("job_engineers")
            .select("id")
            .eq("job_number", job_number)
            .eq("engineer_contact_name", engineer.contact_name)
            .limit(1)
            .execute()
        )
        return bool(assignment_res.data)
    except Exception as exc:
        print(f"Warning: job_engineers access lookup unavailable: {exc}")
        return False


def _get_engineer_role_for_job(engineer: Optional[models.Engineer], job_number: Optional[str]) -> Optional[str]:
    if not engineer or not job_number:
        return None
    res = supabase.table("jobs").select("engineer_contact_name").eq("job_number", job_number).execute()
    if res.data and (res.data[0].get("engineer_contact_name") or "") == engineer.contact_name:
        return "Lead"
    try:
        assignment_res = (
            supabase.table("job_engineers")
            .select("engineer_role")
            .eq("job_number", job_number)
            .eq("engineer_contact_name", engineer.contact_name)
            .limit(1)
            .execute()
        )
        if assignment_res.data:
            return assignment_res.data[0].get("engineer_role") or "Contributing"
    except Exception as exc:
        print(f"Warning: job_engineers role lookup unavailable: {exc}")
    return None


def _get_job_contributions(job_number: Optional[str]) -> list:
    if not job_number:
        return []
    try:
        res = (
            supabase.table("job_contributions")
            .select("*")
            .eq("job_number", job_number)
            .order("created_at", desc=True)
            .execute()
        )
        return [models.JobContribution(**row) for row in (res.data or [])]
    except Exception as exc:
        print(f"Warning: job_contributions lookup unavailable: {exc}")
        return []


def _send_report_email(to_email: str, subject: str, body: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_from = os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME")
    if not smtp_host or not smtp_from or not to_email:
        print(f"Report email notification skipped for {to_email}: SMTP_HOST/SMTP_FROM not configured")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_from
    message["To"] = to_email
    message.set_content(body)

    port = int(os.getenv("SMTP_PORT", "587"))
    timeout = int(os.getenv("SMTP_TIMEOUT", "8"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_ssl = os.getenv("SMTP_SSL", "").lower() in {"1", "true", "yes"}
    use_starttls = os.getenv("SMTP_STARTTLS", "1").lower() not in {"0", "false", "no"}

    print(
        "Report email notification sending "
        f"to={to_email} host={smtp_host} port={port} "
        f"from={smtp_from} username_set={bool(username)} password_set={bool(password)} "
        f"ssl={use_ssl} starttls={use_starttls}"
    )

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, port, timeout=timeout) as smtp:
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(smtp_host, port, timeout=timeout) as smtp:
            if use_starttls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    print(f"Report email notification sent to={to_email}")
    return True


def _send_report_whatsapp(phone: str, message: str):
    webhook_url = os.getenv("WHATSAPP_NOTIFY_WEBHOOK_URL")
    normalized_phone = _normalize_uk_phone(phone)
    if not webhook_url or not normalized_phone:
        print(f"Report WhatsApp notification skipped for {phone}: WHATSAPP_NOTIFY_WEBHOOK_URL/phone not configured")
        return False
    response = requests.post(webhook_url, json={"to": normalized_phone, "message": message}, timeout=10)
    response.raise_for_status()
    return True


def _notify_report_submitted(report_data: dict, report_id: int, host: str):
    settings_res = supabase.table("system_settings").select("value").eq("key", "report_notification_recipients").execute()
    if not settings_res.data:
        print("Report notification skipped: no report_notification_recipients setting found")
        return
    try:
        preferences = json.loads(settings_res.data[0].get("value") or "[]")
    except json.JSONDecodeError:
        print("Report notification skipped: report_notification_recipients is not valid JSON")
        return
    user_ids = [int(item["user_id"]) for item in preferences if str(item.get("user_id", "")).isdigit()]
    if not user_ids:
        print("Report notification skipped: no selected administrator recipients")
        return

    admins_res = supabase.table("users").select("*").in_("id", user_ids).execute()
    admins_by_id = {int(admin["id"]): admin for admin in admins_res.data or [] if admin.get("id") is not None}
    print(f"Report notification loaded {len(preferences)} preferences and {len(admins_by_id)} matching users")
    protocol = "http" if host.split(":", 1)[0] in {"localhost", "127.0.0.1", "0.0.0.0"} else "https"
    report_url = f"{protocol}://{host}/admin/reports/{report_id}"
    job_number = report_data.get("job_number") or "Unknown job"
    company = report_data.get("company") or "Unknown company"
    subject = f"PNJ report submitted: {job_number}"
    body = (
        f"A report has been submitted.\n\n"
        f"Job: {job_number}\n"
        f"Company: {company}\n"
        f"Type: {report_data.get('job_type') or 'Extraction'}\n"
        f"Review: {report_url}"
    )

    for preference in preferences:
        admin = admins_by_id.get(int(preference.get("user_id", 0)))
        if not admin:
            print(f"Report notification skipped preference with missing user_id={preference.get('user_id')}")
            continue
        try:
            if preference.get("email"):
                _send_report_email(admin.get("email"), subject, body)
            if preference.get("whatsapp"):
                _send_report_whatsapp(preference.get("whatsapp_number"), body)
        except Exception as exc:
            print(f"Report notification failed for admin {admin.get('id')}: {exc}")


def _notify_report_submitted_async(report_data: dict, report_id: int, host: str):
    """Send report notifications in the background so report submission can finish."""
    thread = threading.Thread(
        target=_notify_report_submitted,
        args=(dict(report_data), report_id, host),
        daemon=True
    )
    thread.start()


def _insert_with_schema_fallback(table_name: str, payload: dict):
    """Insert a record while tolerating stale PostgREST schema caches."""
    working_payload = dict(payload)
    while True:
        try:
            return supabase.table(table_name).insert(working_payload).execute()
        except APIError as exc:
            message = str(exc)
            match = re.search(r"Could not find the '([^']+)' column of '([^']+)'", message)
            if not match or match.group(2) != table_name:
                raise
            missing_column = match.group(1)
            if missing_column not in working_payload:
                raise
            working_payload.pop(missing_column, None)
            print(f"Warning: {table_name}.{missing_column} missing from schema cache; retrying insert without it")


def _update_with_schema_fallback(table_name: str, payload: dict, match_column: str, match_value):
    """Update a record while dropping unknown columns if the live schema is behind."""
    working_payload = {k: v for k, v in payload.items() if v is not None}
    if not working_payload:
        return None
    while True:
        try:
            return supabase.table(table_name).update(working_payload).eq(match_column, match_value).execute()
        except APIError as exc:
            message = str(exc)
            match = re.search(r"Could not find the '([^']+)' column of '([^']+)'", message)
            if not match or match.group(2) != table_name:
                raise
            missing_column = match.group(1)
            if missing_column not in working_payload:
                raise
            working_payload.pop(missing_column, None)
            print(f"Warning: {table_name}.{missing_column} missing from schema cache; retrying update without it")


async def _build_media_entries(report_id: int, form_data, report_jn: str):
    """Collect both legacy uploads and paired before/after media rows."""
    media_entries = []

    # Legacy bulk uploads remain supported for existing forms.
    for f in form_data.getlist("photos"):
        if hasattr(f, 'filename') and f.filename:
            media_entries.append({
                "file": f,
                "photo_type": "Site Evidence",
                "inspection_item": "Site Survey"
            })

    locations = form_data.getlist("photo_location[]")[:MEDIA_ROW_LIMIT]
    before_files = form_data.getlist("before_media[]")[:MEDIA_ROW_LIMIT]
    after_files = form_data.getlist("after_media[]")[:MEDIA_ROW_LIMIT]

    max_rows = max(len(locations), len(before_files), len(after_files))
    for index in range(max_rows):
        location = locations[index] if index < len(locations) else ""
        before_file = before_files[index] if index < len(before_files) else None
        after_file = after_files[index] if index < len(after_files) else None
        location_label = (location or f"Evidence Row {index + 1}").strip()

        if hasattr(before_file, 'filename') and before_file.filename:
            media_entries.append({
                "file": before_file,
                "photo_type": "Before Clean",
                "inspection_item": location_label
            })
        if hasattr(after_file, 'filename') and after_file.filename:
            media_entries.append({
                "file": after_file,
                "photo_type": "After Clean",
                "inspection_item": location_label
            })

    photos = []
    for entry in media_entries:
        upload = entry["file"]
        filename = f"{report_jn}_{datetime.now().timestamp()}_{upload.filename}"
        storage_path = f"reports/{report_jn}/{filename}"
        file_content = await upload.read()
        photo_url = supabase_storage.upload_file(file_content, storage_path)
        photos.append({
            "report_id": report_id,
            "photo_type": entry["photo_type"],
            "photo_path": photo_url,
            "inspection_item": entry["inspection_item"]
        })

    return photos

@router.post("/extraction-report/start")
async def start_extraction_report(request: Request, user: models.User = Depends(get_current_user)):
    form_data = await request.form()
    job_number = form_data.get("job_number")
    portal_token = form_data.get("portal_token")
    engineer = _get_engineer_by_token(portal_token)
    if not user and not engineer:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not job_number:
        raise HTTPException(status_code=400, detail="Job number is required")
    if engineer and not _engineer_can_access_job(engineer, job_number):
        raise HTTPException(status_code=403, detail="This job is not assigned to this engineer")
    suffix = f"&portal_token={portal_token}" if portal_token else ""
    return RedirectResponse(url=f"/extraction-report?job_number={job_number}{suffix}", status_code=303)

@router.get("/extraction-report", response_class=HTMLResponse)
def extraction_report(
    request: Request,
    job_number: Optional[str] = None,
    job_type: Optional[str] = None,
    portal_token: Optional[str] = None,
    user: models.User = Depends(get_current_user)
):
    engineer = _get_engineer_by_token(portal_token)
    if not user and not engineer:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if engineer and not _engineer_can_access_job(engineer, job_number):
        raise HTTPException(status_code=403, detail="This job is not assigned to this engineer")
    job_info = {
        "job_number": job_number or "",
        "company": "",
        "date": None,
        "time": None,
        "brand": "",
        "address": "",
        "contact_name": "",
        "contact_phone": "-",
        "job_type": job_type or "Extraction"
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
                "contact_phone": j_obj.site_contact_phone or "-",
                "job_type": j_obj.job_type or job_type or "Extraction"
            })
    
    report_template = "extraction_report.html" if job_info["job_type"] == "Extraction" else "callout_report.html"
    report_title = "Extraction Report" if job_info["job_type"] == "Extraction" else "Breakdown / Callout Report"
    engineer_role = _get_engineer_role_for_job(engineer, job_number) if engineer else None
    contributions = _get_job_contributions(job_number)
    return templates.TemplateResponse(report_template, {
        "request": request, 
        "title": report_title, 
        "user": user,
        "engineer": engineer,
        "engineer_role": engineer_role,
        "can_contribute": bool(engineer and engineer_role),
        "can_submit_report": bool(user or not engineer or engineer_role == "Lead"),
        "contributions": contributions,
        "portal_token": portal_token,
        "job": job_info
    })


@router.post("/extraction-report/contribute", response_class=HTMLResponse)
async def submit_job_contribution(request: Request, user: models.User = Depends(get_current_user)):
    form_data = await request.form()
    job_number = (form_data.get("job_number") or "").strip()
    portal_token = form_data.get("portal_token")
    note = (form_data.get("contribution_note") or "").strip()
    engineer = _get_engineer_by_token(portal_token)

    if not engineer:
        raise HTTPException(status_code=401, detail="Engineer portal token is required")
    if not job_number:
        return HTMLResponse("<div class='alert alert-error text-sm'>Job number is required.</div>")
    if not _engineer_can_access_job(engineer, job_number):
        raise HTTPException(status_code=403, detail="This job is not assigned to this engineer")

    engineer_role = _get_engineer_role_for_job(engineer, job_number) or "Contributing"
    uploads = [
        upload for upload in form_data.getlist("contribution_media")
        if hasattr(upload, "filename") and upload.filename
    ]

    if not note and not uploads:
        return HTMLResponse("<div class='alert alert-error text-sm'>Add a note or at least one photo/video.</div>")

    rows = []
    if note and not uploads:
        rows.append({
            "job_number": job_number,
            "engineer_contact_name": engineer.contact_name,
            "engineer_role": engineer_role,
            "note": note,
            "media_type": "Note"
        })

    for upload in uploads:
        safe_filename = re.sub(r"[^A-Za-z0-9_.-]+", "_", upload.filename or "evidence")
        filename = f"contribution_{job_number}_{datetime.now().timestamp()}_{safe_filename}"
        storage_path = f"reports/{job_number}/contributions/{filename}"
        file_content = await upload.read()
        media_url = supabase_storage.upload_file(file_content, storage_path)
        rows.append({
            "job_number": job_number,
            "engineer_contact_name": engineer.contact_name,
            "engineer_role": engineer_role,
            "note": note,
            "media_path": media_url,
            "media_type": upload.content_type or "Evidence",
            "original_filename": upload.filename
        })

    try:
        supabase.table("job_contributions").insert(rows).execute()
    except Exception as exc:
        return HTMLResponse(f"<div class='alert alert-error text-sm'>Could not save contribution: {html.escape(str(exc))}</div>")

    count_label = f"{len(rows)} contribution{'s' if len(rows) != 1 else ''}"
    return HTMLResponse(
        "<div class='alert alert-success text-sm font-bold'>"
        f"Saved {count_label} for {html.escape(engineer.contact_name)}."
        "</div>"
    )

@router.post("/extraction-report")
async def submit_extraction_report(request: Request, user: models.User = Depends(get_current_user)):
    try:
        form_data = await request.form()
        report_jn = form_data.get("job_number")
        job_type = form_data.get("job_type") or "Extraction"
        portal_token = form_data.get("portal_token")
        engineer = _get_engineer_by_token(portal_token)
        if not user and not engineer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if engineer and not _engineer_can_access_job(engineer, report_jn):
            raise HTTPException(status_code=403, detail="This job is not assigned to this engineer")
        engineer_role = _get_engineer_role_for_job(engineer, report_jn) if engineer else None
        if engineer and engineer_role != "Lead":
            return HTMLResponse(
                "<div class='alert alert-error font-bold'>Only the lead engineer can submit the final report. "
                "Your photos and notes should be added in the Your Job Evidence panel.</div>"
            )
        
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
            "job_type": job_type,
            "status": "Submitted",
            "risk_pre": int(form_data.get("risk_pre")) if form_data.get("risk_pre") else None,
            "risk_post": int(form_data.get("risk_post")) if form_data.get("risk_post") else None,
            "cleaning_interval_current": form_data.get("cleaning_interval_current"),
            "cleaning_interval_recommended": form_data.get("cleaning_interval_recommended"),
            "remedial_requirements": form_data.get("remedial_requirements"),
            "risk_improvements": form_data.get("risk_improvements"),
            "issue_description": form_data.get("issue_description"),
            "work_done": form_data.get("work_done"),
            "recommendations": form_data.get("recommendations"),
            "sketch_photo_path": sketch_photo_url,
            "photos_taken": form_data.get("photos_taken"),
            "client_signature": form_data.get("client_signature"),
            "engineer_signature": form_data.get("engineer_signature")
        }
        if job_type == "Breakdown/Callout":
            report_data["remedial_requirements"] = report_data.get("remedial_requirements") or form_data.get("issue_description")
            report_data["risk_improvements"] = report_data.get("risk_improvements") or form_data.get("recommendations")
            work_done_text = (form_data.get("work_done") or "").strip()
            if work_done_text:
                report_data["sketch_details"] = f"[CALL OUT]\nWork done:\n{work_done_text}"
            else:
                report_data["sketch_details"] = "[CALL OUT]"
        
        res = _insert_with_schema_fallback("extraction_reports", report_data)
        report_id = res.data[0]['id']
        
        if job_type == "Extraction":
            # Microns
            m_locations = form_data.getlist("micron_location[]")
            m_descs = form_data.getlist("micron_desc[]")
            m_pres = form_data.getlist("micron_pre[]")
            m_posts = form_data.getlist("micron_post[]")
            readings = []
            for i in range(len(m_descs)):
                if m_pres[i] or m_posts[i]:
                    location = (m_locations[i] if i < len(m_locations) else f"T{i+1}") or f"T{i+1}"
                    readings.append({
                        "report_id": report_id,
                        "location": location,
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

        # Photos and videos
        photos = await _build_media_entries(report_id, form_data, report_jn)
        if photos:
            supabase.table("extraction_photos").insert(photos).execute()

        _notify_report_submitted_async(report_data, report_id, request.url.netloc)

        redirect_url = f"/portal/{portal_token}" if portal_token else "/engineer-diary"
        return HTMLResponse(content=(
            "<div class='alert alert-success font-bold'>Report submitted successfully. Returning to your portal...</div>"
            f"<script>setTimeout(() => {{ window.location.href = {json.dumps(redirect_url)}; }}, 1400);</script>"
        ))
    except HTTPException:
        raise
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
    contributions = _get_job_contributions(report.job_number)
    
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
        "contributions": contributions,
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

    _update_with_schema_fallback("extraction_reports", update_data, "id", report_id)
    
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

@router.get("/admin/reports/{report_id}/download")
def download_admin_report_pdf(report_id: int, user: models.User = Depends(login_required)):
    res = supabase.table("extraction_reports").select("*").eq("id", report_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        report = models.ExtractionReport(**res.data[0])
    except Exception:
        fallback = dict(res.data[0])
        fallback["date"] = None
        fallback["time"] = None
        report = models.ExtractionReport(**fallback)
        
    micron_readings = [models.ExtractionMicronReading(**m) for m in supabase.table("extraction_micron_readings").select("*").eq("report_id", report_id).execute().data]
    inspection_items = [models.ExtractionInspectionItem(**i) for i in supabase.table("extraction_inspection_items").select("*").eq("report_id", report_id).execute().data]
    filter_items = [models.ExtractionFilterItem(**f) for f in supabase.table("extraction_filter_items").select("*").eq("report_id", report_id).execute().data]
    photos = [models.ExtractionPhoto(**p) for p in supabase.table("extraction_photos").select("*").eq("report_id", report_id).execute().data]
    
    tmp_dir = tempfile.gettempdir()
    jn = report.job_number or str(report_id)
    safe_jn = jn.replace('/', '_').replace('\\', '_')
    pdf_path = os.path.join(tmp_dir, f"PNJ_Report_{safe_jn}.pdf")
    
    from ...report_generator import generate_client_pdf
    generate_client_pdf(report, micron_readings, inspection_items, filter_items, photos, pdf_path)
    
    return FileResponse(pdf_path, filename=f"PNJ_Report_{safe_jn}.pdf", media_type="application/pdf")



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
