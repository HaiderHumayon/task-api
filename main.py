from fastapi import Depends, FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase_auth.errors import AuthApiError

from auth import AuthenticationError, get_current_user
from repository import (
    create_task as repository_create_task, delete_task as repository_delete_task,
    get_task as repository_get_task, get_tasks as repository_get_tasks,
    initialize_database, update_task as repository_update_task,
)
from supabase_client import supabase
from src.routes.enrich import router as enrich_router

app = FastAPI(title="Task API", version="1.0", description="A CRUD API with PostgreSQL and Supabase authentication.")
initialize_database()
app.include_router(enrich_router)

class TaskCreate(BaseModel):
    title: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

class AuthCredentials(BaseModel):
    email: str | None = None
    password: str | None = None

def missing_credentials(c: AuthCredentials) -> bool:
    return c.email is None or not c.email.strip() or c.password is None or not c.password.strip()

@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"error": exc.message})

@app.get("/", summary="Show API information")
def read_root():
    return {"name":"Task API","version":"1.0","endpoints":["/tasks","/auth/signup","/auth/login","/auth/logout","/public/info","/protected/profile","/protected/dashboard"]}

@app.get("/health", summary="Check API health")
def health_check(): return {"status":"ok"}

@app.post("/auth/signup", status_code=201, summary="Create a user account")
def signup(c: AuthCredentials):
    if missing_credentials(c): return JSONResponse(status_code=400, content={"error":"Email and password are required"})
    try: r=supabase.auth.sign_up({"email":c.email.strip(),"password":c.password})
    except AuthApiError as exc: return JSONResponse(status_code=400, content={"error":exc.message})
    return JSONResponse(status_code=201, content={"user":jsonable_encoder(r.user)})

@app.post("/auth/login", summary="Log in and receive tokens")
def login(c: AuthCredentials):
    if missing_credentials(c): return JSONResponse(status_code=400, content={"error":"Email and password are required"})
    try: r=supabase.auth.sign_in_with_password({"email":c.email.strip(),"password":c.password})
    except AuthApiError: return JSONResponse(status_code=401, content={"error":"Invalid login credentials"})
    if r.session is None: return JSONResponse(status_code=401, content={"error":"Invalid login credentials"})
    return {"access_token":r.session.access_token,"refresh_token":r.session.refresh_token}

@app.post("/auth/logout", status_code=204, summary="Log out")
def logout(current_user=Depends(get_current_user)):
    supabase.auth.sign_out()
    return Response(status_code=204)

@app.get("/public/info", summary="Read public information")
def public_info(): return {"message":"Welcome stranger! This info is public."}

@app.get("/protected/profile", summary="Read a protected profile")
def protected_profile(current_user=Depends(get_current_user)):
    return {"id":str(current_user.id),"email":current_user.email,"created_at":jsonable_encoder(current_user.created_at)}

@app.get("/protected/dashboard", summary="Read a protected dashboard")
def protected_dashboard(current_user=Depends(get_current_user)):
    return {"message":"Welcome to your protected dashboard.","user_id":str(current_user.id)}

@app.get("/tasks", summary="List all tasks")
def get_tasks(): return repository_get_tasks()

@app.get("/tasks/{task_id}", summary="Get one task by ID")
def get_task(task_id:int):
    task=repository_get_task(task_id)
    if task is None: return JSONResponse(status_code=404, content={"error":"Task not found"})
    return task

@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task_data:TaskCreate):
    if task_data.title is None or not task_data.title.strip(): return JSONResponse(status_code=400, content={"error":"Title is required"})
    return repository_create_task(task_data.title.strip())

@app.put("/tasks/{task_id}", summary="Update an existing task")
def update_task(task_id:int, task_data:TaskUpdate):
    fields=task_data.model_fields_set
    if not fields: return JSONResponse(status_code=400, content={"error":"Provide title, done, or both"})
    if "title" in fields and (task_data.title is None or not task_data.title.strip()): return JSONResponse(status_code=400, content={"error":"Title cannot be empty"})
    if "done" in fields and task_data.done is None: return JSONResponse(status_code=400, content={"error":"Done must be true or false"})
    existing=repository_get_task(task_id)
    if existing is None: return JSONResponse(status_code=404, content={"error":"Task not found"})
    title=task_data.title.strip() if "title" in fields else existing["title"]
    done=task_data.done if "done" in fields else existing["done"]
    return repository_update_task(task_id,title,done)

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id:int):
    if not repository_delete_task(task_id): return JSONResponse(status_code=404, content={"error":"Task not found"})
    return Response(status_code=204)
