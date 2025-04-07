from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import uuid
import threading
from main import generate_video_from_json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store job status
jobs = {}

class GenerationRequest(BaseModel):
    contact_name: str
    contact_gender: str
    your_gender: str
    convo: list

@app.get("/")
async def read_root():
    return {"status": "ok"}

@app.post("/generate")
async def generate(data: GenerationRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'video_path': None,
        'error': None
    }

    def generate_video_task():
        try:
            output_path = generate_video_from_json(data.dict(), job_id=job_id)
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['video_path'] = output_path
        except Exception as e:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = str(e)

    thread = threading.Thread(target=generate_video_task)
    thread.daemon = True
    thread.start()

    return {"job_id": job_id}

@app.get("/status/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/download/{job_id}")
async def download(job_id: str):
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        raise HTTPException(status_code=404, detail="Video not ready")
    
    video_path = jobs[job_id]['video_path']
    return FileResponse(
        path=video_path,
        filename=f"chat_video_{job_id}.mp4",
        media_type="video/mp4"
    ) 