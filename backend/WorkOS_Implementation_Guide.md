# Complete WorkOS SSO Implementation Guide

This document is the "all-in-one" reference for the PNJ Cleaning WorkOS integration, covering the journey from initial scaffolding to the final production-ready state.

## 1. Environment & Project Setup

### WorkOS Project Alignment
Ensure the application identifies with the "DevTest" project.

- **WORKOS_API_KEY**: Must be clean of trailing characters (no commas/spaces).
- **WORKOS_CLIENT_ID**: Correct ID for the environment.
- **WORKOS_REDIRECT_URI**: Must exactly match the whitelist in the WorkOS dashboard (e.g., `https://.../auth/callback`).

### Azure Deployment (ACA) Variables
All keys must be mapped to the **Azure Container App environment variables** for the live site to function.

---

## 2. Backend Implementation ([auth.py](file:///e:/Code/Projects/PNJCleaning/backend/app/routers/auth.py))

### Initiation Flow
We use a two-step lookup to ensure the correct connection is used based on the user's domain.

```python
# auth_workos (POST)
domain = email.split('@')[-1]
connections = wos.sso.list_connections(domain=domain)
connection_id = connections.data[0].id

authorization_url = wos.sso.get_authorization_url(
    connection_id=connection_id, # Must use id, not the object
    redirect_uri=workos_redirect_uri,
    state="workos_auth", # Must be a string (v4+)
)
```

### Callback & Profile Handling
The modern SDK returns Pydantic-based objects. Attributes are accessed directly.

```python
# auth_callback (GET)
profile_and_token = wos.sso.get_profile_and_token(code)
profile = profile_and_token.profile
email = profile.email # Direct access
```

---

## 3. Auto-Provisioning & Database Logic

To ensure users can log in without prior manual account creation, the app auto-provisions them. We implemented a "Unique Username" safeguard to prevent crashes if a name is already taken.

```python
# Provisioning Logic
username = f"{profile.first_name} {profile.last_name}".strip()

# Collision Fix: If name exists, fallback to email
if get_user_by_username(username):
    username = email

supabase.table("users").insert({
    "username": username,
    "email": email,
    "password": security.get_password_hash(str(uuid.uuid4())),
    "role": "Admin"
}).execute()
```

---

## 4. Operational Calendar Fix ([dashboard.py](file:///e:/Code/Projects/PNJCleaning/backend/app/routers/dashboard.py))

The main landing page after SSO login was initially broken due to a template mismatch.

- **The Fix**: Changed `dashboard.html` back to `index.html` in the router since `index.html` is the actual file containing the Manager's Operational Calendar and Stats.

---

## 5. Summary of Key Fixes

| Stage | Error Encountered | Resolution |
| :--- | :--- | :--- |
| **Connection** | `401 Unauthorized` | Removed trailing comma from `WORKOS_API_KEY`. |
| **Handshake** | `AuthenticationException` | Updated SDK params to `connection_id` and string `state`. |
| **Provisioning** | `Duplicate Key Exception` | Added unique username check (checks `users` table). |
| **Post-Login** | `TemplateNotFound` | Corrected `dashboard.py` to render `index.html`. |

---

### Final Verification Status: **ONLINE** 🟢
The system is now fully synced between **WorkOS (DevTest)**, **Azure (ACA)**, and the **Supabase Database**.
