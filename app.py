import os
import subprocess
import time
import shutil
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from starlette.background import BackgroundTask

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIC_DIR = os.path.join(BASE_DIR, "logic")
ENCODER = os.path.join(LOGIC_DIR, "encoder.exe")
DECODER = os.path.join(LOGIC_DIR, "decoder.exe")
ORIGINAL_IMG = os.path.join(LOGIC_DIR, "moan-a-lisa.png")

def cleanup_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.post("/hide")
async def hide_route(
    background_tasks: BackgroundTasks,
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

    output_name = f"out_{int(time.time())}.png"
    output_path = os.path.join(BASE_DIR, output_name)

    res = subprocess.run([ENCODER, "-e", input_path, message, output_path], capture_output=True)

    if temp_input:
        background_tasks.add_task(cleanup_files, temp_input)

    if res.returncode == 0:
        return FileResponse(
            output_path,
            background=BackgroundTask(cleanup_files, output_path)
        )

    if temp_input: cleanup_files(temp_input)
    raise HTTPException(status_code=500, detail="Encoding Failed")

@app.post("/extract")
async def extract_route(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    temp_up = os.path.join(BASE_DIR, f"up_{int(time.time())}.png")
    with open(temp_up, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    res = subprocess.run([DECODER, "-d", temp_up], capture_output=True, text=True)
    background_tasks.add_task(cleanup_files, temp_up)

    if res.returncode == 0:
        return {"message": res.stdout.strip()}
    raise HTTPException(status_code=400, detail="Extraction Failed")
