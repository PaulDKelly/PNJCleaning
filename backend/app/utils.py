import urllib.parse
from . import models

def generate_whatsapp_link(job: models.Job, engineer: models.Engineer, host: str):
    """WhatsApp message generation helper"""
    # Use the provided host (e.g., localhost:8000 or production URL)
    base_url = f"https://{host}" if "localhost" not in host else f"http://{host}"
    
    # Reports link
    report_link = f"{base_url}/extraction-report/{job.job_number}"
    # Queue link
    queue_link = f"{base_url}/portal/{engineer.access_token}"
    
    msg = (
        f"PNJ Extraction - New Job Assigned\n\n"
        f"Job: {job.job_number}\n"
        f"Client: {job.client_name}\n"
        f"Site: {job.site_name}\n"
        f"Address: {job.address}\n\n"
        f"Post-Service Extraction Report:\n{report_link}\n\n"
        f"Your Job Queue & Portal:\n{queue_link}"
    )
    encoded_msg = urllib.parse.quote(msg)
    return f"https://wa.me/{engineer.phone}?text={encoded_msg}"
