from fastapi import FastAPI

from app.api.discovery import router as discovery_router
from app.api.universities import router as universities_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.include_router(discovery_router, prefix=settings.API_PREFIX)
app.include_router(universities_router, prefix=settings.API_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
