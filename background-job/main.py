from fastapi import FastAPI

app = FastAPI(
    title="A3 Background Job API",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}