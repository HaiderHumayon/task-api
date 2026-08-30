from fastapi import FastAPI, Header, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase_auth.errors import AuthApiError

from supabase_client import supabase

from repository import (
    create_task as repository_create_task,
    delete_task as repository_delete_task,
    get_task as repository_get_task,
    get_tasks as repository_get_tasks,
    initialize_database,
    update_task as repository_update_task,
)


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A CRUD API with PostgreSQL and Supabase authentication.",
)


initialize_database()


class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class AuthCredentials(BaseModel):
    email: str | None = None
    password: str | None = None


def missing_credentials(credentials: AuthCredentials) -> bool:
    return (
        credentials.email is None
        or not credentials.email.strip()
        or credentials.password is None
        or not credentials.password.strip()
    )


@app.get("/", summary="Show API information")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Check API health")
def health_check():
    return {"status": "ok"}


@app.post("/auth/signup", status_code=201, summary="Create a user account")
def signup(credentials: AuthCredentials):
    if missing_credentials(credentials):
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})
    try:
        response = supabase.auth.sign_up({"email": credentials.email.strip(), "password": credentials.password})
    except AuthApiError as exc:
        return JSONResponse(status_code=400, content={"error": exc.message})
    return JSONResponse(status_code=201, content={"user": jsonable_encoder(response.user)})


@app.post("/auth/login", summary="Log in and receive tokens")
def login(credentials: AuthCredentials):
    if missing_credentials(credentials):
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})
    try:
        response = supabase.auth.sign_in_with_password({"email": credentials.email.strip(), "password": credentials.password})
    except AuthApiError:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})
    if response.session is None:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})
    return {"access_token": response.session.access_token, "refresh_token": response.session.refresh_token}


@app.get("/public/info", summary="Read public information")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", summary="Read a protected profile")
def protected_profile(authorization: str | None = Header(default=None)):
    if not authorization:
        return JSONResponse(status_code=401, content={"error": "Access token required"})
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        return JSONResponse(status_code=401, content={"error": "Access token required"})
    try:
        response = supabase.auth.get_user(token.strip())
    except AuthApiError:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})
    if response.user is None:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})
    user = response.user
    return {"id": str(user.id), "email": user.email, "created_at": jsonable_encoder(user.created_at)}


@app.get("/tasks", summary="List all tasks")
def get_tasks():
    return repository_get_tasks()


@app.get("/tasks/{task_id}", summary="Get one task by ID")
def get_task(task_id: int):
    task = repository_get_task(task_id)

    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )

    return task


@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task_data: TaskCreate):
    if task_data.title is None or not task_data.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"},
        )

    return repository_create_task(task_data.title.strip())


@app.put("/tasks/{task_id}", summary="Update an existing task")
def update_task(task_id: int, task_data: TaskUpdate):
    provided_fields = task_data.model_fields_set

    if not provided_fields:
        return JSONResponse(
            status_code=400,
            content={"error": "Provide title, done, or both"},
        )

    if "title" in provided_fields:
        if task_data.title is None or not task_data.title.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Title cannot be empty"},
            )

    if "done" in provided_fields and task_data.done is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Done must be true or false"},
        )

    existing_task = repository_get_task(task_id)

    if existing_task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )

    new_title = existing_task["title"]
    new_done = existing_task["done"]

    if "title" in provided_fields:
        new_title = task_data.title.strip()

    if "done" in provided_fields:
        new_done = task_data.done

    updated_task = repository_update_task(
        task_id,
        new_title,
        new_done,
    )

    return updated_task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
)
def delete_task(task_id: int):
    deleted = repository_delete_task(task_id)

    if not deleted:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )

    return Response(status_code=204)
