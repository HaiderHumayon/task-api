# Task API

A simple in-memory CRUD API built with Python and FastAPI.

The API allows users to create, read, update, and delete to-do tasks. It includes input validation, appropriate HTTP status codes, JSON error responses, and interactive Swagger UI documentation.

## Features

- Create a task
- List all tasks
- Retrieve one task by ID
- Update an existing task
- Delete a task
- Validate missing or empty titles
- Return appropriate HTTP status codes
- Test endpoints through Swagger UI
- Store tasks temporarily in memory

## Technologies

- Python 3.10 or newer
- FastAPI
- Uvicorn
- Pydantic
- Git and GitHub

## Project Structure

```text
task-api/
|-- main.py
|-- requirements.txt
|-- README.md
|-- .gitignore
`-- screenshots/
    `-- swagger-ui.png
```

## Installation

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run the API

```powershell
python -m uvicorn main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

## Endpoints

| Method | Endpoint | Description | Success status |
|---|---|---|---|
| GET | `/` | Show API information | `200 OK` |
| GET | `/health` | Check whether the API is running | `200 OK` |
| GET | `/tasks` | List all tasks | `200 OK` |
| GET | `/tasks/{task_id}` | Retrieve one task by ID | `200 OK` |
| POST | `/tasks` | Create a new task | `201 Created` |
| PUT | `/tasks/{task_id}` | Update an existing task | `200 OK` |
| DELETE | `/tasks/{task_id}` | Delete a task | `204 No Content` |

## Task Format

```json
{
  "id": 1,
  "title": "Learn HTTP",
  "done": false
}
```

## Example Request and Response

Command:

```powershell
curl.exe -i http://localhost:8000/health
```

Output:

```http
HTTP/1.1 200 OK
date: Tue, 04 Aug 2026 16:05:31 GMT
server: uvicorn
content-length: 15
content-type: application/json

{"status":"ok"}
```

## Status Codes

| Status code | Meaning |
|---|---|
| `200 OK` | A read or update succeeded |
| `201 Created` | A new task was created |
| `204 No Content` | A task was deleted successfully |
| `400 Bad Request` | The request body was missing or invalid |
| `404 Not Found` | The requested task does not exist |

## Swagger UI

The complete CRUD cycle can be tested through Swagger UI at `/docs`.

![Swagger UI](screenshots/swagger-ui.png)

## In-Memory Storage

Tasks are stored in a Python list while the server is running.

Tasks created, updated, or deleted during use are lost when the server restarts. After a restart, the original three example tasks are restored. Permanent storage would require a database.
