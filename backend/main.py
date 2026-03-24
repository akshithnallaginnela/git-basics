from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base

# Import all models so Base.metadata knows every table before create_all
from backend.models import user, health_record, health_analytics, task  # noqa: F401

from backend.routers import dashboard, vitals

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VitalID API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(vitals.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
