from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
