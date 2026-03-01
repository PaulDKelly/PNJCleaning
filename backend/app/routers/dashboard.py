from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from .. import models
from ..supabase_client import supabase
from ..dependencies import templates, login_required

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
@router.post("/", response_class=HTMLResponse)
def read_root(request: Request, user: models.User = Depends(login_required)):
    print(f"DEBUG: read_root hit with method {request.method}")
    try:
        # Existing logic...
        # 1. Summary stats
        total_jobs = supabase.table("jobs").select("*", count="exact", head=True).execute().count
        active_engineers = supabase.table("engineers").select("*", count="exact", head=True).execute().count
        total_clients = supabase.table("clients").select("*", count="exact", head=True).execute().count
        
        # 2. Recent jobs
        recent_jobs_res = supabase.table("jobs").select("*").order("date", desc=True).limit(20).execute()
        recent_jobs = [models.Job(**j) for j in recent_jobs_res.data]
        
        # 3. All Recent Jobs for "Operation History"
        all_jobs_res = supabase.table("jobs").select("*").order("date", desc=True).limit(10).execute()
        all_jobs = [models.Job(**j) for j in all_jobs_res.data]
        
        # 4. Archived Clients
        archived_clients_res = supabase.table("clients").select("*").eq("archived", True).execute()
        archived_clients = [models.Client(**c) for c in archived_clients_res.data]
        
        # 5. Archived Sites
        archived_sites_res = supabase.table("client_sites").select("*").eq("archived", True).execute()
        archived_sites = [models.ClientSite(**s) for s in archived_sites_res.data]
        
        # 6. Engineers
        engineers_res = supabase.table("engineers").select("*").execute()
        engineers = [models.Engineer(**e) for e in engineers_res.data]
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "user": user,
            "stats": {
                "total_jobs": total_jobs,
                "active_engineers": active_engineers,
                "total_clients": total_clients
            },
            "recent_jobs": recent_jobs,
            "all_jobs": all_jobs,
            "archived_clients": archived_clients,
            "archived_sites": archived_sites,
            "engineers": engineers
        })
    except Exception as e:
        import traceback
        return HTMLResponse(content=f"<h3>Internal Server Error</h3><pre>{traceback.format_exc()}</pre>", status_code=500)
