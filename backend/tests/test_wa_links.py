import urllib.parse
import os

class MockJob:
    def __init__(self, job_number, client_name, site_name, address, date, time, priority, notes):
        self.job_number = job_number
        self.client_name = client_name
        self.site_name = site_name
        self.address = address
        self.date = date
        self.time = time
        self.priority = priority
        self.notes = notes

class MockEngineer:
    def __init__(self, phone, contact_name, access_token):
        self.phone = phone
        self.contact_name = contact_name
        self.access_token = access_token

def generate_whatsapp_link(job, engineer, host):
    if not engineer or not engineer.phone:
        return None
    
    # Determine base URL (Cloud env var or local request host)
    base_url = os.getenv("PUBLIC_URL")
    if not base_url:
        protocol = "https" if "." in host and not host.startswith("localhost") and not host.startswith("127.0.0.1") else "http"
        base_url = f"{protocol}://{host}"
    
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
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

# Test cases
from datetime import datetime
mock_job = MockJob("JOB123", "Test Client", "Test Site", "123 Test St", datetime.now(), datetime.now(), "High", "Test notes")
mock_eng = MockEngineer("07123456789", "John Doe", "token123")

print("--- Local Test (localhost) ---")
link_local = generate_whatsapp_link(mock_job, mock_eng, "localhost:8000")
print(f"Local Link: {link_local}")
assert "http://localhost:8000/portal/token123" in urllib.parse.unquote(link_local)

print("\n--- Cloud Test (pnj-cleaning.azurewebsites.net) ---")
link_cloud = generate_whatsapp_link(mock_job, mock_eng, "pnj-cleaning.azurewebsites.net")
print(f"Cloud Link: {link_cloud}")
assert "https://pnj-cleaning.azurewebsites.net/portal/token123" in urllib.parse.unquote(link_cloud)

print("\n--- PUBLIC_URL Override Test ---")
os.environ["PUBLIC_URL"] = "https://custom.domain.com"
link_override = generate_whatsapp_link(mock_job, mock_eng, "localhost:8000")
print(f"Override Link: {link_override}")
assert "https://custom.domain.com/portal/token123" in urllib.parse.unquote(link_override)

print("\nAll tests passed!")
