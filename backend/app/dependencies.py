from fastapi import Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from jose import jwt
import os
from urllib.parse import quote
from . import models, security
from .supabase_client import supabase

# Centralized templates instance for use in routers
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
templates.env.filters["quote_path"] = lambda value: quote(str(value or ""), safe="")

# Helper to get user by email using Supabase
def get_user_by_email(email: str):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data:
        return models.User(**res.data[0])
    return None

def get_user_by_username(username: str):
    res = supabase.table("users").select("*").eq("username", username).execute()
    if res.data:
        return models.User(**res.data[0])
    return None

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return get_user_by_email(email)
    except Exception:
        return None

def login_required(user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def role_required(allowed_roles: list):
    def dependency(user: models.User = Depends(login_required)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return dependency
