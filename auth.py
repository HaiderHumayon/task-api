from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.errors import AuthApiError
from supabase_client import supabase

security=HTTPBearer(auto_error=False)

class AuthenticationError(Exception):
    def __init__(self, message:str): self.message=message

def get_current_user(credentials:HTTPAuthorizationCredentials|None=Depends(security)):
    if credentials is None or not credentials.credentials.strip(): raise AuthenticationError("Access token required")
    token=credentials.credentials.strip()
    try: response=supabase.auth.get_user(token)
    except AuthApiError: raise AuthenticationError("Invalid or expired token")
    if response.user is None: raise AuthenticationError("Invalid or expired token")
    return response.user
