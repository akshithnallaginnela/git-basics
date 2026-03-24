from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.database import engine, Base

# All models must be imported before create_all
from backend.models import user, health_record, health_analytics, task, blood_report  # noqa: F401

from backend.routers import auth, dashboard, vitals, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VitalID API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(vitals.router)
app.include_router(reports.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
