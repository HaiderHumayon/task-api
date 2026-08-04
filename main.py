from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A simple in-memory CRUD API for creating, reading, updating, and deleting tasks.",
)


class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


tasks = [
    {"id": 1, "title": "Learn HTTP", "done": False},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Test with Swagger UI", "done": True},
]


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
    return tasks


@app.get("/tasks/{task_id}", summary="Get one task by ID")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task_data: TaskCreate):
    if task_data.title is None or not task_data.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"},
        )

    next_id = max((task["id"] for task in tasks), default=0) + 1

    new_task = {
        "id": next_id,
        "title": task_data.title.strip(),
        "done": False,
    }

    tasks.append(new_task)

    return new_task


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

    for task in tasks:
        if task["id"] == task_id:
            if "title" in provided_fields:
                task["title"] = task_data.title.strip()

            if "done" in provided_fields:
                task["done"] = task_data.done

            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
)
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return Response(status_code=204)

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )