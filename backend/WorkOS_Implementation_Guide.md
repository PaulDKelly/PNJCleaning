# WorkOS SSO Implementation Guide

This document provides a comprehensive overview of how **WorkOS Single Sign-On (SSO)** was implemented, including the code changes for both Enterprise (SAML/OIDC) and Social (Google) authentication flows.

## 1. Environment Configuration

The integration relies on three primary environment variables. We identified that the `WORKOS_API_KEY` was "dirty" (contained a trailing comma), which was causing 401 Unauthorized errors. Cleaning this key was the first step to a stable integration.

**Required `.env` Variables:**
```env
WORKOS_API_KEY=sk_test_... (Ensure no trailing commas or extra characters)
WORKOS_CLIENT_ID=project_...
WORKOS_REDIRECT_URI=https://your-domain.com/auth/callback
```

---

## 2. Backend Implementation (`main.py`)

### SDK Initialization
We shifted from global module-level configuration to an explicit `WorkOSClient` instance for better management and reliability.

```python
from workos.client import WorkOSClient

workos_api_key = os.getenv("WORKOS_API_KEY")
workos_client_id = os.getenv("WORKOS_CLIENT_ID")
workos_redirect_uri = os.getenv("WORKOS_REDIRECT_URI")

# Explicit client instance
wos = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)
```

### Two-Step SSO Initiation
Because some WorkOS SDK versions have limitations with the direct `domain` parameter in `get_authorization_url`, we implemented a robust two-step lookup.

1.  **Search**: Find the specific connection ID associated with the user's email domain.
2.  **Initiate**: Use that `connection_id` to generate the login URL.

```python
@app.post("/auth/workos")
async def auth_workos(email: str = Form(...)):
    domain = email.split('@')[-1]
    
    # 1. Look up connection by domain
    connections = wos.sso.list_connections(domain=domain)
    if not connections.data:
        return RedirectResponse(url=f"/login?error=unknown_domain&domain={domain}", status_code=303)
    
    connection_id = connections.data[0].id
    
    # 2. Get URL using the explicit connection ID
    authorization_url = wos.sso.get_authorization_url(
        connection=connection_id,
        redirect_uri=workos_redirect_uri,
        state={},
    )
    return RedirectResponse(url=authorization_url, status_code=303)
```

### Google Social Login (for Personal Gmail)
To handle accounts without a dedicated Enterprise Identity Provider (like "SMTP-only" domains), we added a Social Login flow.

```python
@app.post("/auth/google")
async def auth_google():
    authorization_url = wos.sso.get_authorization_url(
        provider='GoogleOAuth', # Specifically targets Google Social Login
        redirect_uri=workos_redirect_uri,
        state={},
    )
    return RedirectResponse(url=authorization_url, status_code=303)
```

### Callback & Auto-Provisioning
The callback handler was fixed to handle the **Pydantic-based** objects returned by the modern WorkOS SDK (v4+), specifically accessing attributes directly rather than using `.to_dict()`.

```python
@app.get("/auth/callback")
async def auth_callback(request: Request, code: str):
    profile_and_token = wos.sso.get_profile_and_token(code)
    profile = profile_and_token.profile # Direct attribute access
    
    email = profile.email
    user = get_user_by_email(email)
    
    if not user:
        # AUTO-PROVISION logic
        first_name = profile.first_name or ""
        last_name = profile.last_name or ""
        username = f"{first_name} {last_name}".strip() or email.split('@')[0]
        
        # Create user with random password (SSO manages their actual auth)
        hashed_pw = security.get_password_hash(str(uuid.uuid4()))
        supabase.table("users").insert({
            "username": username,
            "email": email,
            "password": hashed_pw,
            "role": "Admin"
        }).execute()
        
        user = get_user_by_email(email)
        
    # Log user in and set cookie
    access_token = security.create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response
```

---

## 3. Frontend Implementation (`login.html`)

The login UI was updated to provide three clear paths: Standard Password, Enterprise SSO, and Google Social Login.

```html
<!-- Enterprise SSO Form -->
<form action="/auth/workos" method="POST">
    <input type="email" name="email" placeholder="you@company.com" required />
    <button type="submit">Continue with Enterprise SSO</button>
</form>

<!-- Social Login Button -->
<button type="submit" formaction="/auth/google">
    Sign in with Google (for Gmail)
</button>
```

---

## 4. Verification & Testing

1.  **Enterprise SSO**: Tested with `@pnjcleaning.co.uk` (verified domain lookup).
2.  **Social Login**: Verified using personal Gmail (automated provisioning).
3.  **Traceback Fix**: Resolved the `ProfileAndToken` attribute error to ensure the final redirect works flawlessly.

![Revision 39 Live](file:///C:/Users/pauld/.gemini/antigravity/brain/2127deb6-bbc5-4568-bc61-48e68e550d22/verify_revision_39_healthy.png)
