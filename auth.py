from fastapi import Header
from supabase_auth.errors import AuthApiError
from supabase_client import supabase

class AuthenticationError(Exception):
    def __init__(self, message:str): self.message=message

def get_current_user(authorization:str|None=Header(default=None)):
    if not authorization: raise AuthenticationError("Access token required")
    scheme, separator, token=authorization.partition(" ")
    if not separator or scheme.lower()!="bearer" or not token.strip(): raise AuthenticationError("Access token required")
    try: response=supabase.auth.get_user(token.strip())
    except AuthApiError: raise AuthenticationError("Invalid or expired token")
    if response.user is None: raise AuthenticationError("Invalid or expired token")
    return response.user
