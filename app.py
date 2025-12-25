import os
import subprocess
import time
import shutil
import uuid
import redis
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from starlette.background import BackgroundTask

app = FastAPI()

# Render provides the REDIS_URL environment variable when you add the Redis add-on
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
r = redis.from_url(REDIS_URL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIC_DIR = os.path.join(BASE_DIR, "logic")
ENCODER = os.path.join(LOGIC_DIR, "encoder.exe")
DECODER = os.path.join(LOGIC_DIR, "decoder.exe")
ORIGINAL_IMG = os.path.join(LOGIC_DIR, "moan-a-lisa.png")

def cleanup_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            try: os.remove(path)
            except: pass

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.post("/hide")
async def hide_route(
    request: Request,
    message: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    temp_input = None
    if file and file.filename:
        temp_input = os.path.join(BASE_DIR, f"in_{int(time.time())}.png")
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        input_path = temp_input
    else:
        input_path = ORIGINAL_IMG

    output_name = f"out_{uuid.uuid4()}.png"
    output_path = os.path.join(BASE_DIR, output_name)

    # Run C++ Encoder
    res = subprocess.run([ENCODER, "-e", input_path, message, output_path], capture_output=True)

    if res.returncode == 0:
        # Read file into memory and store in Redis (expires in 24 hours)
        with open(output_path, "rb") as f:
            img_bytes = f.read()

        share_id = str(uuid.uuid4())
        r.setex(f"stego:{share_id}", 86400, img_bytes) # 24h expiry

        # Cleanup disk immediately
        cleanup_files(output_path)
        if temp_input: cleanup_files(temp_input)

        return {"share_url": f"{request.base_url}share/{share_id}"}

    if temp_input: cleanup_files(temp_input)
    raise HTTPException(status_code=500, detail="Encoding Failed")

@app.get("/share/{share_id}")
async def share_route(share_id: str):
    key = f"stego:{share_id}"
    img_data = r.get(key)

    if not img_data:
        return HTMLResponse("<h2>Link expired or already used!</h2>", status_code=404)

    # ONE-TIME USE: Delete from Redis immediately after retrieval
    r.delete(key)

    return Response(content=img_data, media_type="image/png")

@app.post("/extract")
async def extract_route(file: UploadFile = File(...)):
    temp_up = os.path.join(BASE_DIR, f"up_{int(time.time())}.png")
    with open(temp_up, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    res = subprocess.run([DECODER, "-d", temp_up], capture_output=True, text=True)
    cleanup_files(temp_up)

    if res.returncode == 0:
        return {"message": res.stdout.strip()}
    raise HTTPException(status_code=400, detail="Extraction Failed")
