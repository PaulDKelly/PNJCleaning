import urllib.parse
import os
from . import models


def _is_local_host(host: str) -> bool:
    host = (host or "").split(":", 1)[0].lower()
    return host in {"localhost", "127.0.0.1", "0.0.0.0"}


def _get_request_base_url(host: str) -> str:
    """Resolve the base URL for the current request host."""
    protocol = "http" if _is_local_host(host) else "https"
    return f"{protocol}://{host}".rstrip("/")


def _get_public_base_url(host: str) -> str:
    """Resolve the externally reachable base URL for engineer/customer links."""
    if _is_local_host(host):
        base_url = os.getenv("PUBLIC_URL")
        if base_url:
            return base_url.rstrip("/")

    base_url = os.getenv("PUBLIC_URL")
    if not base_url:
        redirect_uri = os.getenv("WORKOS_REDIRECT_URI")
        if redirect_uri:
            parsed = urllib.parse.urlparse(redirect_uri)
            if parsed.scheme and parsed.netloc:
                base_url = f"{parsed.scheme}://{parsed.netloc}"
    if not base_url:
        base_url = _get_request_base_url(host)
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


def _get_google_maps_link(address: str) -> str:
    """Return a Google Maps search link for a known address."""
    normalized_address = (address or "").strip()
    if not normalized_address:
        return ""
    encoded_address = urllib.parse.quote(normalized_address)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_address}"


def get_report_link(job: models.Job, host: str, public: bool = False) -> str:
    """Return the correct blank report URL for the job type."""
    base_url = _get_public_base_url(host) if public else _get_request_base_url(host)
    job_type = (getattr(job, "job_type", "") or "").strip()
    if job_type == "Breakdown/Callout":
        return f"{base_url}/extraction-report?job_number={job.job_number}&job_type={job_type}"
    return f"{base_url}/extraction-report?job_number={job.job_number}"

def generate_whatsapp_link(job: models.Job, engineer: models.Engineer, host: str):
    """Return WhatsApp web URL for job dispatch."""
    if not engineer or not engineer.phone:
        return None

    base_url = _get_public_base_url(host)
    report_link = get_report_link(job, host, public=True)
    queue_link = f"{base_url}/portal/{engineer.access_token}" if engineer.access_token else f"{base_url}/portal/login"
    maps_link = _get_google_maps_link(job.address)
    is_callout = (getattr(job, "job_type", "") or "").strip().lower() == "breakdown/callout"
    report_label = "Breakdown / Callout Report" if is_callout else "Post-Service Extraction Report"
    maps_section = f"Google Maps:\n{maps_link}\n\n" if maps_link else ""

    msg = (
        f"PNJ Extraction - New Job Assigned\n\n"
        f"Job: {job.job_number}\n"
        f"Client: {job.client_name}\n"
        f"Site: {job.site_name or 'N/A'}\n"
        f"Address: {job.address or 'N/A'}\n\n"
        f"{maps_section}"
        f"{report_label}:\n{report_link}\n\n"
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
