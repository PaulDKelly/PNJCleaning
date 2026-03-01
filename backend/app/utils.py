import urllib.parse
import os
from . import models


def _get_base_url(host: str) -> str:
    """Resolve public base URL with optional PUBLIC_URL override."""
    base_url = os.getenv("PUBLIC_URL")
    if not base_url:
        protocol = "https" if "." in host and not host.startswith("localhost") and not host.startswith("127.0.0.1") else "http"
        base_url = f"{protocol}://{host}"
    return base_url.rstrip("/")


def _normalize_uk_phone(phone: str) -> str:
    """Convert UK numbers to WhatsApp international format without '+' (44...)."""
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("44"):
        return digits
    if digits.startswith("0"):
        return "44" + digits[1:]
    return "44" + digits

def generate_whatsapp_link(job: models.Job, engineer: models.Engineer, host: str):
    """Return WhatsApp web URL for job dispatch."""
    if not engineer or not engineer.phone:
        return None

    base_url = _get_base_url(host)
    report_link = f"{base_url}/extraction-report?job_number={job.job_number}"
    queue_link = f"{base_url}/portal/{engineer.access_token}" if engineer.access_token else f"{base_url}/portal/login"

    msg = (
        f"PNJ Extraction - New Job Assigned\n\n"
        f"Job: {job.job_number}\n"
        f"Client: {job.client_name}\n"
        f"Site: {job.site_name or 'N/A'}\n"
        f"Address: {job.address or 'N/A'}\n\n"
        f"Post-Service Extraction Report:\n{report_link}\n\n"
        f"Your Job Queue & Portal:\n{queue_link}"
    )

    encoded_msg = urllib.parse.quote(msg)
    phone = _normalize_uk_phone(engineer.phone)
    if not phone:
        return None
    return f"https://wa.me/{phone}?text={encoded_msg}"


def generate_whatsapp_app_link(job: models.Job, engineer: models.Engineer, host: str):
    """Return WhatsApp app deep-link URL (whatsapp://send)."""
    web = generate_whatsapp_link(job, engineer, host)
    if not web:
        return None
    if "/wa.me/" not in web:
        return None
    phone = web.split("/wa.me/", 1)[1].split("?", 1)[0]
    if not phone:
        return None
    text = web.split("text=", 1)[1] if "text=" in web else ""
    return f"whatsapp://send?phone={phone}&text={text}"
