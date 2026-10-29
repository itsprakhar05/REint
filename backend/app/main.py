from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analytics import router as analytics_router

app = FastAPI(title="REint API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


app.include_router(
    analytics_router,
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
