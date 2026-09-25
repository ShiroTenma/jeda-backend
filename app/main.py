from fastapi import FastAPI

app = FastAPI(title="JEDA Backend", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "jeda-backend",
        "version": "0.1.0",
    }
