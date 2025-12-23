import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# load environment
load_dotenv("../.env")

# Import routers
from routers import upload, attendance, marks, student, result, course


app = FastAPI(title="Student Analytics API")

# -----------------------------
# ❗ CRITICAL: ENABLE CORS
# -----------------------------
# This allows your HTML frontend (running on file:// or localhost) 
# to talk to this API server.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload.router)
app.include_router(attendance.router)
app.include_router(marks.router)
app.include_router(student.router)
app.include_router(result.router)
app.include_router(course.router)

@app.get("/")
def root():
    return {"ok": True, "msg": "Student Analytics API running with CORS enabled"}

# Run command:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000