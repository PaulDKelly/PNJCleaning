import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import models, security
from ..supabase_client import supabase
from ..dependencies import templates, get_user_by_email, get_user_by_username, get_current_user

router = APIRouter()

# --- WorkOS SSO Integration ---

# Initialize WorkOS
workos_api_key = os.getenv("WORKOS_API_KEY")
workos_client_id = os.getenv("WORKOS_CLIENT_ID")
workos_redirect_uri = os.getenv("WORKOS_REDIRECT_URI")

from workos import WorkOSClient
wos = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: models.User = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("login.html", {"request": request, "user": user})

@router.get("/auth/workos")
async def auth_workos_get():
    """Handle accidental GET requests to SSO initiation"""
    return RedirectResponse(url="/login?error=Invalid+Request+Method")

@router.post("/auth/workos")
async def auth_workos(email: str = Form(...)):
    """Initiate WorkOS SSO flow with robust connection lookup"""
    try:
        domain = email.split('@')[-1]
        print(f"DEBUG: SSO lookup for domain '{domain}'")
        
        connections = wos.sso.list_connections(domain=domain)
        if not connections.data:
            print(f"DEBUG: No connection found for domain '{domain}'")
            return RedirectResponse(url=f"/login?error=unknown_domain&domain={domain}", status_code=303)
        
        connection_id = connections.data[0].id
        print(f"DEBUG: Found connection {connection_id}. Redirecting...")
        
        authorization_url = wos.sso.get_authorization_url(
            connection_id=connection_id,
            redirect_uri=workos_redirect_uri,
            state="workos_auth",  # state must be a string in v4+
        )
        return RedirectResponse(url=authorization_url, status_code=303)
    except Exception as e:
        import traceback
        print(f"WorkOS Auth Error: {e}")
        traceback.print_exc()
        return RedirectResponse(url="/login?error=sso_failed", status_code=303)

@router.get("/auth/google")
async def auth_google_get():
    """Handle accidental GET requests to Google SSO initiation"""
    return RedirectResponse(url="/login?error=Invalid+Request+Method")

@router.post("/auth/google")
async def auth_google():
    """Initiate Google Social Login flow via WorkOS"""
    try:
        authorization_url = wos.sso.get_authorization_url(
            provider='GoogleOAuth',
            redirect_uri=workos_redirect_uri,
            state="google_auth",
        )
        return RedirectResponse(url=authorization_url, status_code=303)
    except Exception as e:
        import traceback
        print(f"WorkOS Google Auth Error: {e}")
        traceback.print_exc()
        return RedirectResponse(url="/login?error=sso_failed", status_code=303)

@router.get("/auth/callback")
async def auth_callback(request: Request, code: str):
    """Handle WorkOS callback and auto-provision users"""
    try:
        print(f"DEBUG: auth_callback received code: {code[:10]}...")
        profile_and_token = wos.sso.get_profile_and_token(code)
        print(f"DEBUG: Profile exchange successful")
        
        profile = profile_and_token.profile
        email = profile.email
        print(f"DEBUG: Authenticated email: {email}")
        
        if not email:
            print("ERROR: No email in WorkOS profile")
            return RedirectResponse(url="/login?error=no_email")
            
        user = get_user_by_email(email)
        
        if not user:
            print(f"DEBUG: User {email} not found. Provisioning...")
            # AUTO-PROVISION
            first_name = profile.first_name or ""
            last_name = profile.last_name or ""
            username = f"{first_name} {last_name}".strip()
            if not username:
                username = email.split('@')[0]
                
            random_pw = str(uuid.uuid4())
            hashed_pw = security.get_password_hash(random_pw)
            
            # Ensure username is unique
            if get_user_by_username(username):
                print(f"DEBUG: Username {username} taken, using email {email} instead")
                username = email
            
            print(f"DEBUG: Inserting user {email} as {username} into database")
            supabase.table("users").insert({
                "username": username,
                "email": email,
                "password": hashed_pw,
                "role": "Admin"
            }).execute()
            
            user = get_user_by_email(email)
            
        if not user:
            print("ERROR: Provisioning failed")
            return RedirectResponse(url="/login?error=provisioning_failed")

        print(f"DEBUG: Creating session for {user.email}")
        access_token = security.create_access_token(data={"sub": user.email})
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response
        
    except Exception as e:
        import traceback
        print(f"WorkOS Callback Error: {e}")
        traceback.print_exc()
        return RedirectResponse(url="/login?error=callback_failed")

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: Optional[str] = Form(None)
):
    if not password:
        return HTMLResponse(content="<div class='alert alert-error'>Password is required</div>", status_code=200)
    user = get_user_by_email(email)
    
    if not user:
        return HTMLResponse(content="<div class='alert alert-error'>User not found</div>", status_code=200)
        
    if not security.verify_password(password, user.password):
        return HTMLResponse(content="<div class='alert alert-error'>Invalid password</div>", status_code=200)
    
    access_token = security.create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/forgot-password")
async def handle_forgot_password(request: Request, email: str = Form(...)):
    user = get_user_by_email(email)
    if not user:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request, 
            "message": "If an account exists with that email, a reset link has been generated."
        })
    
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=1)
    
    supabase.table("users").update({
        "reset_token": token,
        "reset_expires": expires.isoformat()
    }).eq("email", email).execute()
    
    reset_link = f"{request.url.scheme}://{request.url.netloc}/reset-password/{token}"
    print(f"PASSWORD RESET LINK: {reset_link}")
    
    return templates.TemplateResponse("forgot_password.html", {
        "request": request, 
        "message": "A reset link has been generated and logged to the server console."
    })

@router.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
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

@router.post("/reset-password/{token}")
async def handle_reset_password(request: Request, token: str, password: str = Form(...)):
    res = supabase.table("users").select("*").eq("reset_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user_data = res.data[0]
    expires = datetime.fromisoformat(user_data['reset_expires'])
    if datetime.utcnow() > expires:
        raise HTTPException(status_code=400, detail="Expired token")
    
    hashed_password = security.get_password_hash(password)
    supabase.table("users").update({
        "password": hashed_password,
        "reset_token": None,
        "reset_expires": None
    }).eq("id", user_data['id']).execute()
    
    return RedirectResponse(url="/login?message=password_updated", status_code=303)

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response
