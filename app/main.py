from fastapi import FastAPI

app = FastAPI(title="Computer-Use Automation")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
