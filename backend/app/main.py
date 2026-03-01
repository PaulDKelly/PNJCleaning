from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from .routers import auth, scheduler, crm, portal, admin, dashboard, dynamic_reports
from .module_loader import load_modules

# Initialize FastAPI App
app = FastAPI(title="Web App Builder")

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"REQUEST: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"RESPONSE: {response.status_code}")
    return response

from fastapi.responses import RedirectResponse
from fastapi import HTTPException

@app.exception_handler(401)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    if request.url.path == "/login":
        return await request.app.default_exception_handler(request, exc)
    return RedirectResponse(url="/login")

# Versioning and logging
print("WEB_APP_BUILDER_ENGINE: v1.0.0-modular", flush=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Core Engine Routers (Order matters for root routes)
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(auth.router, tags=["Authentication"])
app.include_router(scheduler.router, tags=["Scheduler"])
app.include_router(crm.router, tags=["CRM"])
app.include_router(portal.router, tags=["Portal"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(dynamic_reports.router, tags=["Dynamic Reports"])

# Load Domain Modules Dynamically (e.g., Extraction Report)
load_modules(app)
